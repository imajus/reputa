from urllib import response
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.models import AssetTransferParams
from src.classifiers import classify_nfts
from src.config import Settings, MIXER_ADDRESSES, DEFI_PROTOCOLS, STABLECOINS, BLUE_CHIP_NFTS, PROTOCOL_ADDRESSES
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

settings = Settings()


LENDING_EVENT_SIGNATURES = {
    "Borrow": "borrow",
    "Repay": "repay",
    "Liquidate": "liquidate",
    "LiquidationCall": "liquidate",
    "Supply": "supply",
    "Withdraw": "withdraw",
    "Deposit": "supply",
    "Redeem": "withdraw",
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

def fetch_wallet_events_bitquery(
    wallet: str,
    from_date: Optional[str] = None,
    till_date: Optional[str] = None,
    page_size: int = 100,
    max_results: int = 1000
) -> List[Dict]:
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not till_date:
        till_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    query = """
    query WalletEventsWithinRange($network: evm_network!, $wallet: String!, $from: DateTime!, $till: DateTime!, $limit: Int!, $offset: Int!) {
      EVM(dataset: archive, network: $network) {
        Events(
          limit: { count: $limit, offset: $offset }
          orderBy: { descendingByField: "Block_Time" }
          where: {
            Block: { Time: { since: $from, till: $till } }
            any: [
              { Transaction: { From: { is: $wallet } } },
              { Transaction: { To: { is: $wallet } } },
              { Topics: { includes: { Hash: { is: $wallet } } } }
            ]
          }
        ) {
          Block { Number Time }
          Transaction { Hash From To }
          Log { Signature { Name } SmartContract }
          Topics { Hash }
        }
      }
    }
    """
    
    # 1. Setup a Retry Strategy
    retry_strategy = Retry(
        total=3, # Try 3 times
        backoff_factor=2, # Wait 2s, 4s, 8s between retries
        status_forcelist=[429, 500, 502, 503, 504], # Retry on these errors
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)

    all_events = []
    offset = 0
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.BITQUERY_TOKEN}",
        "User-Agent": "curl/8.5.0",
        "Accept": "*/*"
    }
    
    while True:
        variables = {
            "network": "eth",
            "wallet": wallet,
            "from": from_date,
            "till": till_date,
            "limit": page_size,
            "offset": offset
        }
        
        try:            
            # 2. Increased timeout to 120 seconds
            response = session.post(
                settings.BITQUERY_URL, 
                headers=headers, 
                data=json.dumps({"query": query, "variables": variables}),
                timeout=120 
            )
    
            response.raise_for_status()
            data = response.json()
          
            
            if "data" in data and "EVM" in data["data"]:
                events = data["data"]["EVM"]["Events"]
                if not events: break
                    
                all_events.extend(events)
                if len(events) < page_size or len(all_events) >= max_results:
                    break
                
                offset += page_size
            else:
                break
                
        except requests.exceptions.Timeout:
            print(f"Request timed out for wallet {wallet} after 120s. The query might be too heavy.")
            break
        except Exception as e:
            print(f"Error: {e}")
            break
            
    return all_events

def categorize_lending_event(event_name: str) -> Optional[str]:
    if not event_name:
        return None
    
    event_name_lower = event_name.lower()
    
    for signature, category in LENDING_EVENT_SIGNATURES.items():
        if signature.lower() in event_name_lower:
            return category
    
    return None

def analyze_protocol_interactions(events: List[Dict]) -> Dict:
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
    
    for event in events:
        log = event.get("Log", {})
        smart_contract = log.get("SmartContract", "").lower()
        signature = log.get("Signature", {})
        event_name = signature.get("Name", "")
        
        block = event.get("Block", {})
        tx = event.get("Transaction", {})
        
        protocol_name = protocol_map.get(smart_contract, "Unknown Protocol")
        
        if smart_contract not in protocol_stats:
            protocol_stats[smart_contract] = {
                "protocol_name": protocol_name,
                "contract_address": smart_contract,
                "borrow_count": 0,
                "repay_count": 0,
                "liquidate_count": 0,
                "supply_count": 0,
                "withdraw_count": 0,
                "swap_count": 0,
                "stake_count": 0,
                "unstake_count": 0,
                "total_interactions": 0,
                "first_interaction": None,
                "last_interaction": None,
                "transactions": []
            }
        
        event_category = categorize_lending_event(event_name)
        
        if event_category:
            event_summary[event_category] += 1
            protocol_stats[smart_contract][f"{event_category}_count"] += 1
        else:
            event_summary["other"] += 1
        
        protocol_stats[smart_contract]["total_interactions"] += 1
        
        timestamp = block.get("Time")
        if timestamp:
            if not protocol_stats[smart_contract]["first_interaction"]:
                protocol_stats[smart_contract]["first_interaction"] = timestamp
            protocol_stats[smart_contract]["last_interaction"] = timestamp
        
        protocol_stats[smart_contract]["transactions"].append({
            "tx_hash": tx.get("Hash"),
            "event_name": event_name,
            "event_type": event_category or "other",
            "block_number": str(block.get("Number")),
            "timestamp": timestamp
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
            "repayment_ratio": total_repays / total_borrows if total_borrows > 0 else 0
        }
    }
