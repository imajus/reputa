# routers.py (ENHANCED VERSION)
from fastapi import APIRouter, HTTPException
from src.models import WalletRequest, AssetTransferParams
from src.services import (
    fetch_all_nfts, 
    fetch_token_balances, 
    fetch_asset_transfers,
    enrich_token_data,  # NEW
    calculate_portfolio_concentration,  # NEW
    calculate_wallet_metadata,  # NEW
    check_defi_interactions,
    check_mixer_interactions
)
from src.classifiers import classify_nfts
from src.scoring import calculate_credit_score

api_router = APIRouter()

@api_router.post("/assets/nfts")
async def get_nfts(request: WalletRequest):
    """Get and classify NFTs"""
    try:
        raw_nfts = fetch_all_nfts(request.wallet_address)
        classified = classify_nfts(raw_nfts)
        return classified
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/assets/tokens")
async def get_tokens(request: WalletRequest):
    """Get token balances (basic)"""
    try:
        tokens = fetch_token_balances(request.wallet_address)
        return {"tokens": tokens}
    except Exception as e:
        raise HTTPException(500, str(e))

# NEW: Enhanced token endpoint with prices and volatility
@api_router.post("/assets/tokens/enriched")
async def get_tokens_enriched(request: WalletRequest):
    """Get enriched token data with prices, metadata, and volatility"""
    try:
        raw_tokens = fetch_token_balances(request.wallet_address)
        enriched_tokens = enrich_token_data(raw_tokens)
        concentration = calculate_portfolio_concentration(enriched_tokens)
        
        return {
            "tokens": enriched_tokens,
            "portfolio_metrics": concentration,
            "summary": {
                "total_value_usd": concentration['total_value_usd'],
                "num_tokens": concentration['num_tokens'],
                "diversification_score": concentration['diversification_score'],
                "top_holding": enriched_tokens[0]['symbol'] if enriched_tokens else None,
                "top_holding_percentage": concentration['top_1_concentration'] * 100 if enriched_tokens else 0
            }
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/history/transfers")
async def get_transfers(request: WalletRequest, params: AssetTransferParams = AssetTransferParams()):
    """Get transfer history"""
    try:
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        return {"incoming": incoming, "outgoing": outgoing}
    except Exception as e:
        raise HTTPException(500, str(e))

# NEW: Wallet metadata endpoint
@api_router.post("/wallet/metadata")
async def get_wallet_metadata(request: WalletRequest):
    """Get comprehensive wallet metadata and activity metrics"""
    try:
        params = AssetTransferParams()
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        
        transfers = {"incoming": incoming, "outgoing": outgoing}
        metadata = calculate_wallet_metadata(transfers, request.wallet_address)
        
        return {
            "wallet_address": request.wallet_address,
            "metadata": metadata,
            "activity_summary": {
                "is_active": metadata.get('wallet_age_days', 0) > 0,
                "maturity_level": (
                    "Very Mature" if metadata.get('wallet_age_days', 0) > 730 else
                    "Mature" if metadata.get('wallet_age_days', 0) > 365 else
                    "Established" if metadata.get('wallet_age_days', 0) > 180 else
                    "New" if metadata.get('wallet_age_days', 0) > 30 else
                    "Very New"
                ),
                "activity_level": (
                    "Very Active" if metadata.get('average_txs_per_month', 0) > 10 else
                    "Active" if metadata.get('average_txs_per_month', 0) > 5 else
                    "Moderate" if metadata.get('average_txs_per_month', 0) > 1 else
                    "Low"
                )
            }
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/aggregate")
async def aggregate_data(request: WalletRequest):
    """Aggregate all wallet data (basic)"""
    try:
        nfts = fetch_all_nfts(request.wallet_address)
        classified_nfts = classify_nfts(nfts)
        tokens = fetch_token_balances(request.wallet_address)
        params = AssetTransferParams()
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)

        aggregated = {
            "wallet": request.wallet_address,
            "nfts": classified_nfts,
            "tokens": tokens,
            "transfers": {"incoming": incoming, "outgoing": outgoing}
        }
        return aggregated
    except Exception as e:
        raise HTTPException(500, str(e))

# NEW: Enriched aggregation endpoint
@api_router.post("/aggregate/enriched")
async def aggregate_data_enriched(request: WalletRequest):
    """Aggregate all wallet data with enrichment (prices, volatility, metadata)"""
    try:
        # Fetch all data
        nfts = fetch_all_nfts(request.wallet_address)
        classified_nfts = classify_nfts(nfts)
        
        raw_tokens = fetch_token_balances(request.wallet_address)
        enriched_tokens = enrich_token_data(raw_tokens)
        
        params = AssetTransferParams()
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        
        transfers = {"incoming": incoming, "outgoing": outgoing}
        
        # Calculate metadata
        wallet_metadata = calculate_wallet_metadata(transfers, request.wallet_address)
        portfolio_metrics = calculate_portfolio_concentration(enriched_tokens)

        aggregated = {
            "wallet": request.wallet_address,
            "metadata": wallet_metadata,
            "nfts": classified_nfts,
            "tokens": {
                "enriched": enriched_tokens,
                "raw": raw_tokens  # Include raw for compatibility
            },
            "portfolio": portfolio_metrics,
            "transfers": transfers,
            "enrichment_timestamp": wallet_metadata.get('last_transaction_date')
        }
        return aggregated
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/score")
async def get_credit_score(request: WalletRequest):
    """Calculate credit score (uses enriched data automatically)"""
    try:
        aggregated = await aggregate_data(request)
        score = calculate_credit_score(aggregated)
        return score
    except Exception as e:
        raise HTTPException(500, str(e))

# NEW: Enhanced credit score endpoint with detailed breakdown
@api_router.post("/score/detailed")
async def get_detailed_credit_score(request: WalletRequest):
    """Get credit score with full portfolio analysis and risk assessment"""
    try:
        # Use enriched aggregation
        aggregated = await aggregate_data_enriched(request)
        
        # Convert enriched format to standard format for scoring
        aggregated_for_scoring = {
            "wallet": aggregated["wallet"],
            "nfts": aggregated["nfts"],
            "tokens": aggregated["tokens"]["enriched"],  # Use enriched tokens
            "transfers": aggregated["transfers"]
        }
        
        score = calculate_credit_score(aggregated_for_scoring)
        
        # Add enrichment data to response
        score["enrichment_data"] = {
            "wallet_metadata": aggregated["metadata"],
            "portfolio_metrics": aggregated["portfolio"],
            "data_quality": "enriched",
            "timestamp": aggregated.get("enrichment_timestamp")
        }
        
        return score
    except Exception as e:
        raise HTTPException(500, str(e))

# NEW: Portfolio analysis endpoint
@api_router.post("/portfolio/analysis")
async def analyze_portfolio(request: WalletRequest):
    """Deep portfolio analysis with concentration and volatility metrics"""
    try:
        raw_tokens = fetch_token_balances(request.wallet_address)
        enriched_tokens = enrich_token_data(raw_tokens)
        concentration = calculate_portfolio_concentration(enriched_tokens)
        
        # Calculate category breakdown
        by_category = {}
        for token in enriched_tokens:
            category = token.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = {
                    'count': 0,
                    'total_value_usd': 0,
                    'tokens': []
                }
            by_category[category]['count'] += 1
            by_category[category]['total_value_usd'] += token.get('value_usd', 0)
            by_category[category]['tokens'].append({
                'symbol': token.get('symbol'),
                'value_usd': token.get('value_usd', 0),
                'balance': token.get('balance_human', 0)
            })
        
        # Calculate volatility stats
        volatilities = [t.get('volatility_30d', 0) for t in enriched_tokens if t.get('volatility_30d') is not None]
        avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
        
        return {
            "portfolio_value_usd": concentration['total_value_usd'],
            "num_tokens": concentration['num_tokens'],
            "concentration": {
                "diversification_score": concentration['diversification_score'],
                "herfindahl_index": concentration['herfindahl_index'],
                "top_1_percentage": concentration['top_1_concentration'] * 100,
                "top_3_percentage": concentration['top_3_concentration'] * 100,
                "top_5_percentage": concentration['top_5_concentration'] * 100
            },
            "risk_metrics": {
                "average_volatility_30d": avg_volatility,
                "num_tokens_with_volatility_data": len(volatilities),
                "concentration_risk": "High" if concentration['top_1_concentration'] > 0.5 else 
                                     "Medium" if concentration['top_1_concentration'] > 0.3 else "Low"
            },
            "by_category": by_category,
            "top_holdings": sorted(enriched_tokens, key=lambda x: x.get('value_usd', 0), reverse=True)[:5]
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# NEW: Risk assessment endpoint
@api_router.post("/risk/assessment")
async def assess_risk(request: WalletRequest):
    """Comprehensive risk assessment of wallet"""
    try:
        
        params = AssetTransferParams()
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        transfers = {"incoming": incoming, "outgoing": outgoing}
        
        defi = check_defi_interactions(transfers)
        mixer = check_mixer_interactions(transfers)
        
        raw_tokens = fetch_token_balances(request.wallet_address)
        enriched_tokens = enrich_token_data(raw_tokens)
        concentration = calculate_portfolio_concentration(enriched_tokens)
        
        # Calculate risk score (0-100, lower is better)
        risk_score = 0
        risk_factors = []
        
        # Mixer usage - CRITICAL
        if mixer["has_mixer_interaction"]:
            risk_score += 40
            risk_factors.append({
                "factor": "Mixer Interaction",
                "severity": "CRITICAL",
                "impact": 40,
                "description": "Wallet has interacted with known mixer addresses"
            })
        
        # High concentration
        if concentration['top_1_concentration'] > 0.8:
            risk_score += 25
            risk_factors.append({
                "factor": "Extreme Concentration",
                "severity": "HIGH",
                "impact": 25,
                "description": f"Top holding represents {concentration['top_1_concentration']*100:.1f}% of portfolio"
            })
        elif concentration['top_1_concentration'] > 0.5:
            risk_score += 15
            risk_factors.append({
                "factor": "High Concentration",
                "severity": "MEDIUM",
                "impact": 15,
                "description": f"Top holding represents {concentration['top_1_concentration']*100:.1f}% of portfolio"
            })
        
        # Volatility
        volatilities = [t.get('volatility_30d', 0) for t in enriched_tokens if t.get('volatility_30d')]
        if volatilities:
            avg_vol = sum(volatilities) / len(volatilities)
            if avg_vol > 70:
                risk_score += 20
                risk_factors.append({
                    "factor": "High Volatility",
                    "severity": "HIGH",
                    "impact": 20,
                    "description": f"Average portfolio volatility: {avg_vol:.1f}%"
                })
            elif avg_vol > 40:
                risk_score += 10
                risk_factors.append({
                    "factor": "Moderate Volatility",
                    "severity": "MEDIUM",
                    "impact": 10,
                    "description": f"Average portfolio volatility: {avg_vol:.1f}%"
                })
        
        # Low DeFi usage
        if defi['total_protocols'] == 0:
            risk_score += 5
            risk_factors.append({
                "factor": "No DeFi History",
                "severity": "LOW",
                "impact": 5,
                "description": "No interactions with major DeFi protocols detected"
            })
        
        risk_level = (
            "CRITICAL" if risk_score >= 60 else
            "HIGH" if risk_score >= 40 else
            "MEDIUM" if risk_score >= 20 else
            "LOW"
        )
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": [
                "Diversify holdings to reduce concentration risk" if concentration['top_1_concentration'] > 0.5 else None,
                "Avoid mixer interactions to maintain clean transaction history" if mixer["has_mixer_interaction"] else None,
                "Consider stablecoin allocation to reduce volatility" if volatilities and sum(volatilities)/len(volatilities) > 50 else None,
                "Engage with reputable DeFi protocols to build credit history" if defi['total_protocols'] == 0 else None
            ],
            "positive_factors": [
                "Active DeFi user" if defi['total_protocols'] >= 3 else None,
                "Well-diversified portfolio" if concentration['diversification_score'] > 70 else None,
                "Clean transaction history" if not mixer["has_mixer_interaction"] else None
            ]
        }
    except Exception as e:
        raise HTTPException(500, str(e))