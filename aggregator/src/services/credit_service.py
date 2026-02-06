"""
Credit assessment service
Main orchestrator for comprehensive credit analysis
"""
from typing import Dict, List
from datetime import datetime

from .lending_service import (
    extract_repayment_timelines,
    measure_repayment_punctuality,
    analyze_borrowing_frequency,
    detect_emergency_repayments,
    analyze_protocol_performance,
    detect_capital_looping
)
from .treasury_service import (
    calculate_treasury_nav,
    measure_liquidity_buffers,
    stress_test_treasury,
    calculate_debt_service_coverage,
    model_stress_scenarios
)


def complete_credit_assessment(aggregated_data: Dict) -> Dict:
    protocol_analysis = aggregated_data['lending_history']['protocol_analysis']
    enriched_tokens = aggregated_data['tokens']['holdings']
    wallet_metadata = aggregated_data['wallet_metadata']
    eth_balance = aggregated_data['eth_balance']
    stablecoin_data = aggregated_data['defi_analysis']['stablecoins']
        
    # - Analyzing credit performance
    repayment_timelines = extract_repayment_timelines(protocol_analysis)
    punctuality = measure_repayment_punctuality(repayment_timelines)
    borrowing_freq = analyze_borrowing_frequency(protocol_analysis, wallet_metadata)
    emergency_repay = detect_emergency_repayments(protocol_analysis)
    protocol_perf = analyze_protocol_performance(protocol_analysis)
    
    # - Assessing balance sheet
    treasury_nav = calculate_treasury_nav(enriched_tokens, eth_balance)
    liquidity = measure_liquidity_buffers(enriched_tokens, stablecoin_data)
    stress_test = stress_test_treasury(treasury_nav, enriched_tokens)
    
    # - Analyzing capital usage
    looping = detect_capital_looping(protocol_analysis)
    
    # - Evaluating cash flows
    debt_coverage = calculate_debt_service_coverage(protocol_analysis, treasury_nav, wallet_metadata)
    stress_scenarios = model_stress_scenarios(treasury_nav, debt_coverage)
    
    # - Assessment complete
    assessment = {
        'wallet': aggregated_data['wallet'],
        'assessment_date': datetime.utcnow().isoformat(),
        
        '1_past_credit_performance': {
            'repayment_timelines': repayment_timelines,
            'punctuality': punctuality,
            'borrowing_frequency': borrowing_freq,
            'emergency_repayments': emergency_repay,
            'protocol_performance': protocol_perf
        },
        
        '2_balance_sheet': {
            'treasury_nav': treasury_nav,
            'liquidity_buffers': liquidity,
            'stress_test': stress_test
        },
        
        '3_use_of_proceeds': {
            'looping_detection': looping
        },
        
        '4_cash_flows': {
            'debt_service_coverage': debt_coverage,
            'stress_scenarios': stress_scenarios
        }
    }
    
    credit_score = calculate_credit_score_comprehensive(assessment, aggregated_data)
    assessment['credit_score'] = credit_score

    return assessment


def calculate_credit_score_comprehensive(assessment: Dict, aggregated_data: Dict) -> Dict:
    perf = assessment['1_past_credit_performance']
    balance = assessment['2_balance_sheet']
    proceeds = assessment['3_use_of_proceeds']
    cash = assessment['4_cash_flows']
    
    base_score = 300
    max_score = 850
    
    payment_score = 0
    punctuality = perf['punctuality']['punctuality_score']
    payment_score += punctuality
    
    timelines = perf['repayment_timelines']
    if timelines['total_borrowings'] > 0:
        repayment_ratio = timelines['repaid_count'] / timelines['total_borrowings']
        payment_score += repayment_ratio * 50
    
    protocol_perf = perf['protocol_performance']
    if protocol_perf['total_protocols_used'] > 0:
        avg_repayment_rate = protocol_perf['average_repayment_rate']
        payment_score += avg_repayment_rate * 42.5
    
    payment_score = min(payment_score, 192.5)
    
    leverage_score = 0
    
    liquidity = balance['liquidity_buffers']
    liquidity_ratio = liquidity['liquidity_ratio']
    if liquidity_ratio > 0.5:
        leverage_score += 40
    elif liquidity_ratio > 0.3:
        leverage_score += 30
    elif liquidity_ratio > 0.15:
        leverage_score += 20
    else:
        leverage_score += 10
    
    stress = balance['stress_test']
    stress_resilience = stress['stress_resilience']
    stress_points = {
        'high': 37.5,
        'moderate': 20,
        'low': 5
    }
    leverage_score += stress_points.get(stress_resilience, 0)
    
    leverage_score = min(leverage_score, 137.5)
    
    proceeds_score = 0
    
    looping = proceeds['looping_detection']
    loop_ratio = looping['loop_ratio']
    
    if loop_ratio == 0:
        proceeds_score += 60
    elif loop_ratio < 0.3:
        proceeds_score += 45
    elif loop_ratio < 0.6:
        proceeds_score += 25
    else:
        proceeds_score += 5
    
    proceeds_score += 50
    
    proceeds_score = min(proceeds_score, 110)
    
    cashflow_score = 0
    
    dscr = cash['debt_service_coverage']['debt_service_coverage_ratio']
    
    if dscr > 2.5:
        cashflow_score += 70
    elif dscr > 1.5:
        cashflow_score += 55
    elif dscr > 1.0:
        cashflow_score += 35
    elif dscr > 0.5:
        cashflow_score += 15
    else:
        cashflow_score += 5
    
    stress_scenarios = cash['stress_scenarios']
    stress_resilience = stress_scenarios['stress_resilience']
    
    stress_cashflow_points = {
        'high': 40,
        'moderate': 25,
        'low': 10
    }
    cashflow_score += stress_cashflow_points.get(stress_resilience, 0)
    
    cashflow_score = min(cashflow_score, 110)
    
    penalties = 0
    
    if perf['emergency_repayments']['has_emergency_behavior']:
        emergency_count = perf['emergency_repayments']['emergency_repayment_count']
        penalties += min(emergency_count * 10, 40)
    
    outstanding = timelines.get('outstanding_count', 0)
    if outstanding > 0:
        penalties += min(outstanding * 15, 50)
    
    if looping['has_looping_behavior'] and loop_ratio > 0.5:
        penalties += 30
    
    diversification = aggregated_data.get('tokens', {}).get('concentration', {})
    herfindahl = diversification.get('herfindahl_index', 0)
    if herfindahl > 0.8:
        penalties += 25
    
    raw_score = (
        base_score +
        payment_score +
        leverage_score +
        proceeds_score +
        cashflow_score -
        penalties
    )
    
    final_score = max(300, min(int(raw_score), max_score))
    
    if final_score >= 800:
        grade = 'AAA'
        risk_level = 'Very Low'
    elif final_score >= 750:
        grade = 'AA'
        risk_level = 'Low'
    elif final_score >= 700:
        grade = 'A'
        risk_level = 'Low-Medium'
    elif final_score >= 650:
        grade = 'BBB'
        risk_level = 'Medium'
    elif final_score >= 600:
        grade = 'BB'
        risk_level = 'Medium-High'
    elif final_score >= 550:
        grade = 'B'
        risk_level = 'High'
    elif final_score >= 500:
        grade = 'CCC'
        risk_level = 'Very High'
    else:
        grade = 'D'
        risk_level = 'Default Risk'
    
    return {
        'credit_score': final_score,
        'grade': grade,
        'risk_level': risk_level,
        'score_breakdown': {
            'payment_history': round(payment_score, 2),
            'leverage_solvency': round(leverage_score, 2),
            'use_of_proceeds': round(proceeds_score, 2),
            'cash_flow': round(cashflow_score, 2),
            'base_score': base_score,
            'penalties': round(penalties, 2)
        },
        'component_weights': {
            'payment_history': '35%',
            'leverage_solvency': '25%',
            'use_of_proceeds': '20%',
            'cash_flow': '20%'
        },
        'key_strengths': _identify_strengths(perf, balance, proceeds, cash),
        'key_risks': _identify_risks(perf, balance, proceeds, cash, penalties)
    }


def _identify_strengths(perf, balance, proceeds, cash) -> List[str]:
    strengths = []
    
    if perf['punctuality']['punctuality_score'] > 80:
        strengths.append("Strong payment history")
    
    if balance['liquidity_buffers']['liquidity_health'] in ['excellent', 'good']:
        strengths.append("Strong liquidity reserves")
    
    if cash['debt_service_coverage']['debt_service_coverage_ratio'] > 1.5:
        strengths.append("Healthy debt service coverage")
    
    if proceeds['looping_detection']['loop_ratio'] < 0.3:
        strengths.append("Responsible capital usage")
    
    return strengths[:3]


def _identify_risks(perf, balance, proceeds, cash, penalties) -> List[str]:
    risks = []
    
    if perf['repayment_timelines']['outstanding_count'] > 0:
        risks.append(f"{perf['repayment_timelines']['outstanding_count']} outstanding loans")
    
    if balance['liquidity_buffers']['liquidity_health'] == 'poor':
        risks.append("Limited liquidity buffer")
    
    if perf['emergency_repayments']['has_emergency_behavior']:
        risks.append("History of emergency repayments")
    
    if proceeds['looping_detection']['loop_ratio'] > 0.5:
        risks.append("Excessive capital recycling")
    
    if cash['debt_service_coverage']['debt_service_coverage_ratio'] < 1.0:
        risks.append("Insufficient debt service coverage")
    
    return risks[:3]