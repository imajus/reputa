"""
Treasury and risk analysis service
Handles NAV calculation, liquidity analysis, stress testing, and debt coverage
"""
from typing import Dict, List
from collections import defaultdict


def calculate_treasury_nav(enriched_tokens: List[Dict], eth_balance: float, eth_price: float = 2800) -> Dict:
    token_value = sum(t.get('value_usd', 0) for t in enriched_tokens)
    eth_value = eth_balance * eth_price
    total_nav = token_value + eth_value
    
    asset_categories = defaultdict(float)
    for token in enriched_tokens:
        category = token.get('category', 'unknown')
        asset_categories[category] += token.get('value_usd', 0)
    
    return {
        'current_nav_usd': total_nav,
        'token_value_usd': token_value,
        'eth_value_usd': eth_value,
        'eth_balance': eth_balance,
        'asset_breakdown': dict(asset_categories),
        'largest_asset_category': max(asset_categories.items(), key=lambda x: x[1])[0] if asset_categories else None
    }


def measure_liquidity_buffers(enriched_tokens: List[Dict], stablecoin_data: Dict) -> Dict:
    total_stablecoins = stablecoin_data.get('total_stablecoin_usd', 0)
    
    liquid_assets = total_stablecoins
    
    for token in enriched_tokens:
        symbol = token.get('symbol', '').upper()
        if symbol in ['WETH', 'WBTC', 'USDC', 'USDT', 'DAI']:
            if token.get('category') != 'stablecoin':
                liquid_assets += token.get('value_usd', 0)
    
    total_assets = sum(t.get('value_usd', 0) for t in enriched_tokens)
    liquidity_ratio = liquid_assets / max(total_assets, 1)
    
    estimated_monthly_burn = 500
    runway_months = liquid_assets / estimated_monthly_burn
    
    return {
        'liquid_assets_usd': liquid_assets,
        'total_assets_usd': total_assets,
        'liquidity_ratio': liquidity_ratio,
        'estimated_runway_months': runway_months,
        'liquidity_health': 'excellent' if liquidity_ratio > 0.5
                           else 'good' if liquidity_ratio > 0.3
                           else 'moderate' if liquidity_ratio > 0.15
                           else 'poor'
    }


def stress_test_treasury(treasury_nav: Dict, enriched_tokens: List[Dict]) -> Dict:
    current_nav = treasury_nav.get('current_nav_usd', 0)
    
    scenarios = {}
    
    for shock_pct in [30, 50, 70]:
        shock_factor = 1 - (shock_pct / 100)
        
        shocked_value = 0
        for token in enriched_tokens:
            category = token.get('category', 'unknown')
            value = token.get('value_usd', 0)
            
            if category == 'stablecoin':
                shocked_value += value * 0.98
            else:
                shocked_value += value * shock_factor
        
        scenarios[f'-{shock_pct}%'] = {
            'nav_usd': shocked_value,
            'nav_loss_usd': current_nav - shocked_value,
            'nav_loss_pct': ((current_nav - shocked_value) / max(current_nav, 1)) * 100
        }
    
    critical_threshold_pct = 50
    
    return {
        'current_nav_usd': current_nav,
        'stress_scenarios': scenarios,
        'critical_threshold_pct': critical_threshold_pct,
        'stress_resilience': 'high' if scenarios['-50%']['nav_usd'] > current_nav * 0.4
                            else 'moderate' if scenarios['-50%']['nav_usd'] > current_nav * 0.3
                            else 'low'
    }


def calculate_debt_service_coverage(protocol_analysis: Dict, treasury_nav: Dict, wallet_metadata: Dict) -> Dict:
    total_txs = wallet_metadata.get('total_transactions', 0)
    wallet_age_days = wallet_metadata.get('wallet_age_days', 1)
    monthly_tx_volume = (total_txs / max(wallet_age_days / 30, 1))
    
    estimated_monthly_revenue = monthly_tx_volume * 10
    
    total_borrows = protocol_analysis['summary'].get('total_borrow_events', 0)
    total_repays = protocol_analysis['summary'].get('total_repay_events', 0)
    outstanding = total_borrows - total_repays
    
    estimated_debt = outstanding * 1000
    monthly_interest = (estimated_debt * 0.05) / 12
    
    dscr = estimated_monthly_revenue / max(monthly_interest, 1)
    
    return {
        'estimated_monthly_revenue': estimated_monthly_revenue,
        'estimated_outstanding_debt': estimated_debt,
        'estimated_monthly_interest': monthly_interest,
        'debt_service_coverage_ratio': dscr,
        'coverage_health': 'excellent' if dscr > 2.5
                          else 'good' if dscr > 1.5
                          else 'adequate' if dscr > 1.0
                          else 'poor',
        'can_service_debt': dscr > 1.0
    }


def model_stress_scenarios(treasury_nav: Dict, debt_coverage: Dict) -> Dict:
    current_revenue = debt_coverage.get('estimated_monthly_revenue', 0)
    current_interest = debt_coverage.get('estimated_monthly_interest', 0)
    liquid_assets = treasury_nav.get('current_nav_usd', 0) * 0.3
    
    stress_scenarios = {}
    
    for revenue_shock in [30, 50, 70]:
        shocked_revenue = current_revenue * (1 - revenue_shock/100)
        net_cash_flow = shocked_revenue - current_interest
        
        if net_cash_flow < 0:
            months_to_insolvency = liquid_assets / abs(net_cash_flow)
        else:
            months_to_insolvency = float('inf')
        
        stress_scenarios[f'-{revenue_shock}%_revenue'] = {
            'monthly_revenue': shocked_revenue,
            'monthly_interest': current_interest,
            'net_cash_flow': net_cash_flow,
            'months_to_insolvency': months_to_insolvency if months_to_insolvency != float('inf') else None,
            'can_survive': months_to_insolvency > 12 or months_to_insolvency == float('inf')
        }
    
    breakpoint_found = False
    for shock in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
        shocked_revenue = current_revenue * (1 - shock/100)
        if shocked_revenue < current_interest:
            breakpoint_revenue_shock = shock
            breakpoint_found = True
            break
    
    return {
        'stress_scenarios': stress_scenarios,
        'breakpoint_revenue_shock_pct': breakpoint_revenue_shock if breakpoint_found else 90,
        'stress_resilience': 'high' if not breakpoint_found or breakpoint_revenue_shock > 60
                            else 'moderate' if breakpoint_revenue_shock > 40
                            else 'low'
    }