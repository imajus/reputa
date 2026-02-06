"""
Wallet metadata service
Handles wallet age, transaction history, and counterparty analysis
"""
from typing import Dict, List
from datetime import datetime


def calculate_wallet_metadata(transfers: Dict[str, List[Dict]], wallet_address: str) -> Dict:
    incoming = transfers.get('incoming', [])
    outgoing = transfers.get('outgoing', [])
    
    all_transfers = incoming + outgoing
    
    if not all_transfers:
        return {
            'first_transaction_date': None,
            'last_transaction_date': None,
            'wallet_age_days': 0,
            'total_transactions': 0,
            'incoming_transactions': 0,
            'outgoing_transactions': 0,
            'unique_counterparties': 0,
            'average_txs_per_month': 0,
            'error': 'No transaction data available'
        }
    
    timestamps = []
    for tx in all_transfers:
        ts = tx.get('metadata', {}).get('blockTimestamp')
        if ts:
            timestamps.append(ts)
    
    if not timestamps:
        return {
            'first_transaction_date': None,
            'wallet_age_days': 0,
            'total_transactions': len(all_transfers),
            'error': 'No timestamp data available'
        }
    
    parsed_timestamps = []
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            parsed_timestamps.append(dt)
        except:
            continue
    
    if not parsed_timestamps:
        return {
            'first_transaction_date': None,
            'wallet_age_days': 0,
            'total_transactions': len(all_transfers)
        }
    
    first_tx = min(parsed_timestamps)
    last_tx = max(parsed_timestamps)
    now = datetime.utcnow()
    
    wallet_age = (now - first_tx.replace(tzinfo=None)).days
    
    unique_counterparties = set()
    for tx in all_transfers:
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()
        
        if from_addr != wallet_address.lower():
            unique_counterparties.add(from_addr)
        if to_addr != wallet_address.lower():
            unique_counterparties.add(to_addr)
    
    return {
        'first_transaction_date': first_tx.isoformat(),
        'last_transaction_date': last_tx.isoformat(),
        'wallet_age_days': wallet_age,
        'total_transactions': len(all_transfers),
        'incoming_transactions': len(incoming),
        'outgoing_transactions': len(outgoing),
        'unique_counterparties': len(unique_counterparties),
        'average_txs_per_month': (len(all_transfers) / max(wallet_age / 30, 1))
    }