# scoring.py (ENHANCED VERSION)
from typing import Dict, List
from datetime import datetime
from src.services import (
    estimate_nft_values, 
    fetch_token_prices,
    enrich_token_data,  # NEW
    calculate_portfolio_concentration,  # NEW
    check_defi_interactions,
    check_mixer_interactions,
    analyze_stablecoin_holdings,
    fetch_eth_balance,
    calculate_wallet_metadata  # NEW
)
from src.config import BLUE_CHIP_NFTS

def analyze_transfers(transfers: Dict[str, List[Dict]]) -> Dict:
    """ENHANCED: Better transfer analysis with activity patterns"""
    incoming = transfers["incoming"]
    outgoing = transfers["outgoing"]
    all_tx = incoming + outgoing
    
    if not all_tx:
        return {
            "age_days": 0, 
            "tx_count": 0, 
            "eth_in": 0.0, 
            "eth_out": 0.0,
            "active_months": 0,
            "avg_tx_per_month": 0
        }
    
    timestamps = [t["metadata"]["blockTimestamp"] for t in all_tx if "metadata" in t and t["metadata"].get("blockTimestamp")]
    if not timestamps:
        return {
            "age_days": 0, 
            "tx_count": len(all_tx), 
            "eth_in": 0.0, 
            "eth_out": 0.0,
            "active_months": 0,
            "avg_tx_per_month": 0
        }
    
    earliest = min(timestamps)
    latest = max(timestamps)
    age_days = (datetime.utcnow() - datetime.fromisoformat(earliest.rstrip("Z"))).days
    
    # Count active months
    unique_months = set()
    for ts in timestamps:
        dt = datetime.fromisoformat(ts.rstrip("Z"))
        unique_months.add((dt.year, dt.month))
    
    eth_in = sum(t.get("value", 0.0) for t in incoming if t.get("asset") == "ETH")
    eth_out = sum(t.get("value", 0.0) for t in outgoing if t.get("asset") == "ETH")
    
    # NEW: Calculate transaction frequency
    avg_tx_per_month = len(all_tx) / max(age_days / 30, 1)
    
    # NEW: Detect dormancy periods
    dormant_periods = 0
    if len(timestamps) > 1:
        sorted_timestamps = sorted([datetime.fromisoformat(ts.rstrip("Z")) for ts in timestamps])
        for i in range(1, len(sorted_timestamps)):
            gap_days = (sorted_timestamps[i] - sorted_timestamps[i-1]).days
            if gap_days > 90:  # 3 months of inactivity
                dormant_periods += 1
    
    return {
        "age_days": age_days,
        "tx_count": len(all_tx),
        "eth_in": eth_in,
        "eth_out": eth_out,
        "active_months": len(unique_months),
        "avg_tx_per_month": avg_tx_per_month,
        "dormant_periods": dormant_periods,
        "latest_activity": latest
    }

def calculate_token_value(tokens: List[Dict], prices: Dict[str, float] = None) -> float:
    """ENHANCED: Works with enriched token data"""
    # If tokens are already enriched, just sum the values
    if tokens and 'value_usd' in tokens[0]:
        return sum(t.get('value_usd', 0) for t in tokens)
    
    # Fallback to old method
    total = 0.0
    for token in tokens:
        addr = token["contractAddress"].lower()
        balance = int(token["tokenBalance"], 16) / (10 ** 18)
        price = prices.get(addr, 0.0) if prices else 0.0
        total += balance * price
    return total

def calculate_nft_value(nfts: List[Dict]) -> Dict:
    values = estimate_nft_values(nfts)
    total_value = sum(v for v in values.values() if v is not None)
    
    # Count blue chip NFTs
    blue_chip_count = 0
    for nft in nfts:
        contract_addr = nft.get("contract", {}).get("address", "").lower()
        if contract_addr in [addr.lower() for addr in BLUE_CHIP_NFTS]:
            blue_chip_count += 1
    
    return {
        "total_value": total_value,
        "blue_chip_count": blue_chip_count
    }

def analyze_nft_quality(nfts: Dict) -> Dict:
    verified_count = 0
    not_requested_count = 0
    other_count = 0
    
    for nft in nfts["legit_nfts"]:
        safelist = nft.get("classification", {}).get("safelist", "unknown")
        if safelist == "verified":
            verified_count += 1
        elif safelist == "not_requested":
            not_requested_count += 1
        else:
            other_count += 1
    
    return {
        "verified_count": verified_count,
        "not_requested_count": not_requested_count,
        "other_count": other_count,
        "verification_rate": verified_count / max(nfts["counts"]["legit"], 1)
    }

# NEW: Volatility Risk Score
def calculate_volatility_risk(enriched_tokens: List[Dict]) -> Dict:
    """Calculate portfolio risk based on token volatility"""
    if not enriched_tokens:
        return {
            'average_volatility': 0,
            'high_volatility_exposure': 0,
            'risk_score': 0
        }
    
    volatilities = [t.get('volatility_30d', 0) for t in enriched_tokens if t.get('volatility_30d') is not None]
    
    if not volatilities:
        return {
            'average_volatility': 0,
            'high_volatility_exposure': 0,
            'risk_score': 50  # Unknown risk
        }
    
    avg_volatility = sum(volatilities) / len(volatilities)
    
    # Calculate exposure to high-volatility assets (>50% volatility)
    total_value = sum(t.get('value_usd', 0) for t in enriched_tokens)
    high_vol_value = sum(
        t.get('value_usd', 0) for t in enriched_tokens 
        if t.get('volatility_30d', 0) and t.get('volatility_30d') > 50
    )
    
    high_vol_exposure = high_vol_value / total_value if total_value > 0 else 0
    
    # Risk score: lower is better (0-100)
    # Penalize high average volatility and high exposure
    risk_score = min(avg_volatility + (high_vol_exposure * 50), 100)
    
    return {
        'average_volatility': avg_volatility,
        'high_volatility_exposure': high_vol_exposure,
        'risk_score': risk_score
    }

# NEW: Stablecoin Stability Score
def calculate_stablecoin_score(stablecoin_data: Dict, total_portfolio: float) -> Dict:
    """Calculate financial stability based on stablecoin holdings"""
    stablecoin_usd = stablecoin_data.get('total_stablecoin_usd', 0)
    
    if total_portfolio == 0:
        return {
            'stablecoin_ratio': 0,
            'liquidity_score': 0
        }
    
    stablecoin_ratio = stablecoin_usd / total_portfolio
    
    # Higher ratio = more liquid/stable (up to a point)
    # Optimal range: 20-50% stablecoins
    if 0.2 <= stablecoin_ratio <= 0.5:
        liquidity_score = 100
    elif stablecoin_ratio > 0.5:
        # Too conservative
        liquidity_score = max(100 - ((stablecoin_ratio - 0.5) * 100), 50)
    else:
        # Not enough liquidity
        liquidity_score = stablecoin_ratio * 500  # 20% = 100 points
    
    return {
        'stablecoin_ratio': stablecoin_ratio,
        'stablecoin_usd': stablecoin_usd,
        'liquidity_score': min(liquidity_score, 100)
    }

def calculate_credit_score(aggregated: Dict) -> Dict:
    """ENHANCED: Credit scoring with volatility and concentration analysis"""
    nfts = aggregated["nfts"]
    raw_tokens = aggregated["tokens"]
    transfers = aggregated["transfers"]
    wallet = aggregated["wallet"]
    
    # ENHANCED: Enrich token data with prices, metadata, volatility
    enriched_tokens = enrich_token_data(raw_tokens)
    
    # ENHANCED: Calculate portfolio concentration
    concentration = calculate_portfolio_concentration(enriched_tokens)
    
    # Analyze data
    transfer_analysis = analyze_transfers(transfers)
    defi_activity = check_defi_interactions(transfers)
    mixer_check = check_mixer_interactions(transfers)
    nft_quality = analyze_nft_quality(nfts)
    stablecoin_data = analyze_stablecoin_holdings(enriched_tokens)
    
    # NEW: Volatility risk
    volatility_risk = calculate_volatility_risk(enriched_tokens)
    
    # Get ETH balance
    eth_balance = fetch_eth_balance(wallet)
    
    # Calculate values (using enriched data)
    token_value = calculate_token_value(enriched_tokens)
    nft_data = calculate_nft_value(nfts["legit_nfts"])
    
    # Assume ETH price (you can enhance this with real price fetch)
    eth_price = 2800  # Update this with real-time price
    total_assets = token_value + nft_data["total_value"] * eth_price + (eth_balance * eth_price)
    
    # NEW: Stablecoin stability score
    stablecoin_score = calculate_stablecoin_score(stablecoin_data, total_assets)
    
    # === SCORING (0-850 range like FICO) ===
    
    # 1. PAYMENT HISTORY (35%) - Max 298 points
    payment_score = 0
    
    # DeFi usage shows financial responsibility
    if defi_activity["aave"]:
        payment_score += 80
    if defi_activity["compound"]:
        payment_score += 70
    if defi_activity["ethena"]:  # NEW: Ethena staking
        payment_score += 60
    if defi_activity["morpho"]:  # NEW: Morpho lending
        payment_score += 50
    if defi_activity["total_protocols"] >= 3:
        payment_score += 50
    
    # Regular activity (ENHANCED)
    if transfer_analysis["active_months"] > 12:
        payment_score += 60
    elif transfer_analysis["active_months"] > 6:
        payment_score += 30
    
    # Consistent activity (NEW)
    if transfer_analysis["avg_tx_per_month"] > 5:
        payment_score += 40
    elif transfer_analysis["avg_tx_per_month"] > 2:
        payment_score += 20
    
    # No long dormant periods (NEW)
    if transfer_analysis.get("dormant_periods", 0) == 0:
        payment_score += 30
    
    # Balanced in/out ratio
    if transfer_analysis["eth_in"] > 0:
        ratio = transfer_analysis["eth_out"] / transfer_analysis["eth_in"]
        if ratio < 2:
            payment_score += 38
    
    payment_score = min(payment_score, 298)
    
    # 2. AMOUNTS OWED (30%) - Max 255 points
    amounts_score = 0
    
    # Stablecoin liquidity (ENHANCED)
    amounts_score += stablecoin_score['liquidity_score'] * 1.0
    
    # Total asset value
    asset_score = min(total_assets * 0.01, 100)
    amounts_score += asset_score
    
    # ETH balance
    if eth_balance > 10:
        amounts_score += 55
    elif eth_balance > 1:
        amounts_score += 35
    elif eth_balance > 0.1:
        amounts_score += 15
    
    amounts_score = min(amounts_score, 255)
    
    # 3. LENGTH OF HISTORY (15%) - Max 128 points
    history_score = 0
    
    wallet_age_years = transfer_analysis["age_days"] / 365
    history_score += min(wallet_age_years * 30, 80)
    
    # Transaction count
    tx_score = min(transfer_analysis["tx_count"] * 0.5, 48)
    history_score += tx_score
    
    history_score = min(history_score, 128)
    
    # 4. NEW CREDIT (10%) - Max 85 points
    new_credit_score = 0
    
    # Recent DeFi usage
    if defi_activity["total_protocols"] > 0:
        new_credit_score += min(defi_activity["total_protocols"] * 20, 60)
    
    # Not overextended
    if transfer_analysis["tx_count"] < 1000:
        new_credit_score += 25
    
    new_credit_score = min(new_credit_score, 85)
    
    # 5. CREDIT MIX (10%) - Max 85 points (ENHANCED)
    mix_score = 0
    
    # Asset diversification using Herfindahl index
    diversification_bonus = concentration['diversification_score'] * 0.4
    mix_score += diversification_bonus
    
    # Protocol diversity
    mix_score += min(defi_activity["total_protocols"] * 10, 45)
    
    mix_score = min(mix_score, 85)
    
    # === REPUTATION BONUSES ===
    reputation_bonus = 0
    
    # POAPs
    poap_bonus = min(nfts["counts"]["poaps"] * 3, 40)
    reputation_bonus += poap_bonus
    
    # ENS ownership
    if nfts["counts"]["ens"] > 0:
        reputation_bonus += 25
    
    # Verified NFTs
    verified_bonus = min(nft_quality["verified_count"] * 5, 60)
    reputation_bonus += verified_bonus
    
    # Blue chip NFTs
    blue_chip_bonus = min(nft_data["blue_chip_count"] * 15, 50)
    reputation_bonus += blue_chip_bonus
    
    # NEW: Staking activity (shows long-term commitment)
    if defi_activity.get("staking_events", 0) > 0:
        reputation_bonus += min(defi_activity["staking_events"] * 5, 30)
    
    reputation_bonus = min(reputation_bonus, 200)
    
    # === RISK PENALTIES ===
    risk_penalty = 0
    
    # Mixer interaction (MAJOR red flag)
    if mixer_check["has_mixer_interaction"]:
        risk_penalty += 200
    
    # NEW: High concentration risk
    if concentration['top_1_concentration'] > 0.8:
        risk_penalty += 100
    elif concentration['top_1_concentration'] > 0.5:
        risk_penalty += 50
    
    # NEW: High volatility risk
    if volatility_risk['risk_score'] > 70:
        risk_penalty += 80
    elif volatility_risk['risk_score'] > 50:
        risk_penalty += 40
    
    # Spam NFT ratio
    spam_ratio = nfts["counts"]["spam"] / max(nfts["counts"]["total"], 1)
    if spam_ratio > 0.5:
        risk_penalty += 80
    elif spam_ratio > 0.2:
        risk_penalty += 40
    
    # Drainer pattern
    if transfer_analysis["eth_in"] > 0:
        imbalance = transfer_analysis["eth_out"] / transfer_analysis["eth_in"]
        if imbalance > 10:
            risk_penalty += 150
        elif imbalance > 5:
            risk_penalty += 70
    
    # Low verification rate for NFTs
    if nft_quality["verification_rate"] < 0.3 and nfts["counts"]["legit"] > 5:
        risk_penalty += 30
    
    # === CALCULATE FINAL SCORE ===
    base_score = (
        payment_score +
        amounts_score +
        history_score +
        new_credit_score +
        mix_score
    )
    
    final_score = base_score + reputation_bonus - risk_penalty
    
    # Clamp to 0-850
    final_score = max(0, min(final_score, 850))
    
    # Determine grade
    if final_score >= 800:
        grade = "A+"
        rating = "Excellent"
    elif final_score >= 740:
        grade = "A"
        rating = "Very Good"
    elif final_score >= 670:
        grade = "B+"
        rating = "Good"
    elif final_score >= 580:
        grade = "B"
        rating = "Fair"
    elif final_score >= 500:
        grade = "C"
        rating = "Poor"
    elif final_score >= 400:
        grade = "D"
        rating = "Very Poor"
    else:
        grade = "F"
        rating = "Bad"
    
    return {
        "score": int(final_score),
        "grade": grade,
        "rating": rating,
        "max_score": 850,
        "breakdown": {
            "payment_history": int(payment_score),
            "amounts_owed": int(amounts_score),
            "length_of_history": int(history_score),
            "new_credit": int(new_credit_score),
            "credit_mix": int(mix_score),
            "reputation_bonus": int(reputation_bonus),
            "risk_penalty": int(-risk_penalty)
        },
        "details": {
            "total_assets_usd": round(total_assets, 2),
            "eth_balance": round(eth_balance, 4),
            "token_value_usd": round(token_value, 2),
            "nft_value_eth": round(nft_data["total_value"], 4),
            "stablecoin_balance_usd": round(stablecoin_data["total_stablecoin_usd"], 2),
            "wallet_age_days": transfer_analysis["age_days"],
            "tx_count": transfer_analysis["tx_count"],
            "active_months": transfer_analysis["active_months"],
            "avg_tx_per_month": round(transfer_analysis.get("avg_tx_per_month", 0), 2),
            "defi_protocols_used": defi_activity["total_protocols"],
            "staking_events": defi_activity.get("staking_events", 0),
            "has_mixer_interaction": mixer_check["has_mixer_interaction"],
            "verified_nfts": nft_quality["verified_count"],
            "blue_chip_nfts": nft_data["blue_chip_count"],
            "poap_count": nfts["counts"]["poaps"],
            "ens_count": nfts["counts"]["ens"]
        },
        "portfolio_analysis": {
            "diversification_score": round(concentration['diversification_score'], 2),
            "top_1_concentration": round(concentration['top_1_concentration'] * 100, 2),
            "top_3_concentration": round(concentration['top_3_concentration'] * 100, 2),
            "herfindahl_index": round(concentration['herfindahl_index'], 4),
            "num_tokens": concentration['num_tokens'],
            "average_volatility": round(volatility_risk['average_volatility'], 2),
            "high_volatility_exposure": round(volatility_risk['high_volatility_exposure'] * 100, 2),
            "volatility_risk_score": round(volatility_risk['risk_score'], 2),
            "stablecoin_ratio": round(stablecoin_score['stablecoin_ratio'] * 100, 2),
            "liquidity_score": round(stablecoin_score['liquidity_score'], 2)
        },
        "risk_flags": {
            "mixer_transactions": mixer_check["has_mixer_interaction"],
            "high_spam_ratio": spam_ratio > 0.2,
            "drainer_pattern": transfer_analysis["eth_out"] / max(transfer_analysis["eth_in"], 0.001) > 5,
            "low_nft_verification": nft_quality["verification_rate"] < 0.3,
            "high_concentration": concentration['top_1_concentration'] > 0.5,
            "high_volatility": volatility_risk['risk_score'] > 50,
            "dormant_periods": transfer_analysis.get("dormant_periods", 0) > 2
        }
    }