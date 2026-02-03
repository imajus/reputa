"""
Blockchain Data Aggregator
Fetches wallet data using Alchemy API: tokens, NFTs, POAPs, ENS, transactions
"""

import asyncio
import aiohttp
from typing import List, Set
from datetime import datetime

from src.config import settings
from src.credit_scorer import (
    WalletData, Token, NFT, POAP, RWA, 
    Transaction, DeFiPosition, CreditScorer
)


class DataAggregator:
    """
    Aggregator that fetches wallet data using Alchemy API:
    - ETH and ERC20 token balances
    - NFTs (including POAPs and ENS)
    - Transaction history
    - Scam and mixer detection
    """
    
    def __init__(self, alchemy_key: str):
        self.alchemy_key = alchemy_key
        self.alchemy_base = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"
        self.alchemy_nft_base = f"https://eth-mainnet.g.alchemy.com/nft/v3/{alchemy_key}"
        
        self.stablecoins = {
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
            "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
            "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
        }
        
        self.mixers = {
            "0x722122df12d4e14e13ac3b6895a86e84145b6967",
            "0x07687e702b410fa43f4cb4af7fa097918ffd2730",
            "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",
            "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
            "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        }
        
        self.known_scams = {
            "0x94f1b9b64e2932f6a2db338f616844400cd58e8a",
            "0xbda83686c90314cfbaaeb18db46723d83fdf0c83",
            "0xba36735021a9ccd7582ebc7f70164794154ff30e",
        }
        
        self.poap_contract = "0x22c1f6050e56d2876009903609a2cc3fef83b415"
        self.ens_contract = "0xd4416b13d2b3a9abae7acd5d6c2bbdbe25686401"
    
    async def get_wallet_data(self, address: str) -> WalletData:
        """Fetch all wallet data"""
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                self._get_eth_balance(session, address),
                self._get_tokens(session, address),
                self._get_nfts_and_poaps(session, address),
                self._get_transactions(session, address),
                self._get_wallet_age(session, address),
                return_exceptions=True
            )
            
            eth_balance = results[0] if not isinstance(results[0], Exception) else 0.0
            tokens = results[1] if not isinstance(results[1], Exception) else []
            nft_data = results[2] if not isinstance(results[2], Exception) else ([], [], [])
            transactions = results[3] if not isinstance(results[3], Exception) else []
            wallet_age = results[4] if not isinstance(results[4], Exception) else 0
            
            nfts, poaps, ens_names = nft_data
            
            scam_interactions = self._detect_scam_interactions(transactions)
            mixer_usage = self._detect_mixer_usage(transactions)
        
        return WalletData(
            address=address,
            wallet_age_days=wallet_age,
            eth_balance=eth_balance,
            tokens=tokens,
            nfts=nfts,
            poaps=poaps,
            ens_names=ens_names,
            rwas=[],
            transactions=transactions,
            defi_positions=[],
            chains=["ethereum"],
            scam_interactions=scam_interactions,
            mixer_usage=mixer_usage,
            balance_history=[]
        )
    
    async def _get_eth_balance(self, session: aiohttp.ClientSession, address: str) -> float:
        """Fetch ETH balance using eth_getBalance"""
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"]
            }
            
            async with session.post(self.alchemy_base, json=payload) as resp:
                data = await resp.json()
                
                if "result" in data:
                    balance_wei = int(data["result"], 16)
                    balance_eth = balance_wei / 1e18
                    return balance_eth
        
        except Exception as e:
            print(f"Error fetching ETH balance: {e}")
        
        return 0.0
    
    async def _get_tokens(self, session: aiohttp.ClientSession, address: str) -> List[Token]:
        """Fetch ERC20 token balances"""
        tokens = []
        
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "alchemy_getTokenBalances",
                "params": [address, "erc20"]
            }
            
            async with session.post(self.alchemy_base, json=payload) as resp:
                data = await resp.json()
                
                if "result" not in data:
                    return tokens
                
                for token_data in data["result"]["tokenBalances"]:
                    contract = token_data["contractAddress"].lower()
                    balance_hex = token_data["tokenBalance"]
                    
                    if balance_hex == "0x0" or balance_hex == "0x00":
                        continue
                    
                    balance_int = int(balance_hex, 16)
                    if balance_int == 0:
                        continue
                    
                    metadata = await self._get_token_metadata(session, contract)
                    if not metadata:
                        continue
                    
                    decimals = metadata.get("decimals", 18)
                    balance = balance_int / (10 ** decimals)
                    
                    is_stable = contract in self.stablecoins
                    price = 1.0 if is_stable else 0.0
                    value_usd = balance * price
                    
                    tokens.append(Token(
                        symbol=metadata.get("symbol", "UNKNOWN"),
                        balance=balance,
                        value_usd=value_usd,
                        is_stable=is_stable
                    ))
        
        except Exception as e:
            print(f"Error fetching tokens: {e}")
        
        return tokens
    
    async def _get_token_metadata(self, session: aiohttp.ClientSession, contract: str) -> dict:
        """Get token metadata"""
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "alchemy_getTokenMetadata",
                "params": [contract]
            }
            
            async with session.post(self.alchemy_base, json=payload) as resp:
                data = await resp.json()
                return data.get("result", {})
        except:
            return {}
    
    async def _get_nfts_and_poaps(
        self, 
        session: aiohttp.ClientSession, 
        address: str
    ) -> tuple[List[NFT], List[POAP], List[str]]:
        """
        Fetch NFTs using Alchemy NFT API
        Separates regular NFTs, POAPs, and ENS names
        """
        nfts = []
        poaps = []
        ens_names = []
        
        try:
            url = f"{self.alchemy_nft_base}/getNFTsForOwner"
            params = {
                "owner": address,
                "withMetadata": "true",
                "pageSize": "100"
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return nfts, poaps, ens_names
                
                data = await resp.json()
                
                if "ownedNfts" not in data:
                    return nfts, poaps, ens_names
                
                for nft_data in data["ownedNfts"]:
                    contract_addr = nft_data.get("contract", {}).get("address", "").lower()
                    
                    if contract_addr == self.poap_contract:
                        poap = self._parse_poap(nft_data)
                        if poap:
                            poaps.append(poap)
                    
                    elif contract_addr == self.ens_contract:
                        ens_name = nft_data.get("name", "")
                        if ens_name:
                            ens_names.append(ens_name)
                    
                    else:
                        is_spam = nft_data.get("contract", {}).get("isSpam", False)
                        if not is_spam:
                            collection = nft_data.get("contract", {}).get("name", "Unknown")
                            floor_price = nft_data.get("contract", {}).get("openSeaMetadata", {}).get("floorPrice", 0.0)
                            
                            eth_price = 3000.0
                            value_usd = floor_price * eth_price if floor_price else 100.0
                            
                            nfts.append(NFT(
                                collection=collection,
                                value_usd=value_usd
                            ))
        
        except Exception as e:
            print(f"Error fetching NFTs: {e}")
        
        return nfts, poaps, ens_names
    
    def _parse_poap(self, nft_data: dict) -> POAP:
        """Parse POAP data from NFT response"""
        try:
            name = nft_data.get("name", "Unknown Event")
            description = nft_data.get("description", "")
            
            mint_info = nft_data.get("mint", {})
            timestamp = mint_info.get("timestamp")
            
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    date = datetime.now()
            else:
                date = datetime.now()
            
            category = self._categorize_poap(name)
            
            return POAP(
                event_name=name,
                date=date,
                category=category
            )
        
        except Exception as e:
            print(f"Error parsing POAP: {e}")
            return None
    
    def _categorize_poap(self, event_name: str) -> str:
        """Categorize POAP based on event name"""
        name_lower = event_name.lower()
        
        if any(kw in name_lower for kw in ["ethglobal", "devcon", "eth denver", "consensus", "token2049"]):
            return "conference"
        elif any(kw in name_lower for kw in ["workshop", "bootcamp", "course", "tutorial"]):
            return "educational"
        elif any(kw in name_lower for kw in ["meetup", "community", "local"]):
            return "community"
        elif any(kw in name_lower for kw in ["hackathon", "buidl"]):
            return "hackathon"
        else:
            return "other"
    
    async def _get_transactions(
        self, 
        session: aiohttp.ClientSession, 
        address: str
    ) -> List[Transaction]:
        """Fetch transaction history using alchemy_getAssetTransfers"""
        transactions = []
        
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "alchemy_getAssetTransfers",
                "params": [{
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "toAddress": address,
                    "withMetadata": False,
                    "excludeZeroValue": True,
                    "maxCount": "0x3e8",
                    "category": ["external", "internal", "erc20", "erc721", "erc1155"]
                }]
            }
            
            async with session.post(self.alchemy_base, json=payload) as resp:
                data = await resp.json()
                
                if "result" not in data or "transfers" not in data["result"]:
                    return transactions
                
                eth_price = 3000.0
                
                for transfer in data["result"]["transfers"]:
                    value = transfer.get("value", 0)
                    value_usd = value * eth_price if isinstance(value, (int, float)) else 0.0
                    
                    from_addr = transfer.get("from", "")
                    to_addr = transfer.get("to", "")
                    block_num = transfer.get("blockNum", "0x0")
                    
                    try:
                        timestamp = datetime.now()
                    except:
                        timestamp = datetime.now()
                    
                    transactions.append(Transaction(
                        timestamp=timestamp,
                        value_usd=value_usd,
                        gas_paid_usd=0.0,
                        from_address=from_addr,
                        to_address=to_addr
                    ))
        
        except Exception as e:
            print(f"Error fetching transactions: {e}")
        
        return transactions
    
    def _detect_scam_interactions(self, transactions: List[Transaction]) -> Set[str]:
        """Detect interactions with known scam addresses"""
        scam_interactions = set()
        
        for tx in transactions:
            to_addr = tx.to_address.lower() if tx.to_address else ""
            from_addr = tx.from_address.lower() if hasattr(tx, 'from_address') and tx.from_address else ""
            
            if to_addr in self.known_scams:
                scam_interactions.add(to_addr)
            if from_addr in self.known_scams:
                scam_interactions.add(from_addr)
        
        return scam_interactions
    
    def _detect_mixer_usage(self, transactions: List[Transaction]) -> bool:
        """Detect if wallet used privacy mixers"""
        for tx in transactions:
            to_addr = tx.to_address.lower() if tx.to_address else ""
            from_addr = tx.from_address.lower() if hasattr(tx, 'from_address') and tx.from_address else ""
            
            if to_addr in self.mixers or from_addr in self.mixers:
                return True
        
        return False
    
    async def _get_wallet_age(self, session: aiohttp.ClientSession, address: str) -> int:
        """Get wallet age by finding first transaction"""
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "alchemy_getAssetTransfers",
                "params": [{
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "fromAddress": address,
                    "withMetadata": False,
                    "excludeZeroValue": False,
                    "maxCount": "0x1",
                    "category": ["external"]
                }]
            }
            
            async with session.post(self.alchemy_base, json=payload) as resp:
                data = await resp.json()
                
                if "result" in data and "transfers" in data["result"] and data["result"]["transfers"]:
                    first_tx = data["result"]["transfers"][0]
                    block_num = first_tx.get("blockNum", "0x0")
                    
                    block_payload = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "eth_getBlockByNumber",
                        "params": [block_num, False]
                    }
                    
                    async with session.post(self.alchemy_base, json=block_payload) as block_resp:
                        block_data = await block_resp.json()
                        
                        if "result" in block_data and block_data["result"]:
                            timestamp_hex = block_data["result"].get("timestamp", "0x0")
                            timestamp = int(timestamp_hex, 16)
                            first_date = datetime.fromtimestamp(timestamp)
                            age = (datetime.now() - first_date).days
                            return max(0, age)
        
        except Exception as e:
            print(f"Error fetching wallet age: {e}")
        
        return 0