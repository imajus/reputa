from datetime import datetime
from typing import Dict, List
from src.services.lending_service import analyze_protocol_interactions, fetch_wallet_events_etherscan
from src.services.token_service import estimate_nft_values

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
    
    unique_months = set()
    for ts in timestamps:
        dt = datetime.fromisoformat(ts.rstrip("Z"))
        unique_months.add((dt.year, dt.month))
    
    eth_in = sum(t.get("value", 0.0) for t in incoming if t.get("asset") == "ETH")
    eth_out = sum(t.get("value", 0.0) for t in outgoing if t.get("asset") == "ETH")
    
    avg_tx_per_month = len(all_tx) / max(age_days / 30, 1)
    
    dormant_periods = 0
    if len(timestamps) > 1:
        sorted_timestamps = sorted([datetime.fromisoformat(ts.rstrip("Z")) for ts in timestamps])
        for i in range(1, len(sorted_timestamps)):
            gap_days = (sorted_timestamps[i] - sorted_timestamps[i-1]).days
            if gap_days > 90:
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
    if tokens and 'value_usd' in tokens[0]:
        return sum(t.get('value_usd', 0) for t in tokens)
    
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

def calculate_volatility_risk(enriched_tokens: List[Dict]) -> Dict:
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
            'risk_score': 50
        }
    
    avg_volatility = sum(volatilities) / len(volatilities)
    
    total_value = sum(t.get('value_usd', 0) for t in enriched_tokens)
    high_vol_value = sum(
        t.get('value_usd', 0) for t in enriched_tokens 
        if t.get('volatility_30d', 0) and t.get('volatility_30d') > 50
    )
    
    high_vol_exposure = high_vol_value / total_value if total_value > 0 else 0
    
    risk_score = min(avg_volatility + (high_vol_exposure * 50), 100)
    
    return {
        'average_volatility': avg_volatility,
        'high_volatility_exposure': high_vol_exposure,
        'risk_score': risk_score
    }

def calculate_stablecoin_score(stablecoin_data: Dict, total_portfolio: float) -> Dict:
    stablecoin_usd = stablecoin_data.get('total_stablecoin_usd', 0)
    
    if total_portfolio == 0:
        return {
            'stablecoin_ratio': 0,
            'liquidity_score': 0
        }
    
    stablecoin_ratio = stablecoin_usd / total_portfolio
    
    if 0.2 <= stablecoin_ratio <= 0.5:
        liquidity_score = 100
    elif stablecoin_ratio > 0.5:
        liquidity_score = max(100 - ((stablecoin_ratio - 0.5) * 100), 50)
    else:
        liquidity_score = stablecoin_ratio * 500
    
    return {
        'stablecoin_ratio': stablecoin_ratio,
        'stablecoin_usd': stablecoin_usd,
        'liquidity_score': min(liquidity_score, 100)
    }

def calculate_credit_assessment(protocol_analysis: Dict) -> Dict:
    summary = protocol_analysis.get("summary", {})
    risk_indicators = protocol_analysis.get("risk_indicators", {})
    
    total_borrows = summary.get("total_borrow_events", 0)
    total_repays = summary.get("total_repay_events", 0)
    total_liquidations = summary.get("total_liquidation_events", 0)
    
    credit_score = 50
    
    if total_borrows == 0:
        credit_score = 50
    else:
        repayment_ratio = total_repays / total_borrows
        
        if repayment_ratio >= 1.0:
            credit_score = 100
        elif repayment_ratio >= 0.9:
            credit_score = 95
        elif repayment_ratio >= 0.8:
            credit_score = 85
        elif repayment_ratio >= 0.7:
            credit_score = 75
        elif repayment_ratio >= 0.6:
            credit_score = 65
        elif repayment_ratio >= 0.5:
            credit_score = 55
        elif repayment_ratio >= 0.4:
            credit_score = 45
        else:
            credit_score = 30
        
        if total_liquidations > 0:
            credit_score -= (total_liquidations * 20)
    
    credit_score = max(0, min(100, credit_score))
    
    lending_protocols_used = {}
    for contract, data in protocol_analysis.get("protocols", {}).items():
        protocol_name = data.get("protocol_name", "Unknown")
        borrows = data.get("borrow_count", 0)
        repays = data.get("repay_count", 0)
        liquidations = data.get("liquidate_count", 0)
        
        if borrows > 0 or repays > 0 or liquidations > 0:
            lending_protocols_used[protocol_name] = {
                "borrows": borrows,
                "repays": repays,
                "liquidations": liquidations,
                "repayment_ratio": repays / max(borrows, 1)
            }
    
    if credit_score >= 90:
        creditworthiness = "EXCELLENT"
    elif credit_score >= 75:
        creditworthiness = "GOOD"
    elif credit_score >= 60:
        creditworthiness = "FAIR"
    elif credit_score >= 40:
        creditworthiness = "POOR"
    else:
        creditworthiness = "VERY POOR"
    
    return {
        "credit_score": credit_score,
        "total_borrowing_events": total_borrows,
        "total_repayment_events": total_repays,
        "total_liquidations": total_liquidations,
        "repayment_ratio": risk_indicators.get("repayment_ratio", 0),
        "lending_protocols_used": lending_protocols_used,
        "has_default_history": total_liquidations > 0,
        "creditworthiness": creditworthiness,
        "has_borrowing_activity": total_borrows > 0
    }

def fetch_protocol_lending_history(transactions: List[Dict]) -> Dict:
    try:
        if not transactions:
            return {
                "protocol_analysis": {
                    "protocols": {},
                    "summary": {
                        "total_protocols_interacted": 0,
                        "total_borrow_events": 0,
                        "total_repay_events": 0,
                        "total_liquidation_events": 0,
                        "total_supply_events": 0,
                        "total_withdrawal_events": 0,
                        "has_borrowing_activity": False,
                        "has_repayment_activity": False,
                        "has_liquidation_events": False
                    },
                    "risk_indicators": {
                        "liquidation_risk": "UNKNOWN",
                        "debt_management": "INACTIVE",
                        "borrowing_activity": "NONE",
                        "repayment_ratio": 0
                    }
                }
            }
        
        protocol_analysis = analyze_protocol_interactions(transactions)
        
        return {
            "protocol_analysis": protocol_analysis,
            "events_count": len(transactions)
        }
        
    except Exception as e:
        print(f"Error in fetch_protocol_lending_history: {e}")
        return {
            "error": str(e),
            "protocol_analysis": {
                "protocols": {},
                "summary": {},
                "risk_indicators": {}
            }
        }
    
def calculate_credit_score(aggregated: Dict) -> Dict:
    nfts = aggregated["nfts"]
    raw_tokens = aggregated["tokens"]["holdings"]
    transfers = aggregated["transfers"]
    wallet = aggregated["wallet"]
    lending_history = aggregated.get("lending_history", {})
    
    protocol_analysis = lending_history.get("protocol_analysis", {})
    credit_assessment = calculate_credit_assessment(protocol_analysis)
    
    enriched_tokens = raw_tokens
    concentration = aggregated["tokens"]["concentration"]
    
    transfer_analysis = analyze_transfers(transfers)
    defi_activity = aggregated["defi_analysis"]["protocol_interactions"]
    mixer_check = aggregated["defi_analysis"]["mixer_check"]
    nft_quality = analyze_nft_quality(nfts)
    stablecoin_data = aggregated["defi_analysis"]["stablecoins"]
    
    volatility_risk = calculate_volatility_risk(enriched_tokens)
    
    eth_balance = aggregated["eth_balance"]
    
    token_value = calculate_token_value(enriched_tokens)
    nft_data = calculate_nft_value(nfts["legit_nfts"])
    
    eth_price = 2800
    total_assets = token_value + nft_data["total_value"] * eth_price + (eth_balance * eth_price)
    
    stablecoin_score = calculate_stablecoin_score(stablecoin_data, total_assets)

    payment_score = 0
    
    if credit_assessment.get("has_borrowing_activity"):
        credit_subscore = (credit_assessment["credit_score"] / 100) * 150
        payment_score += credit_subscore
        
        if credit_assessment["creditworthiness"] == "EXCELLENT":
            payment_score += 30
        elif credit_assessment["creditworthiness"] == "GOOD":
            payment_score += 20
        
        if credit_assessment["has_default_history"]:
            payment_score -= 50
    else:
        payment_score += 50
    
    if defi_activity["aave"]:
        payment_score += 20
    if defi_activity["compound"]:
        payment_score += 15
    if defi_activity["ethena"]:
        payment_score += 15
    if defi_activity["morpho"]:
        payment_score += 10
    if defi_activity["total_protocols"] >= 3:
        payment_score += 20
    
    if transfer_analysis["active_months"] > 12:
        payment_score += 30
    elif transfer_analysis["active_months"] > 6:
        payment_score += 15
    
    if transfer_analysis["avg_tx_per_month"] > 5:
        payment_score += 20
    elif transfer_analysis["avg_tx_per_month"] > 2:
        payment_score += 10
    
    if transfer_analysis.get("dormant_periods", 0) == 0:
        payment_score += 15
    
    payment_score = min(payment_score, 298)
    
    amounts_score = 0
    
    amounts_score += stablecoin_score['liquidity_score'] * 1.0
    
    asset_score = min(total_assets * 0.01, 100)
    amounts_score += asset_score
    
    if eth_balance > 10:
        amounts_score += 55
    elif eth_balance > 1:
        amounts_score += 35
    elif eth_balance > 0.1:
        amounts_score += 15
    
    amounts_score = min(amounts_score, 255)
    
    history_score = 0
    
    wallet_age_years = transfer_analysis["age_days"] / 365
    history_score += min(wallet_age_years * 30, 80)
    
    tx_score = min(transfer_analysis["tx_count"] * 0.5, 48)
    history_score += tx_score
    
    history_score = min(history_score, 128)
    
    new_credit_score = 0
    
    if defi_activity["total_protocols"] > 0:
        new_credit_score += min(defi_activity["total_protocols"] * 20, 60)
    
    if transfer_analysis["tx_count"] < 1000:
        new_credit_score += 25
    
    new_credit_score = min(new_credit_score, 85)
    
    mix_score = 0
    
    diversification_bonus = concentration['diversification_score'] * 0.4
    mix_score += diversification_bonus
    
    mix_score += min(defi_activity["total_protocols"] * 10, 45)
    
    mix_score = min(mix_score, 85)
    
    reputation_bonus = 0
    
    poap_bonus = min(nfts["counts"]["poaps"] * 3, 40)
    reputation_bonus += poap_bonus
    
    if nfts["counts"]["ens"] > 0:
        reputation_bonus += 25
    
    verified_bonus = min(nft_quality["verified_count"] * 5, 60)
    reputation_bonus += verified_bonus
    
    blue_chip_bonus = min(nft_data["blue_chip_count"] * 15, 50)
    reputation_bonus += blue_chip_bonus
    
    if defi_activity.get("staking_events", 0) > 0:
        reputation_bonus += min(defi_activity["staking_events"] * 5, 30)
    
    if credit_assessment.get("has_borrowing_activity") and not credit_assessment.get("has_default_history"):
        reputation_bonus += 40
    
    reputation_bonus = min(reputation_bonus, 200)
    
    risk_penalty = 0
    
    if mixer_check["has_mixer_interaction"]:
        risk_penalty += 200
    
    if concentration['top_1_concentration'] > 0.8:
        risk_penalty += 100
    elif concentration['top_1_concentration'] > 0.5:
        risk_penalty += 50
    
    if volatility_risk['risk_score'] > 70:
        risk_penalty += 80
    elif volatility_risk['risk_score'] > 50:
        risk_penalty += 40
    
    spam_ratio = nfts["counts"]["spam"] / max(nfts["counts"]["total"], 1)
    if spam_ratio > 0.5:
        risk_penalty += 80
    elif spam_ratio > 0.2:
        risk_penalty += 40
    
    if transfer_analysis["eth_in"] > 0:
        imbalance = transfer_analysis["eth_out"] / transfer_analysis["eth_in"]
        if imbalance > 10:
            risk_penalty += 150
        elif imbalance > 5:
            risk_penalty += 70
    
    if nft_quality["verification_rate"] < 0.3 and nfts["counts"]["legit"] > 5:
        risk_penalty += 30
    
    if credit_assessment.get("total_liquidations", 0) > 0:
        liquidation_penalty = min(credit_assessment["total_liquidations"] * 30, 100)
        risk_penalty += liquidation_penalty
    
    base_score = (
        payment_score +
        amounts_score +
        history_score +
        new_credit_score +
        mix_score
    )
    
    final_score = base_score + reputation_bonus - risk_penalty
    
    final_score = max(0, min(final_score, 850))
    
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
        "credit_history": {
            "credit_score": credit_assessment["credit_score"],
            "creditworthiness": credit_assessment["creditworthiness"],
            "total_borrows": credit_assessment["total_borrowing_events"],
            "total_repays": credit_assessment["total_repayment_events"],
            "total_liquidations": credit_assessment["total_liquidations"],
            "repayment_ratio": round(credit_assessment["repayment_ratio"], 2),
            "has_borrowing_activity": credit_assessment["has_borrowing_activity"],
            "has_default_history": credit_assessment["has_default_history"],
            "lending_protocols": credit_assessment["lending_protocols_used"]
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
            "dormant_periods": transfer_analysis.get("dormant_periods", 0) > 2,
            "has_liquidations": credit_assessment["total_liquidations"] > 0,
            "poor_repayment": credit_assessment.get("has_borrowing_activity") and credit_assessment["repayment_ratio"] < 0.5
        }
    }