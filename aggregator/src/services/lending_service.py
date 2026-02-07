"""
Lending protocol analysis service
Handles protocol interaction analysis, event categorization, and borrowing history
"""
import statistics
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from .blockchain_service import fetch_wallet_events_etherscan


LENDING_EVENT_SIGNATURES = {
    "borrow": "borrow",
    "flashLoan": "borrow",
    "flashBorrow": "borrow",
    "repay": "repay",
    "repayBorrow": "repay",
    "repayWithATokens": "repay",
    "repayWithPermit": "repay",
    "liquidate": "liquidate",
    "liquidationCall": "liquidate",
    "liquidateBorrow": "liquidate",
    "supply": "supply",
    "deposit": "supply",
    "mint": "supply",
    "withdraw": "withdraw",
    "redeem": "withdraw",
    "transfer": "transfer",
    "approval": "approval"
}


def categorize_lending_event(function_name: str) -> Optional[str]:
    if not function_name:
        return None
    
    function_name_lower = function_name.lower()
    
    for signature, category in LENDING_EVENT_SIGNATURES.items():
        if signature.lower() in function_name_lower:
            return category
    
    return None


def analyze_protocol_interactions(transactions: List[Dict]) -> Dict:
    from src.config import DEFI_PROTOCOLS
    
    protocol_map = {addr.lower(): name for name, addr in DEFI_PROTOCOLS.items()}
    
    protocol_stats = {}
    event_summary = {
        "borrow": 0,
        "repay": 0,
        "liquidate": 0,
        "supply": 0,
        "withdraw": 0,
        "other": 0
    }
    
    for tx in transactions:
        contract_address = tx.get("to", "").lower()
        if not contract_address:
            continue
            
        function_name = tx.get("functionName", "")
        function_signature = function_name.split("(")[0] if "(" in function_name else function_name
        
        protocol_name = protocol_map.get(contract_address, "Unknown Protocol")
        
        if contract_address not in protocol_stats:
            protocol_stats[contract_address] = {
                "protocol_name": protocol_name,
                "contract_address": contract_address,
                "borrow_count": 0,
                "repay_count": 0,
                "liquidate_count": 0,
                "supply_count": 0,
                "withdraw_count": 0,
                "total_interactions": 0,
                "first_interaction": None,
                "last_interaction": None,
            }
        
        event_category = categorize_lending_event(function_signature)
        
        if event_category and event_category in event_summary:
            event_summary[event_category] += 1
            protocol_stats[contract_address][f"{event_category}_count"] += 1
        else:
            event_summary["other"] += 1
        
        protocol_stats[contract_address]["total_interactions"] += 1
        
        timestamp = int(tx.get("timeStamp", 0))
        timestamp_iso = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None
        
        if timestamp_iso:
            if not protocol_stats[contract_address]["first_interaction"]:
                protocol_stats[contract_address]["first_interaction"] = timestamp_iso
            protocol_stats[contract_address]["last_interaction"] = timestamp_iso
    
    total_borrows = sum(p["borrow_count"] for p in protocol_stats.values())
    total_repays = sum(p["repay_count"] for p in protocol_stats.values())
    total_liquidations = sum(p["liquidate_count"] for p in protocol_stats.values())
    
    return {
        "protocols": protocol_stats,
        "summary": {
            "total_protocols_interacted": len(protocol_stats),
            "total_borrow_events": total_borrows,
            "total_repay_events": total_repays,
            "total_liquidation_events": total_liquidations,
            "total_supply_events": event_summary["supply"],
            "total_withdrawal_events": event_summary["withdraw"],
            "has_borrowing_activity": total_borrows > 0,
            "has_repayment_activity": total_repays > 0,
            "has_liquidation_events": total_liquidations > 0,
            "event_type_distribution": event_summary
        },
        "risk_indicators": {
            "liquidation_risk": "HIGH" if total_liquidations > 0 else "LOW",
            "debt_management": "ACTIVE" if total_repays > 0 or total_borrows > 0 else "INACTIVE",
            "borrowing_activity": "ACTIVE" if total_borrows > 0 else "INACTIVE",
            "repayment_ratio": round(total_repays / total_borrows, 2) if total_borrows > 0 else 0
        }
    }


def fetch_protocol_lending_history(wallet: str, transactions: List[Dict]) -> Dict:
    try:
        if not transactions:
            print(f"No transactions found for wallet {wallet}")
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
                },
                "events_count": 0
            }
        
        protocol_analysis = analyze_protocol_interactions(transactions)
        
        return {
            "protocol_analysis": protocol_analysis,
            "events_count": len(transactions)
        }
        
    except Exception as e:
        print(f"Error in fetch_protocol_lending_history: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "protocol_analysis": {
                "protocols": {},
                "summary": {},
                "risk_indicators": {}
            },
            "events_count": 0
        }


def extract_repayment_timelines(protocol_analysis: Dict) -> Dict:
    protocols = protocol_analysis.get('protocols', {})
    repayment_timelines = []
    
    for contract_addr, proto_data in protocols.items():
        protocol_name = proto_data.get('protocol_name', 'Unknown')
        transactions = proto_data.get('transactions', [])
        
        borrows = [tx for tx in transactions if tx.get('event_type') == 'borrow']
        repays = [tx for tx in transactions if tx.get('event_type') == 'repay']
        
        for i, borrow_tx in enumerate(borrows):
            borrow_time = datetime.fromisoformat(borrow_tx['timestamp'])
            
            matching_repay = None
            repay_time = None
            
            for repay_tx in repays:
                repay_timestamp = datetime.fromisoformat(repay_tx['timestamp'])
                if repay_timestamp > borrow_time:
                    matching_repay = repay_tx
                    repay_time = repay_timestamp
                    break
            
            if matching_repay:
                days_to_repay = (repay_time - borrow_time).days
                
                repayment_timelines.append({
                    'protocol': protocol_name,
                    'borrow_tx': borrow_tx['tx_hash'],
                    'borrow_time': borrow_time.isoformat(),
                    'repay_tx': matching_repay['tx_hash'],
                    'repay_time': repay_time.isoformat(),
                    'days_to_repay': days_to_repay,
                    'status': 'repaid'
                })
            else:
                repayment_timelines.append({
                    'protocol': protocol_name,
                    'borrow_tx': borrow_tx['tx_hash'],
                    'borrow_time': borrow_time.isoformat(),
                    'repay_tx': None,
                    'repay_time': None,
                    'days_to_repay': None,
                    'status': 'outstanding'
                })
    
    repaid_timelines = [t for t in repayment_timelines if t['status'] == 'repaid']
    avg_repayment_days = statistics.mean([t['days_to_repay'] for t in repaid_timelines]) if repaid_timelines else 0
    
    return {
        'timelines': repayment_timelines,
        'total_borrowings': len(repayment_timelines),
        'repaid_count': len(repaid_timelines),
        'outstanding_count': len([t for t in repayment_timelines if t['status'] == 'outstanding']),
        'average_repayment_days': avg_repayment_days,
        'fastest_repayment_days': min([t['days_to_repay'] for t in repaid_timelines]) if repaid_timelines else None,
        'slowest_repayment_days': max([t['days_to_repay'] for t in repaid_timelines]) if repaid_timelines else None
    }


def measure_repayment_punctuality(repayment_timelines: Dict) -> Dict:
    timelines = repayment_timelines.get('timelines', [])
    
    punctuality_classification = {
        'early': 0,
        'on_time': 0,
        'late': 0,
        'outstanding': 0
    }
    
    for timeline in timelines:
        if timeline['status'] == 'outstanding':
            punctuality_classification['outstanding'] += 1
        else:
            days = timeline['days_to_repay']
            if days < 7:
                punctuality_classification['early'] += 1
            elif days <= 90:
                punctuality_classification['on_time'] += 1
            else:
                punctuality_classification['late'] += 1
    
    total_repaid = sum([punctuality_classification[k] for k in ['early', 'on_time', 'late']])
    
    punctuality_score = 0
    if total_repaid > 0:
        punctuality_score = (
            (punctuality_classification['early'] * 100 +
             punctuality_classification['on_time'] * 80 +
             punctuality_classification['late'] * 40) / total_repaid
        )
    
    return {
        'classification': punctuality_classification,
        'punctuality_score': punctuality_score,
        'early_repayment_rate': punctuality_classification['early'] / max(total_repaid, 1),
        'on_time_rate': punctuality_classification['on_time'] / max(total_repaid, 1),
        'late_rate': punctuality_classification['late'] / max(total_repaid, 1)
    }


def analyze_borrowing_frequency(protocol_analysis: Dict, wallet_metadata: Dict) -> Dict:
    protocols = protocol_analysis.get('protocols', {})
    wallet_age_days = wallet_metadata.get('wallet_age_days', 1)
    
    all_borrows = []
    for proto_data in protocols.values():
        borrows = [tx for tx in proto_data.get('transactions', []) 
                  if tx.get('event_type') == 'borrow']
        all_borrows.extend(borrows)
    
    if not all_borrows:
        return {
            'total_borrows': 0,
            'borrows_per_month': 0,
            'frequency_trend': 'none',
            'monthly_distribution': {}
        }
    
    monthly_borrows = defaultdict(int)
    for borrow in all_borrows:
        try:
            dt = datetime.fromisoformat(borrow['timestamp'])
            month_key = f"{dt.year}-{dt.month:02d}"
            monthly_borrows[month_key] += 1
        except:
            continue
    
    total_months = max(wallet_age_days / 30, 1)
    borrows_per_month = len(all_borrows) / total_months
    
    sorted_months = sorted(monthly_borrows.items())
    if len(sorted_months) >= 2:
        midpoint = len(sorted_months) // 2
        first_half_avg = statistics.mean([v for k, v in sorted_months[:midpoint]])
        second_half_avg = statistics.mean([v for k, v in sorted_months[midpoint:]])
        
        if second_half_avg > first_half_avg * 1.2:
            trend = 'increasing'
        elif second_half_avg < first_half_avg * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'insufficient_data'
    
    return {
        'total_borrows': len(all_borrows),
        'borrows_per_month': borrows_per_month,
        'frequency_trend': trend,
        'monthly_distribution': dict(monthly_borrows),
        'most_active_month': max(monthly_borrows.items(), key=lambda x: x[1])[0] if monthly_borrows else None
    }


def detect_emergency_repayments(protocol_analysis: Dict) -> Dict:
    protocols = protocol_analysis.get('protocols', {})
    
    emergency_repayments = []
    
    for proto_data in protocols.values():
        transactions = proto_data.get('transactions', [])
        
        borrows = [tx for tx in transactions if tx.get('event_type') == 'borrow']
        repays = [tx for tx in transactions if tx.get('event_type') == 'repay']
        
        for borrow in borrows:
            borrow_time = datetime.fromisoformat(borrow['timestamp'])
            
            for repay in repays:
                repay_time = datetime.fromisoformat(repay['timestamp'])
                hours_diff = (repay_time - borrow_time).total_seconds() / 3600
                
                if 0 < hours_diff <= 24:
                    emergency_repayments.append({
                        'protocol': proto_data['protocol_name'],
                        'borrow_tx': borrow['tx_hash'],
                        'repay_tx': repay['tx_hash'],
                        'hours_between': hours_diff,
                        'borrow_time': borrow_time.isoformat(),
                        'repay_time': repay_time.isoformat()
                    })
    
    return {
        'emergency_repayment_count': len(emergency_repayments),
        'has_emergency_behavior': len(emergency_repayments) > 0,
        'emergency_repayments': emergency_repayments,
        'crisis_response_score': 100 if len(emergency_repayments) > 0 else 50
    }


def analyze_protocol_performance(protocol_analysis: Dict) -> Dict:
    protocols = protocol_analysis.get('protocols', {})
    
    protocol_performance = {}

    for contract_addr, proto_data in protocols.items():
        protocol_name = proto_data.get('protocol_name')
        borrows = proto_data.get('borrow_count', 0)
        repays = proto_data.get('repay_count', 0)
        liquidations = proto_data.get('liquidate_count', 0)
        
        if borrows > 0 or repays > 0:
            repayment_rate = repays / max(borrows, 1)
            
            protocol_performance[protocol_name] = {
                'borrow_count': borrows,
                'repay_count': repays,
                'liquidation_count': liquidations,
                'repayment_rate': repayment_rate,
                'performance_grade': 'A' if repayment_rate >= 1.0 and liquidations == 0
                                    else 'B' if repayment_rate >= 0.8
                                    else 'C' if repayment_rate >= 0.5
                                    else 'D'
            }
    
    if protocol_performance:
        best_protocol = max(protocol_performance.items(), 
                          key=lambda x: x[1]['repayment_rate'])
        worst_protocol = min(protocol_performance.items(), 
                           key=lambda x: x[1]['repayment_rate'])
    else:
        best_protocol = None
        worst_protocol = None
    
    return {
        'protocol_performance': protocol_performance,
        'total_protocols_used': len(protocol_performance),
        'best_protocol': best_protocol[0] if best_protocol else None,
        'worst_protocol': worst_protocol[0] if worst_protocol else None,
        'average_repayment_rate': statistics.mean([p['repayment_rate'] for p in protocol_performance.values()]) if protocol_performance else 0
    }


def detect_capital_looping(protocol_analysis: Dict) -> Dict:
    protocols = protocol_analysis.get('protocols', {})
    
    looping_detected = []
    
    for _, proto_data in protocols.items():
        transactions = proto_data.get('transactions', [])
        
        for i, tx in enumerate(transactions[:-1]):
            next_tx = transactions[i+1]
            
            tx_type = tx.get('event_type')
            next_type = next_tx.get('event_type')
            
            if tx_type == 'supply' and next_type == 'borrow':
                looping_detected.append({
                    'protocol': proto_data['protocol_name'],
                    'pattern': 'supply_then_borrow',
                    'first_tx': tx['tx_hash'],
                    'second_tx': next_tx['tx_hash'],
                    'leverage_type': 'recursive'
                })
            
            elif tx_type == 'borrow' and next_type == 'supply':
                looping_detected.append({
                    'protocol': proto_data['protocol_name'],
                    'pattern': 'borrow_then_supply',
                    'first_tx': tx['tx_hash'],
                    'second_tx': next_tx['tx_hash'],
                    'leverage_type': 'compound'
                })
    
    total_borrows = protocol_analysis['summary'].get('total_borrow_events', 0)
    loop_ratio = len(looping_detected) / max(total_borrows, 1)
    
    return {
        'looping_instances': looping_detected,
        'looping_count': len(looping_detected),
        'has_looping_behavior': len(looping_detected) > 0,
        'loop_ratio': loop_ratio,
        'leverage_strategy': 'recursive' if loop_ratio > 0.5 else 'none'
    }