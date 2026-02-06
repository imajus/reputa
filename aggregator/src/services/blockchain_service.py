"""
Blockchain data fetching service
Handles all interactions with blockchain APIs (Alchemy, Etherscan)
"""
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.models import AssetTransferParams
from src.config import Settings

settings = Settings()


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
            "apikey": settings.ETHERSCAN_API_KEY
        }
        
        try:
            response = session.get(
                settings.ETHERSCAN_API_URL,
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