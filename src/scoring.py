# scoring.py
from typing import Dict, List
from datetime import datetime
from src.services import estimate_nft_values, fetch_token_prices

def analyze_transfers(transfers: Dict[str, List[Dict]]) -> Dict:
    incoming = transfers["incoming"]
    outgoing = transfers["outgoing"]
    all_tx = incoming + outgoing

    if not all_tx:
        return {"age_days": 0, "tx_count": 0, "eth_in": 0.0, "eth_out": 0.0}

    timestamps = [t["metadata"]["blockTimestamp"] for t in all_tx if "metadata" in t and t["metadata"].get("blockTimestamp")]
    if not timestamps:
        return {"age_days": 0, "tx_count": len(all_tx), "eth_in": 0.0, "eth_out": 0.0}

    earliest = min(timestamps)
    age_days = (datetime.utcnow() - datetime.fromisoformat(earliest.rstrip("Z"))).days

    eth_in = sum(t.get("value", 0.0) for t in incoming if t.get("asset") == "ETH")
    eth_out = sum(t.get("value", 0.0) for t in outgoing if t.get("asset") == "ETH")

    return {
        "age_days": age_days,
        "tx_count": len(all_tx),
        "eth_in": eth_in,
        "eth_out": eth_out
    }

def calculate_token_value(tokens: List[Dict], prices: Dict[str, float]) -> float:
    total = 0.0
    for token in tokens:
        addr = token["contractAddress"].lower()
        balance = int(token["tokenBalance"], 16) / (10 ** 18)  # Assume 18 decimals; adjust if needed
        price = prices.get(addr, 0.0)
        total += balance * price
    return total

def calculate_nft_value(nfts: List[Dict]) -> float:
    values = estimate_nft_values(nfts)
    return sum(values.values())

def calculate_credit_score(aggregated: Dict) -> Dict:
    nfts = aggregated["nfts"]
    tokens = aggregated["tokens"]
    transfers = aggregated["transfers"]
    transfer_analysis = analyze_transfers(transfers)

    # Fetch prices
    token_contracts = [t["contractAddress"].lower() for t in tokens]
    token_prices = fetch_token_prices(token_contracts)

    # Values
    token_value = calculate_token_value(tokens, token_prices)
    nft_value = calculate_nft_value(nfts["legit_nfts"])
    total_assets = token_value + nft_value

    # Reputation
    poap_bonus = nfts["counts"]["poaps"] * 120
    ens_bonus = 80 if nfts["ens_domains"] else 0
    verified_count = sum(1 for nft in nfts["legit_nfts"] if nft["classification"]["safelist"] == "verified")
    verified_bonus = verified_count * 40

    # Activity
    age_bonus = transfer_analysis["age_days"] * 0.5  # Max ~1000 days = 500
    tx_bonus = min(transfer_analysis["tx_count"] * 2, 200)  # Cap at 100 tx
    eth_activity = min((transfer_analysis["eth_in"] + transfer_analysis["eth_out"]) * 10, 300)  # Activity proxy

    # Patterns: Penalize if spam NFTs > 20% or high out/low in (potential drainer)
    spam_ratio = nfts["counts"]["spam"] / max(nfts["counts"]["total"], 1)
    spam_penalty = -100 if spam_ratio > 0.2 else 0
    imbalance = transfer_analysis["eth_out"] / max(transfer_analysis["eth_in"], 0.001)
    imbalance_penalty = -150 if imbalance > 5 else 0  # Suspicious if out >> in

    # Total (0-1000)
    raw_score = (
        (total_assets * 0.3) +  # Asset weight
        poap_bonus + ens_bonus + verified_bonus +  # Reputation
        age_bonus + tx_bonus + eth_activity +  # Activity
        spam_penalty + imbalance_penalty + 100  # Base
    )
    score = min(max(raw_score, 0), 1000)

    return {
        "score": score,
        "breakdown": {
            "assets": total_assets * 0.3,
            "reputation": poap_bonus + ens_bonus + verified_bonus,
            "activity": age_bonus + tx_bonus + eth_activity,
            "penalties": spam_penalty + imbalance_penalty,
            "details": {
                "token_value": token_value,
                "nft_value": nft_value,
                "wallet_age_days": transfer_analysis["age_days"],
                "tx_count": transfer_analysis["tx_count"],
                "eth_in": transfer_analysis["eth_in"],
                "eth_out": transfer_analysis["eth_out"]
            }
        }
    }