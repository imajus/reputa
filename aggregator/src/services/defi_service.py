"""
DeFi analysis service
Handles protocol interactions, mixer detection, and stablecoin analysis
"""
from typing import Dict, List, Set
from collections import defaultdict

from src.config import DEFI_PROTOCOLS, MIXER_ADDRESSES, STABLECOINS


def check_defi_interactions(transfers: Dict[str, List[Dict]]) -> Dict:
    all_transfers = transfers["incoming"] + transfers["outgoing"]
    
    interactions = {
        "aave": False,
        "compound": False,
        "uniswap": False,
        "curve": False,
        "ethena": False,
        "morpho": False,
        "total_protocols": 0,
        "staking_events": 0,
        "protocol_details": []
    }
    
    protocol_addresses = set()
    
    for tx in all_transfers:
        to_addr = (tx.get("to") or "").lower()
        from_addr = (tx.get("from") or "").lower()
        
        for protocol_name, protocol_addr in DEFI_PROTOCOLS.items():
            if to_addr == protocol_addr.lower() or from_addr == protocol_addr.lower():
                if "Aave V3" in protocol_name:
                    interactions["aave"] = True
                    protocol_addresses.add("aave")
                elif "compound" in protocol_name:
                    interactions["compound"] = True
                    protocol_addresses.add("compound")
                elif "uniswap" in protocol_name:
                    interactions["uniswap"] = True
                    protocol_addresses.add("uniswap")
                elif "curve" in protocol_name:
                    interactions["curve"] = True
                    protocol_addresses.add("curve")
                elif "ethena" in protocol_name:
                    interactions["ethena"] = True
                    protocol_addresses.add("ethena")
                    if 'sena' in protocol_name or 'eusde' in protocol_name or 'stdeusd' in protocol_name:
                        interactions["staking_events"] += 1
                elif "morpho" in protocol_name:
                    interactions["morpho"] = True
                    protocol_addresses.add("morpho")
                
                interactions["protocol_details"].append({
                    'protocol': protocol_name,
                    'address': protocol_addr,
                    'transaction_hash': tx.get('hash'),
                    'timestamp': tx.get('metadata', {}).get('blockTimestamp'),
                    'category': tx.get('category')
                })
    
    interactions["total_protocols"] = len(protocol_addresses)
    return interactions


def check_mixer_interactions(transfers: Dict[str, List[Dict]]) -> Dict:
    incoming = transfers.get("incoming", [])
    outgoing = transfers.get("outgoing", [])
    all_transfers = incoming + outgoing

    mixers = {m.lower() for m in MIXER_ADDRESSES}

    total_count = 0
    per_mixer_count = defaultdict(int)
    tx_hashes: Set[str] = set()
    counterparties: Set[str] = set()

    first_ts = None
    last_ts = None

    incoming_count = 0
    outgoing_count = 0

    for tx in all_transfers:
        to_addr = (tx.get("to") or "").lower()
        from_addr = (tx.get("from") or "").lower()
        ts = tx.get("metadata", {}).get("blockTimestamp")
        tx_hash = tx.get("hash")

        hit_mixer = None
        if to_addr in mixers:
            hit_mixer = to_addr
            outgoing_count += 1
            counterparties.add(from_addr)
        elif from_addr in mixers:
            hit_mixer = from_addr
            incoming_count += 1
            counterparties.add(to_addr)

        if not hit_mixer:
            continue

        total_count += 1
        per_mixer_count[hit_mixer] += 1

        if tx_hash:
            tx_hashes.add(tx_hash)

        if ts:
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts

    return {
        "has_mixer_interaction": total_count > 0,
        "mixer_tx_count": total_count,
        "unique_mixers": list(per_mixer_count.keys()),
        "per_mixer_tx_count": dict(per_mixer_count),
        "incoming_mixer_txs": incoming_count,
        "outgoing_mixer_txs": outgoing_count,
        "first_interaction_timestamp": first_ts,
        "last_interaction_timestamp": last_ts,
        "unique_counterparties": len(counterparties),
        "tx_hashes": list(tx_hashes),
    }


def analyze_stablecoin_holdings(tokens: List[Dict]) -> Dict:
    stablecoin_balance = 0.0
    stablecoin_details = []
    
    for token in tokens:
        if 'category' in token and token['category'] == 'stablecoin':
            balance_usd = token.get('value_usd', 0)
            stablecoin_balance += balance_usd
            stablecoin_details.append({
                'symbol': token.get('symbol'),
                'balance_usd': balance_usd,
                'balance_human': token.get('balance_human', 0)
            })
        else:
            addr = token.get("contractAddress", "").lower()
            if addr in [v.lower() for v in STABLECOINS.values()]:
                balance = int(token["tokenBalance"], 16) / (10 ** 6)
                stablecoin_balance += balance
    
    return {
        "total_stablecoin_usd": stablecoin_balance,
        "has_stablecoins": stablecoin_balance > 0,
        "stablecoin_breakdown": stablecoin_details
    }