import time
import requests
import statistics
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.models import AssetTransferParams
from src.classifiers import classify_nfts
from src.config import Settings, MIXER_ADDRESSES, DEFI_PROTOCOLS, STABLECOINS, BLUE_CHIP_NFTS, PROTOCOL_ADDRESSES
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import defaultdict

settings = Settings()

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

def fetch_token_metadata(contract_address: str) -> Optional[Dict]:
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

def fetch_token_price_alchemy(contract_address: str) -> Optional[Dict]:
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

def fetch_token_prices(contracts: List[str]) -> Dict[str, float]:
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
        
        if contract_addr.lower() in [addr.lower() for addr in BLUE_CHIP_NFTS]:
            floor = max(floor, 0.5)
        
        values[f"{contract_addr}_{token_id}"] = floor
    return values

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

def fetch_wallet_events_etherscan(
    wallet: str,
    start_block: int = 0,
    end_block: str = "latest",
    page: int = 1,
    offset: int = 1000,
    sort: str = "asc"
) -> List[Dict]:
    """
    Fetch wallet transaction history from Etherscan API
    
    Args:
        wallet: Ethereum wallet address
        start_block: Starting block number (default: 0)
        end_block: Ending block number (default: "latest")
        page: Page number for pagination (default: 1)
        offset: Number of transactions per page (default: 1000, max: 10000)
        sort: Sort order - "asc" or "desc" (default: "asc")
    
    Returns:
        List of transaction dictionaries
    """
    
    # Setup retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    
    all_transactions = []
    current_page = page
    
    # Etherscan API endpoint
    base_url = "https://api.etherscan.io/v2/api"
    
    while True:
        params = {
            "chainid": 1,
            "module": "account",
            "action": "txlist",
            "address": wallet,
            "startblock": start_block,
            "endblock": end_block,
            "page": current_page,
            "offset": offset,
            "sort": sort,
            "apikey": settings.ETHERSCAN_API_KEY  # Make sure to add this to your settings
        }
        
        try:
            response = session.get(
                base_url,
                params=params,
                timeout=120
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check if the API call was successful
            if data.get("status") != "1":
                error_message = data.get("message", "Unknown error")
                print(f"Etherscan API error: {error_message}")
                break
            
            transactions = data.get("result", [])
            
            if not transactions:
                break
            
            all_transactions.extend(transactions)
            
            # If we got fewer transactions than the offset, we've reached the end
            if len(transactions) < offset:
                break
            
            current_page += 1
            
            time.sleep(0.2)
            
        except requests.exceptions.Timeout:
            print(f"Request timed out for wallet {wallet} after 120s.")
            break
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            break
    
    return all_transactions

def categorize_lending_event(function_name: str) -> Optional[str]:
    if not function_name:
        return None
    
    function_name_lower = function_name.lower()
    
    for signature, category in LENDING_EVENT_SIGNATURES.items():
        if signature.lower() in function_name_lower:
            return category
    
    return None

def analyze_protocol_interactions(transactions: List[Dict]) -> Dict:
    protocol_map = {addr.lower(): name for name, addr in PROTOCOL_ADDRESSES.items()}
    
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
                "transactions": []
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
        
        protocol_stats[contract_address]["transactions"].append({
            "tx_hash": tx.get("hash"),
            "function_name": function_signature,
            "event_type": event_category or "other",
            "block_number": tx.get("blockNumber"),
            "timestamp": timestamp_iso,
            "value": tx.get("value", "0"),
            "is_error": tx.get("isError") == "1"
        })
    
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

def fetch_protocol_lending_history(wallet: str) -> Dict:
    try:
        transactions = fetch_wallet_events_etherscan(wallet=wallet)
        print("transactions", transactions)

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