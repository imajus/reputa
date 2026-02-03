# scoring.py
from typing import Dict, List
from datetime import datetime
from src.services import (
    estimate_nft_values, 
    fetch_token_prices, 
    check_defi_interactions,
    check_mixer_interactions,
    analyze_stablecoin_holdings,
    fetch_eth_balance
)
from src.config import BLUE_CHIP_NFTS

def analyze_transfers(transfers: Dict[str, List[Dict]]) -> Dict:
    incoming = transfers["incoming"]
    outgoing = transfers["outgoing"]
    all_tx = incoming + outgoing
    
    if not all_tx:
        return {
            "age_days": 0, 
            "tx_count": 0, 
            "eth_in": 0.0, 
            "eth_out": 0.0,
            "active_months": 0
        }
    
    timestamps = [t["metadata"]["blockTimestamp"] for t in all_tx if "metadata" in t and t["metadata"].get("blockTimestamp")]
    if not timestamps:
        return {
            "age_days": 0, 
            "tx_count": len(all_tx), 
            "eth_in": 0.0, 
            "eth_out": 0.0,
            "active_months": 0
        }
    
    earliest = min(timestamps)
    age_days = (datetime.utcnow() - datetime.fromisoformat(earliest.rstrip("Z"))).days
    
    # Count active months
    unique_months = set()
    for ts in timestamps:
        dt = datetime.fromisoformat(ts.rstrip("Z"))
        unique_months.add((dt.year, dt.month))
    
    eth_in = sum(t.get("value", 0.0) for t in incoming if t.get("asset") == "ETH")
    eth_out = sum(t.get("value", 0.0) for t in outgoing if t.get("asset") == "ETH")
    
    return {
        "age_days": age_days,
        "tx_count": len(all_tx),
        "eth_in": eth_in,
        "eth_out": eth_out,
        "active_months": len(unique_months)
    }

def calculate_token_value(tokens: List[Dict], prices: Dict[str, float]) -> float:
    total = 0.0
    for token in tokens:
        addr = token["contractAddress"].lower()
        balance = int(token["tokenBalance"], 16) / (10 ** 18)
        price = prices.get(addr, 0.0)
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

def calculate_credit_score(aggregated: Dict) -> Dict:
    nfts = aggregated["nfts"]
    tokens = aggregated["tokens"]
    transfers = aggregated["transfers"]
    wallet = aggregated["wallet"]
    
    # Analyze data
    transfer_analysis = analyze_transfers(transfers)
    defi_activity = check_defi_interactions(transfers)
    mixer_check = check_mixer_interactions(transfers)
    nft_quality = analyze_nft_quality(nfts)
    stablecoin_data = analyze_stablecoin_holdings(tokens)
    
    # Get ETH balance
    eth_balance = fetch_eth_balance(wallet)
    
    # Fetch token prices
    token_contracts = [t["contractAddress"].lower() for t in tokens]
    token_prices = fetch_token_prices(token_contracts)
    
    # Calculate values
    token_value = calculate_token_value(tokens, token_prices)
    nft_data = calculate_nft_value(nfts["legit_nfts"])
    total_assets = token_value + nft_data["total_value"] + (eth_balance * 2000)  # Assume ETH ~ $2000
    
    # === SCORING (0-850 range like FICO) ===
    
    # 1. PAYMENT HISTORY (35%) - Max 298 points
    payment_score = 0
    
    # DeFi usage shows financial responsibility
    if defi_activity["aave"]:
        payment_score += 80
    if defi_activity["compound"]:
        payment_score += 70
    if defi_activity["total_protocols"] >= 3:
        payment_score += 50
    
    # Regular activity
    if transfer_analysis["active_months"] > 12:
        payment_score += 60
    elif transfer_analysis["active_months"] > 6:
        payment_score += 30
    
    # Balanced in/out ratio (not a drainer)
    if transfer_analysis["eth_in"] > 0:
        ratio = transfer_analysis["eth_out"] / transfer_analysis["eth_in"]
        if ratio < 2:
            payment_score += 38
    
    # 2. AMOUNTS OWED (30%) - Max 255 points
    # We don't have debt data, so we use assets as proxy
    amounts_score = 0
    
    # Stablecoin holdings (liquidity)
    if stablecoin_data["total_stablecoin_usd"] > 10000:
        amounts_score += 100
    elif stablecoin_data["total_stablecoin_usd"] > 1000:
        amounts_score += 60
    elif stablecoin_data["total_stablecoin_usd"] > 100:
        amounts_score += 30
    
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
    
    # 3. LENGTH OF HISTORY (15%) - Max 128 points
    history_score = 0
    
    wallet_age_years = transfer_analysis["age_days"] / 365
    history_score += min(wallet_age_years * 30, 80)
    
    # Transaction count
    tx_score = min(transfer_analysis["tx_count"] * 0.5, 48)
    history_score += tx_score
    
    # 4. NEW CREDIT (10%) - Max 85 points
    new_credit_score = 0
    
    # Recent DeFi usage (we approximate)
    if defi_activity["total_protocols"] > 0:
        new_credit_score += min(defi_activity["total_protocols"] * 20, 60)
    
    # Not overextended
    if transfer_analysis["tx_count"] < 1000:
        new_credit_score += 25
    
    # 5. CREDIT MIX (10%) - Max 85 points
    mix_score = 0
    
    # Asset diversification
    asset_types = 0
    if len(tokens) > 0:
        asset_types += 1
    if nfts["counts"]["legit"] > 0:
        asset_types += 1
    if stablecoin_data["has_stablecoins"]:
        asset_types += 1
    if eth_balance > 0:
        asset_types += 1
    
    mix_score += asset_types * 15
    
    # Protocol diversity
    mix_score += min(defi_activity["total_protocols"] * 10, 25)
    
    # === REPUTATION BONUSES ===
    reputation_bonus = 0
    
    # POAPs (event attendance)
    poap_bonus = min(nfts["counts"]["poaps"] * 3, 40)
    reputation_bonus += poap_bonus
    
    # ENS ownership (identity)
    if nfts["counts"]["ens"] > 0:
        reputation_bonus += 25
    
    # Verified NFTs
    verified_bonus = min(nft_quality["verified_count"] * 5, 60)
    reputation_bonus += verified_bonus
    
    # Blue chip NFTs
    blue_chip_bonus = min(nft_data["blue_chip_count"] * 15, 50)
    reputation_bonus += blue_chip_bonus
    
    # === RISK PENALTIES ===
    risk_penalty = 0
    
    # Mixer interaction (MAJOR red flag)
    if mixer_check["has_mixer_interaction"]:
        risk_penalty += 200
    
    # Spam NFT ratio
    spam_ratio = nfts["counts"]["spam"] / max(nfts["counts"]["total"], 1)
    if spam_ratio > 0.5:
        risk_penalty += 80
    elif spam_ratio > 0.2:
        risk_penalty += 40
    
    # Drainer pattern (out >> in)
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
    elif final_score >= 740:
        grade = "A"
    elif final_score >= 670:
        grade = "B+"
    elif final_score >= 580:
        grade = "B"
    elif final_score >= 500:
        grade = "C"
    elif final_score >= 400:
        grade = "D"
    else:
        grade = "F"
    
    return {
        "score": int(final_score),
        "grade": grade,
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
            "defi_protocols_used": defi_activity["total_protocols"],
            "has_mixer_interaction": mixer_check["has_mixer_interaction"],
            "verified_nfts": nft_quality["verified_count"],
            "blue_chip_nfts": nft_data["blue_chip_count"],
            "poap_count": nfts["counts"]["poaps"],
            "ens_count": nfts["counts"]["ens"]
        },
        "risk_flags": {
            "mixer_transactions": mixer_check["has_mixer_interaction"],
            "high_spam_ratio": spam_ratio > 0.2,
            "drainer_pattern": transfer_analysis["eth_out"] / max(transfer_analysis["eth_in"], 0.001) > 5,
            "low_nft_verification": nft_quality["verification_rate"] < 0.3
        }
    }