"""
Credit Scoring System
Updated to include eth_balance and ens_names
"""

from dataclasses import dataclass, field
from typing import List, Set
from datetime import datetime


@dataclass
class Token:
    symbol: str
    balance: float
    value_usd: float
    is_stable: bool


@dataclass
class NFT:
    collection: str
    value_usd: float


@dataclass
class POAP:
    event_name: str
    date: datetime
    category: str


@dataclass
class RWA:
    protocol: str
    asset_type: str
    value_usd: float


@dataclass
class Transaction:
    timestamp: datetime
    value_usd: float
    gas_paid_usd: float
    to_address: str = ""
    from_address: str = ""


@dataclass
class DeFiPosition:
    protocol: str
    position_type: str
    value_usd: float


@dataclass
class WalletData:
    address: str
    wallet_age_days: int
    eth_balance: float
    tokens: List[Token] = field(default_factory=list)
    nfts: List[NFT] = field(default_factory=list)
    poaps: List[POAP] = field(default_factory=list)
    ens_names: List[str] = field(default_factory=list)
    rwas: List[RWA] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    defi_positions: List[DeFiPosition] = field(default_factory=list)
    chains: List[str] = field(default_factory=list)
    scam_interactions: Set[str] = field(default_factory=set)
    mixer_usage: bool = False
    balance_history: List[float] = field(default_factory=list)


class CreditScorer:
    """
    Credit scoring system based on on-chain activity
    """
    
    def calculate_score(self, data: WalletData) -> dict:
        """Calculate credit score from wallet data"""
        
        score = 0
        breakdown = {}
        
        wallet_age_score = self._score_wallet_age(data.wallet_age_days)
        score += wallet_age_score
        breakdown["wallet_age"] = wallet_age_score
        
        asset_score = self._score_assets(data.eth_balance, data.tokens, data.nfts)
        score += asset_score
        breakdown["assets"] = asset_score
        
        activity_score = self._score_activity(data.transactions)
        score += activity_score
        breakdown["activity"] = activity_score
        
        poap_score = self._score_poaps(data.poaps)
        score += poap_score
        breakdown["poaps"] = poap_score
        
        ens_score = self._score_ens(data.ens_names)
        score += ens_score
        breakdown["ens"] = ens_score
        
        defi_score = self._score_defi(data.defi_positions)
        score += defi_score
        breakdown["defi"] = defi_score
        
        rwa_score = self._score_rwas(data.rwas)
        score += rwa_score
        breakdown["rwa"] = rwa_score
        
        risk_penalty = self._calculate_risk_penalty(data.scam_interactions, data.mixer_usage)
        score -= risk_penalty
        breakdown["risk_penalty"] = -risk_penalty
        
        score = max(300, min(850, score))
        
        return {
            "score": int(score),
            "breakdown": breakdown,
            "risk_level": self._get_risk_level(score)
        }
    
    def _score_wallet_age(self, age_days: int) -> float:
        """Score based on wallet age (max 100 points)"""
        if age_days >= 730:
            return 100
        elif age_days >= 365:
            return 80
        elif age_days >= 180:
            return 60
        elif age_days >= 90:
            return 40
        elif age_days >= 30:
            return 20
        else:
            return 10
    
    def _score_assets(self, eth_balance: float, tokens: List[Token], nfts: List[NFT]) -> float:
        """Score based on asset holdings (max 200 points)"""
        score = 0
        
        eth_price = 3000.0
        eth_value = eth_balance * eth_price
        
        total_token_value = sum(token.value_usd for token in tokens)
        total_nft_value = sum(nft.value_usd for nft in nfts)
        
        total_value = eth_value + total_token_value + total_nft_value
        
        if total_value >= 100000:
            score += 100
        elif total_value >= 50000:
            score += 80
        elif total_value >= 10000:
            score += 60
        elif total_value >= 5000:
            score += 40
        elif total_value >= 1000:
            score += 20
        else:
            score += 10
        
        stable_value = sum(token.value_usd for token in tokens if token.is_stable)
        if stable_value > 0:
            stable_ratio = stable_value / total_value if total_value > 0 else 0
            score += min(50, stable_ratio * 100)
        
        if len(tokens) > 0:
            score += min(30, len(tokens) * 3)
        
        if len(nfts) > 0:
            score += min(20, len(nfts) * 2)
        
        return min(200, score)
    
    def _score_activity(self, transactions: List[Transaction]) -> float:
        """Score based on transaction activity (max 150 points)"""
        score = 0
        
        tx_count = len(transactions)
        
        if tx_count >= 1000:
            score += 60
        elif tx_count >= 500:
            score += 50
        elif tx_count >= 100:
            score += 40
        elif tx_count >= 50:
            score += 30
        elif tx_count >= 10:
            score += 20
        else:
            score += 10
        
        if tx_count > 0:
            total_value = sum(tx.value_usd for tx in transactions)
            avg_value = total_value / tx_count
            
            if avg_value >= 10000:
                score += 40
            elif avg_value >= 1000:
                score += 30
            elif avg_value >= 100:
                score += 20
            else:
                score += 10
        
        recent_txs = [
            tx for tx in transactions 
            if (datetime.now() - tx.timestamp).days <= 30
        ]
        
        if len(recent_txs) >= 10:
            score += 50
        elif len(recent_txs) >= 5:
            score += 30
        elif len(recent_txs) >= 1:
            score += 10
        
        return min(150, score)
    
    def _score_poaps(self, poaps: List[POAP]) -> float:
        """Score based on POAP attendance (max 100 points)"""
        score = 0
        
        if len(poaps) >= 20:
            score += 40
        elif len(poaps) >= 10:
            score += 30
        elif len(poaps) >= 5:
            score += 20
        elif len(poaps) >= 1:
            score += 10
        
        category_weights = {
            "conference": 15,
            "hackathon": 20,
            "educational": 10,
            "community": 5,
            "other": 5
        }
        
        for poap in poaps:
            score += category_weights.get(poap.category, 5)
        
        recent_poaps = [
            poap for poap in poaps 
            if (datetime.now() - poap.date).days <= 180
        ]
        
        if len(recent_poaps) >= 3:
            score += 20
        elif len(recent_poaps) >= 1:
            score += 10
        
        return min(100, score)
    
    def _score_ens(self, ens_names: List[str]) -> float:
        """Score based on ENS ownership (max 50 points)"""
        if len(ens_names) == 0:
            return 0
        
        score = 30
        
        if len(ens_names) > 1:
            score += min(20, (len(ens_names) - 1) * 10)
        
        return min(50, score)
    
    def _score_defi(self, positions: List[DeFiPosition]) -> float:
        """Score based on DeFi participation (max 100 points)"""
        score = 0
        
        if len(positions) >= 10:
            score += 40
        elif len(positions) >= 5:
            score += 30
        elif len(positions) >= 3:
            score += 20
        elif len(positions) >= 1:
            score += 10
        
        total_defi_value = sum(pos.value_usd for pos in positions)
        
        if total_defi_value >= 50000:
            score += 40
        elif total_defi_value >= 10000:
            score += 30
        elif total_defi_value >= 5000:
            score += 20
        elif total_defi_value >= 1000:
            score += 10
        
        unique_protocols = len(set(pos.protocol for pos in positions))
        score += min(20, unique_protocols * 5)
        
        return min(100, score)
    
    def _score_rwas(self, rwas: List[RWA]) -> float:
        """Score based on RWA holdings (max 50 points)"""
        if len(rwas) == 0:
            return 0
        
        score = 20
        
        total_rwa_value = sum(rwa.value_usd for rwa in rwas)
        
        if total_rwa_value >= 10000:
            score += 30
        elif total_rwa_value >= 5000:
            score += 20
        elif total_rwa_value >= 1000:
            score += 10
        
        return min(50, score)
    
    def _calculate_risk_penalty(self, scam_interactions: Set[str], mixer_usage: bool) -> float:
        """Calculate penalty for risky behavior"""
        penalty = 0
        
        if len(scam_interactions) > 0:
            penalty += 100 * len(scam_interactions)
        
        if mixer_usage:
            penalty += 50
        
        return penalty
    
    def _get_risk_level(self, score: int) -> str:
        """Determine risk level based on score"""
        if score >= 750:
            return "low"
        elif score >= 650:
            return "medium"
        elif score >= 550:
            return "high"
        else:
            return "very_high"