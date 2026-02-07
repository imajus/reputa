"""
Wallet metadata service
Handles wallet age, transaction history, and counterparty analysis
"""
import requests
from typing import Dict, List
from datetime import datetime
from src.config import Settings
from .blockchain_service import fetch_wallet_events_etherscan

settings = Settings()

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

def analyze_transaction_patterns(wallet_address: str, transactions: List[Dict]) -> Dict:
    """
    Analyze transaction patterns using Etherscan API
    """
       
    if not transactions:
        return {
            'total_transactions': 0,
            'successful_tx_rate': 0,
            'average_gas_price': 0,
            'total_gas_spent': 0
        }
    
    successful_txs = [tx for tx in transactions if tx.get('isError') == '0']
    failed_txs = [tx for tx in transactions if tx.get('isError') == '1']
    
    total_gas_used = sum(int(tx.get('gasUsed', 0)) * int(tx.get('gasPrice', 0)) 
                         for tx in successful_txs) / 1e18
    
    avg_gas_price = sum(int(tx.get('gasPrice', 0)) for tx in transactions) / len(transactions) / 1e9
    
    # Activity consistency
    tx_dates = [datetime.fromtimestamp(int(tx['timeStamp'])) for tx in transactions]
    if len(tx_dates) > 1:
        date_diffs = [(tx_dates[i] - tx_dates[i-1]).days for i in range(1, len(tx_dates))]
        avg_days_between_tx = sum(date_diffs) / len(date_diffs)
    else:
        avg_days_between_tx = 0
    
    return {
        'total_transactions': len(transactions),
        'successful_transactions': len(successful_txs),
        'failed_transactions': len(failed_txs),
        'success_rate': len(successful_txs) / len(transactions) if transactions else 0,
        'total_gas_spent_eth': total_gas_used,
        'average_gas_price_gwei': avg_gas_price,
        'average_days_between_transactions': avg_days_between_tx,
        'transaction_consistency_score': min(100, 100 / (avg_days_between_tx + 1))
    }