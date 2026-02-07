"""
Token analysis service
Handles token enrichment, categorization, and portfolio analysis
"""
from typing import List, Dict, Optional

from .blockchain_service import (
    fetch_token_metadata,
    fetch_token_price_alchemy,
    fetch_historical_prices_alchemy,
    fetch_token_prices
)
from src.config import BLUE_CHIP_NFTS


def calculate_volatility(prices: List[Dict]) -> Optional[float]:
    if not prices or len(prices) < 2:
        return None
    
    try:
        price_values = [p.get('value', 0) for p in prices if p.get('value') is not None and p.get('value') != 0]
        
        if len(price_values) < 2:
            return None
        
        returns = []
        for i in range(1, len(price_values)):
            if price_values[i-1] and price_values[i] and price_values[i-1] > 0:
                daily_return = (price_values[i] - price_values[i-1]) / price_values[i-1]
                returns.append(daily_return)
                
        if not returns:
            return None
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        if variance is None or variance < 0:
            return None
            
        volatility = variance ** 0.5
        
        return volatility * 100
    except:
        return None


def categorize_token(symbol: str, address: str) -> str:
    symbol_upper = symbol.upper() if symbol else ''
    address_lower = address.lower()
    
    stablecoins = ['USDC', 'USDT', 'DAI', 'USDE', 'DEUSD', 'EUSDE', 'FRAX', 'LUSD']
    if symbol_upper in stablecoins or 'USD' in symbol_upper:
        return 'stablecoin'
    
    governance = ['ENA', 'SENA', 'UNI', 'AAVE', 'COMP', 'MKR', 'CRV', 'BAL']
    if symbol_upper in governance:
        return 'governance'
    
    lsd = ['STETH', 'RETH', 'CBETH', 'STDEUSD', 'WSTETH']
    if symbol_upper in lsd or symbol_upper.startswith('ST'):
        return 'liquid_staking'
    
    if symbol_upper.startswith('W'):
        return 'wrapped'
    
    return 'unknown'


def enrich_token_data(tokens: List[Dict]) -> List[Dict]:
    enriched = []
    
    for token in tokens:
        contract_address = token.get('contractAddress')
        raw_balance = token.get('tokenBalance')
        
        if not contract_address or not raw_balance:
            continue
        
        balance_int = int(raw_balance, 16) if isinstance(raw_balance, str) else raw_balance
        
        metadata = fetch_token_metadata(contract_address)
        
        if not metadata:
            enriched.append({
                **token,
                'balance_human': balance_int / (10 ** 18),
                'current_price_usd': 0,
                'value_usd': 0,
                'symbol': 'UNKNOWN',
                'name': 'Unknown Token'
            })
            continue
        
        decimals = metadata.get('decimals') or 18
        if not isinstance(decimals, int) or decimals < 0:
            decimals = 18
        balance = balance_int / (10 ** decimals)
        
        price_data = fetch_token_price_alchemy(contract_address)
        
        if price_data:
            current_price = price_data.get('price', 0)
        else:
            prices = fetch_token_prices([contract_address])
            current_price = prices.get(contract_address, 0)
        
        value_usd = balance * current_price
        
        historical = fetch_historical_prices_alchemy(contract_address, days=30)
        volatility = calculate_volatility(historical) if historical else None
        
        category = categorize_token(metadata.get('symbol', ''), contract_address)
        
        enriched.append({
            **token,
            'contract_address': contract_address,
            'symbol': metadata.get('symbol'),
            'name': metadata.get('name'),
            'decimals': decimals,
            'balance_human': balance,
            'balance_raw': balance_int,
            'current_price_usd': current_price,
            'value_usd': value_usd,
            'category': category,
            'volatility_30d': volatility,
            'logo': metadata.get('logo'),
            'metadata': metadata
        })
    
    return enriched


def calculate_portfolio_concentration(enriched_tokens: List[Dict]) -> Dict:
    if not enriched_tokens:
        return {
            'herfindahl_index': 0,
            'top_1_concentration': 0,
            'top_3_concentration': 0,
            'top_5_concentration': 0,
            'diversification_score': 0,
            'num_tokens': 0
        }
    
    total_value = sum(t.get('value_usd', 0) for t in enriched_tokens)
    
    if total_value == 0:
        return {
            'herfindahl_index': 0,
            'top_1_concentration': 0,
            'top_3_concentration': 0,
            'top_5_concentration': 0,
            'diversification_score': 0,
            'num_tokens': len(enriched_tokens)
        }
    
    sorted_tokens = sorted(enriched_tokens, key=lambda x: x.get('value_usd', 0), reverse=True)
    
    herfindahl = sum((t.get('value_usd', 0) / total_value) ** 2 for t in enriched_tokens if t.get('value_usd') is not None)
    
    top_1 = sorted_tokens[0].get('value_usd', 0) / total_value if sorted_tokens else 0
    top_3 = sum(t.get('value_usd', 0) for t in sorted_tokens[:3]) / total_value if len(sorted_tokens) >= 3 else top_1
    top_5 = sum(t.get('value_usd', 0) for t in sorted_tokens[:5]) / total_value if len(sorted_tokens) >= 5 else top_3
    
    diversification = (1 - herfindahl) * 100
    
    return {
        'herfindahl_index': herfindahl,
        'top_1_concentration': top_1,
        'top_3_concentration': top_3,
        'top_5_concentration': top_5,
        'diversification_score': diversification,
        'num_tokens': len(enriched_tokens),
        'total_value_usd': total_value
    }


def estimate_nft_values(nfts: List[Dict]) -> Dict[str, float]:
    values = {}
    for nft in nfts:
        floor = nft.get("contract", {}).get("openSeaMetadata", {}).get("floorPrice") or 0.0
        token_id = nft.get("tokenId")
        contract_addr = nft.get("contract", {}).get("address", "")
        
        if contract_addr.lower() in [addr.lower() for addr in BLUE_CHIP_NFTS]:
            floor = max(floor, 0.5)
        
        values[f"{contract_addr}_{token_id}"] = floor
    return values


def analyze_token_velocity(wallet_address: str, enriched_tokens: List[Dict]) -> Dict:
    """
    Analyze how quickly tokens move through the wallet
    """
    from .blockchain_service import fetch_asset_transfers
    from src.models import AssetTransferParams
    
    params = AssetTransferParams()
    incoming = fetch_asset_transfers(wallet_address, params, is_from=False)
    outgoing = fetch_asset_transfers(wallet_address, params, is_from=True)
    
    # Calculate token-specific velocity
    token_flows = {}
    
    for tx in incoming + outgoing:
        token = tx.get('asset', 'ETH')
        value = float(tx.get('value', 0))
        
        if token not in token_flows:
            token_flows[token] = {'inflow': 0, 'outflow': 0, 'net': 0}
        
        if tx in incoming:
            token_flows[token]['inflow'] += value
        else:
            token_flows[token]['outflow'] += value
        
        token_flows[token]['net'] = token_flows[token]['inflow'] - token_flows[token]['outflow']
    
    # Calculate velocity (turnover ratio)
    for token in token_flows:
        total_flow = token_flows[token]['inflow'] + token_flows[token]['outflow']
        current_balance = next((t['balance_human'] for t in enriched_tokens 
                               if t.get('symbol') == token), 0)
        
        if current_balance > 0:
            token_flows[token]['velocity'] = total_flow / current_balance
        else:
            token_flows[token]['velocity'] = 0
    
    avg_velocity = sum(t['velocity'] for t in token_flows.values()) / max(len(token_flows), 1)
    
    return {
        'token_flows': token_flows,
        'average_velocity': avg_velocity,
        'velocity_health': 'healthy' if 2 <= avg_velocity <= 10 else 
                          'low' if avg_velocity < 2 else 'high',
        'net_positive_tokens': sum(1 for t in token_flows.values() if t['net'] > 0),
        'net_negative_tokens': sum(1 for t in token_flows.values() if t['net'] < 0)
    }