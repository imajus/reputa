from fastapi import APIRouter, HTTPException
from src.models import WalletRequest, AssetTransferParams
from src.services import (
    complete_credit_assessment,
    fetch_all_nfts,
    fetch_token_balances,
    fetch_asset_transfers,
    enrich_token_data,
    calculate_portfolio_concentration,
    check_defi_interactions,
    check_mixer_interactions,
    analyze_stablecoin_holdings,
    calculate_wallet_metadata,
    fetch_eth_balance
)

from src.classifiers import classify_nfts
from src.scoring import calculate_credit_score, fetch_protocol_lending_history

api_router = APIRouter()

@api_router.post("/assets/nfts")
async def get_nfts(request: WalletRequest):
    try:
        raw_nfts = fetch_all_nfts(request.wallet_address)
        classified = classify_nfts(raw_nfts)
        return classified
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/assets/tokens")
async def get_tokens(request: WalletRequest):
    try:
        raw_tokens = fetch_token_balances(request.wallet_address)
        enriched = enrich_token_data(raw_tokens)
        concentration = calculate_portfolio_concentration(enriched)
        
        return {
            "tokens": enriched,
            "concentration_metrics": concentration
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/history/transfers")
async def get_transfers(request: WalletRequest, params: AssetTransferParams = AssetTransferParams()):
    try:
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        return {"incoming": incoming, "outgoing": outgoing}
    except Exception as e:
        raise HTTPException(500, str(e))
    
@api_router.post("/lending/protocol-history")
async def get_protocol_lending_history(request: WalletRequest):
    try:
        return fetch_protocol_lending_history(request.wallet_address)
    except Exception as e:
        raise HTTPException(500, str(e))

# New endpoint for final credit score calculation
@api_router.post("/aggregate")
async def aggregate_all_data(request: WalletRequest):
    try:
        # Aggregate data first
        nfts = fetch_all_nfts(request.wallet_address)
        classified_nfts = classify_nfts(nfts)
        
        raw_tokens = fetch_token_balances(request.wallet_address)
        enriched_tokens = enrich_token_data(raw_tokens)
        concentration = calculate_portfolio_concentration(enriched_tokens)
        
        params = AssetTransferParams()
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        
        transfers = {"incoming": incoming, "outgoing": outgoing}
        
        eth_balance = fetch_eth_balance(request.wallet_address)
        
        defi_interactions = check_defi_interactions(transfers)
        mixer_check = check_mixer_interactions(transfers)
        stablecoin_data = analyze_stablecoin_holdings(enriched_tokens)
        wallet_metadata = calculate_wallet_metadata(transfers, request.wallet_address)
        
        lending_history = fetch_protocol_lending_history(request.wallet_address)
        
        aggregated = {
            "wallet": request.wallet_address,
            "nfts": classified_nfts,
            "tokens": {
                "holdings": enriched_tokens,
                "concentration": concentration
            },
            "transfers": transfers,
            "eth_balance": eth_balance,
            "defi_analysis": {
                "protocol_interactions": defi_interactions,
                "mixer_check": mixer_check,
                "stablecoins": stablecoin_data
            },
            "wallet_metadata": wallet_metadata,
            "lending_history": lending_history
        }
        
        return aggregated
    
    except Exception as e:
        raise HTTPException(500, str(e))
    

@api_router.post("/credit-score")
async def calculate_score(request: WalletRequest):
    try: 
        aggregated = await aggregate_all_data(request)
        
        # credit_score = calculate_credit_score(aggregated)
        credit_score = complete_credit_assessment(aggregated)
        return credit_score
    
    except Exception as e:
        raise HTTPException(500, str(e))