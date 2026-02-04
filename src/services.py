# services.py (ENHANCED VERSION)
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.models import AssetTransferParams
from src.classifiers import classify_nfts
from src.config import Settings, MIXER_ADDRESSES, DEFI_PROTOCOLS, STABLECOINS, BLUE_CHIP_NFTS

settings = Settings()

# === NFT Fetchers ===
def fetch_all_nfts(wallet: str) -> List[Dict]:
    all_nfts = []
    params = {"owner": wallet, "withMetadata": "true", "pageSize": 100}
    while True:
        r = requests.get(f"{settings.ALCHEMY_NFT_URL}/getNFTsForOwner", params=params)
        r.raise_for_status()
        data = r.json()
        all_nfts.extend(data.get("ownedNfts", []))
        if not data.get("pageKey"):
            break
        params["pageKey"] = data["pageKey"]
    return all_nfts

# === Token Fetchers ===
def fetch_token_balances(wallet: str) -> List[Dict]:
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenBalances",
        "params": [wallet, "erc20"]
    }
    r = requests.post(settings.ALCHEMY_CORE_URL, json=payload)
    r.raise_for_status()
    balances = r.json()["result"]["tokenBalances"]
    return [b for b in balances if int(b["tokenBalance"], 16) > 0]

def fetch_eth_balance(wallet: str) -> float:
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet, "latest"]
    }
    r = requests.post(settings.ALCHEMY_CORE_URL, json=payload)
    r.raise_for_status()
    balance_hex = r.json()["result"]
    balance_wei = int(balance_hex, 16)
    return balance_wei / (10 ** 18)

def fetch_token_metadata_batch(contract_addresses: List[str]) -> List[Dict]:
    if not contract_addresses:
        return []
    payload = {"contractAddresses": contract_addresses}
    r = requests.post(f"{settings.ALCHEMY_NFT_URL}/getContractMetadataBatch", json=payload)
    if r.status_code != 200:
        return []
    return r.json().get("contracts", [])

# === ENHANCED: Token Metadata (Individual) ===
def fetch_token_metadata(contract_address: str) -> Optional[Dict]:
    """Fetch detailed metadata for a single token using Alchemy"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getTokenMetadata",
            "params": [contract_address],
            "id": 1
        }
        
        r = requests.post(settings.ALCHEMY_CORE_URL, json=payload)
        r.raise_for_status()
        result = r.json()
        
        return result.get('result')
    except Exception as e:
        print(f"Error fetching metadata for {contract_address}: {e}")
        return None

# === ENHANCED: Alchemy Prices API (Better than CoinGecko) ===
def fetch_token_price_alchemy(contract_address: str) -> Optional[Dict]:
    """Fetch current token price using Alchemy Prices API"""
    try:
        url = f"https://api.g.alchemy.com/prices/v1/{settings.ALCHEMY_API_KEY}/tokens/by-address"
        
        params = {
            'network': 'eth-mainnet',
            'addresses': contract_address
        }
        
        r = requests.get(url, params=params)
        
        if r.status_code == 200:
            data = r.json()
            if data.get('data') and len(data['data']) > 0:
                token_data = data['data'][0]
                prices = token_data.get('prices', [])
                if prices:
                    return {
                        'price': prices[0].get('value', 0),
                        'currency': prices[0].get('currency', 'usd'),
                        'timestamp': token_data.get('lastUpdatedAt'),
                        'symbol': token_data.get('symbol'),
                        'name': token_data.get('name')
                    }
        
        return None
    except Exception as e:
        print(f"Error fetching price from Alchemy for {contract_address}: {e}")
        return None

def fetch_historical_prices_alchemy(contract_address: str, days: int = 30) -> Optional[List[Dict]]:
    """Fetch historical prices for volatility calculation"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        url = f"https://api.g.alchemy.com/prices/v1/{settings.ALCHEMY_API_KEY}/tokens/historical"
        
        params = {
            'network': 'eth-mainnet',
            'address': contract_address,
            'startTime': int(start_time.timestamp()),
            'endTime': int(end_time.timestamp()),
            'interval': '1d'
        }
        
        r = requests.get(url, params=params)
        
        if r.status_code == 200:
            data = r.json()
            return data.get('data', {}).get('prices', [])
        
        return None
    except Exception as e:
        print(f"Error fetching historical prices: {e}")
        return None

def calculate_volatility(prices: List[Dict]) -> Optional[float]:
    """Calculate 30-day price volatility (standard deviation of returns)"""
    if not prices or len(prices) < 2:
        return None
    
    try:
        price_values = [p.get('value', 0) for p in prices if p.get('value') is not None and p.get('value') != 0]
        
        if len(price_values) < 2:
            return None
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(price_values)):
            if price_values[i-1] and price_values[i] and price_values[i-1] > 0:
                daily_return = (price_values[i] - price_values[i-1]) / price_values[i-1]
                returns.append(daily_return)
                
        if not returns:
            return None
        
        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        if variance is None or variance < 0:
            return None
            
        volatility = variance ** 0.5
        
        return volatility * 100  # Convert to percentage
    except:
        return None

# === ENHANCED: Enrich Tokens with Prices & Metadata ===
def enrich_token_data(tokens: List[Dict]) -> List[Dict]:
    """Enrich token balances with metadata, prices, and volatility"""
    enriched = []
    
    for token in tokens:
        contract_address = token.get('contractAddress')
        raw_balance = token.get('tokenBalance')
        
        if not contract_address or not raw_balance:
            continue
        
        # Convert hex balance
        balance_int = int(raw_balance, 16) if isinstance(raw_balance, str) else raw_balance
        
        # Get metadata
        metadata = fetch_token_metadata(contract_address)
        
        if not metadata:
            # Fallback to basic data
            enriched.append({
                **token,
                'balance_human': balance_int / (10 ** 18),  # Assume 18 decimals
                'current_price_usd': 0,
                'value_usd': 0,
                'symbol': 'UNKNOWN',
                'name': 'Unknown Token'
            })
            continue
        
        # Calculate human-readable balance
        decimals = metadata.get('decimals') or 18
        if not isinstance(decimals, int) or decimals < 0:
            decimals = 18
        balance = balance_int / (10 ** decimals)
        
        # Get price from Alchemy (primary) or fall back to CoinGecko
        price_data = fetch_token_price_alchemy(contract_address)
        
        if price_data:
            current_price = price_data.get('price', 0)
        else:
            # Fallback to CoinGecko
            prices = fetch_token_prices([contract_address])
            current_price = prices.get(contract_address, 0)
        
        value_usd = balance * current_price
        
        # Get volatility
        historical = fetch_historical_prices_alchemy(contract_address, days=30)
        volatility = calculate_volatility(historical) if historical else None
        
        # Categorize token
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

def categorize_token(symbol: str, address: str) -> str:
    """Categorize token type"""
    symbol_upper = symbol.upper() if symbol else ''
    address_lower = address.lower()
    
    # Stablecoins
    stablecoins = ['USDC', 'USDT', 'DAI', 'USDE', 'DEUSD', 'EUSDE', 'FRAX', 'LUSD']
    if symbol_upper in stablecoins or 'USD' in symbol_upper:
        return 'stablecoin'
    
    # Governance tokens
    governance = ['ENA', 'SENA', 'UNI', 'AAVE', 'COMP', 'MKR', 'CRV', 'BAL']
    if symbol_upper in governance:
        return 'governance'
    
    # Liquid staking derivatives
    lsd = ['STETH', 'RETH', 'CBETH', 'STDEUSD', 'WSTETH']
    if symbol_upper in lsd or symbol_upper.startswith('ST'):
        return 'liquid_staking'
    
    # Wrapped assets
    if symbol_upper.startswith('W'):
        return 'wrapped'
    
    return 'unknown'

# === ENHANCED: Portfolio Concentration Analysis ===
def calculate_portfolio_concentration(enriched_tokens: List[Dict]) -> Dict:
    """Calculate portfolio concentration metrics"""
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
    
    # Sort by value
    sorted_tokens = sorted(enriched_tokens, key=lambda x: x.get('value_usd', 0), reverse=True)
    
    # Calculate Herfindahl Index (sum of squared market shares)
    herfindahl = sum((t.get('value_usd', 0) / total_value) ** 2 for t in enriched_tokens if t.get('value_usd') is not None)
    
    # Top concentrations
    top_1 = sorted_tokens[0].get('value_usd', 0) / total_value if sorted_tokens else 0
    top_3 = sum(t.get('value_usd', 0) for t in sorted_tokens[:3]) / total_value if len(sorted_tokens) >= 3 else top_1
    top_5 = sum(t.get('value_usd', 0) for t in sorted_tokens[:5]) / total_value if len(sorted_tokens) >= 5 else top_3
    
    # Diversification score (inverse of concentration, 0-100)
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

# === Transfer Fetchers ===
def fetch_asset_transfers(wallet: str, params: AssetTransferParams, is_from: bool = False) -> List[Dict]:
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": params.fromBlock,
            "toBlock": params.toBlock,
            "excludeZeroValue": params.excludeZeroValue,
            "maxCount": params.maxCount,
            "category": params.category,
            "withMetadata": True
        }]
    }
    key = "fromAddress" if is_from else "toAddress"
    payload["params"][0][key] = wallet
    
    r = requests.post(settings.ALCHEMY_CORE_URL, json=payload)
    r.raise_for_status()
    transfers = r.json()["result"].get("transfers", [])
    page_key = r.json()["result"].get("pageKey")
    
    while page_key:
        payload["params"][0]["pageKey"] = page_key
        r = requests.post(settings.ALCHEMY_CORE_URL, json=payload)
        r.raise_for_status()
        transfers.extend(r.json()["result"].get("transfers", []))
        page_key = r.json()["result"].get("pageKey")
    
    return transfers

# === ENHANCED: DeFi Analysis with Ethena Detection ===
def check_defi_interactions(transfers: Dict[str, List[Dict]]) -> Dict:
    all_transfers = transfers["incoming"] + transfers["outgoing"]
    
    interactions = {
        "aave": False,
        "compound": False,
        "uniswap": False,
        "curve": False,
        "ethena": False,  # NEW: Ethena staking
        "morpho": False,  # NEW: Morpho lending
        "total_protocols": 0,
        "staking_events": 0,  # NEW: Count staking operations
        "protocol_details": []  # NEW: Detailed protocol interaction list
    }
    
    # Extended protocol list
    EXTENDED_PROTOCOLS = {
        **DEFI_PROTOCOLS,
        'ethena_sena': '0x8be3460a480c80728a8c4d7a5d5303c85ba7b3b9',
        'ethena_eusde': '0x90d2af7d622ca3141efa4d8f1f24d86e5974cc8f',
        'ethena_usde': '0x4c9edd5852cd905f086c759e8383e09bff1e68b3',
        'ethena_deusd': '0x15700b564ca08d9439c58ca5053166e8317aa138',
        'ethena_stdeusd': '0x5c5b196abe0d54485975d1ec29617d42d9198326',
        'morpho_blue': '0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb',
    }
    
    protocol_addresses = set()
    
    for tx in all_transfers:
        to_addr = (tx.get("to") or "").lower()
        from_addr = (tx.get("from") or "").lower()
        
        for protocol_name, protocol_addr in EXTENDED_PROTOCOLS.items():
            if to_addr == protocol_addr.lower() or from_addr == protocol_addr.lower():
                # Track protocol category
                if "aave" in protocol_name:
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
                    # Count staking if interacting with sENA or eUSDe
                    if 'sena' in protocol_name or 'eusde' in protocol_name or 'stdeusd' in protocol_name:
                        interactions["staking_events"] += 1
                elif "morpho" in protocol_name:
                    interactions["morpho"] = True
                    protocol_addresses.add("morpho")
                
                # Add to detailed list
                interactions["protocol_details"].append({
                    'protocol': protocol_name,
                    'address': protocol_addr,
                    'transaction_hash': tx.get('hash'),
                    'timestamp': tx.get('metadata', {}).get('blockTimestamp'),
                    'category': tx.get('category')
                })
    
    interactions["total_protocols"] = len(protocol_addresses)
    print("interactions:", interactions)
    return interactions

def check_mixer_interactions(transfers: Dict[str, List[Dict]]) -> Dict:
    all_transfers = transfers["incoming"] + transfers["outgoing"]
    
    mixer_txs = []
    for tx in all_transfers:
        to_addr = (tx.get("to") or "").lower()
        from_addr = (tx.get("from") or "").lower()
        
        for mixer in MIXER_ADDRESSES:
            if to_addr == mixer.lower() or from_addr == mixer.lower():
                mixer_txs.append(tx)
    
    return {
        "has_mixer_interaction": len(mixer_txs) > 0,
        "mixer_tx_count": len(mixer_txs),
        "mixer_transactions": mixer_txs
    }

def analyze_stablecoin_holdings(tokens: List[Dict]) -> Dict:
    """ENHANCED: Works with enriched token data"""
    stablecoin_balance = 0.0
    stablecoin_details = []
    
    for token in tokens:
        # Handle both enriched and raw token data
        if 'category' in token and token['category'] == 'stablecoin':
            balance_usd = token.get('value_usd', 0)
            stablecoin_balance += balance_usd
            stablecoin_details.append({
                'symbol': token.get('symbol'),
                'balance_usd': balance_usd,
                'balance_human': token.get('balance_human', 0)
            })
        else:
            # Fallback to old method
            addr = token.get("contractAddress", "").lower()
            if addr in [v.lower() for v in STABLECOINS.values()]:
                balance = int(token["tokenBalance"], 16) / (10 ** 6)
                stablecoin_balance += balance
    
    return {
        "total_stablecoin_usd": stablecoin_balance,
        "has_stablecoins": stablecoin_balance > 0,
        "stablecoin_breakdown": stablecoin_details
    }

# === Price Fetchers (Keep CoinGecko as fallback) ===
def fetch_token_prices(contracts: List[str]) -> Dict[str, float]:
    """CoinGecko fallback for price fetching"""
    if not contracts:
        return {}
    params = {"contract_addresses": ",".join(contracts), "vs_currencies": "usd"}
    r = requests.get(settings.COINGECKO_URL, params=params)
    if r.status_code != 200:
        return {}
    prices = {}
    data = r.json()
    for addr in contracts:
        price_data = data.get(addr.lower(), {})
        prices[addr] = price_data.get("usd", 0.0)
    return prices

def estimate_nft_values(nfts: List[Dict]) -> Dict[str, float]:
    values = {}
    for nft in nfts:
        floor = nft.get("contract", {}).get("openSeaMetadata", {}).get("floorPrice") or 0.0
        token_id = nft.get("tokenId")
        contract_addr = nft.get("contract", {}).get("address", "")
        
        # Blue chip bonus
        if contract_addr.lower() in [addr.lower() for addr in BLUE_CHIP_NFTS]:
            floor = max(floor, 0.5)  # Minimum value for blue chips
        
        values[f"{contract_addr}_{token_id}"] = floor
    return values

# === ENHANCED: Wallet Activity Metrics ===
def calculate_wallet_metadata(transfers: Dict[str, List[Dict]], wallet_address: str) -> Dict:
    """Calculate comprehensive wallet metadata"""
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
    
    # Extract timestamps
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
    
    # Parse timestamps
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
    
    # Calculate unique counterparties
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