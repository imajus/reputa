"""
REST API for Credit Scoring
Converted from GraphQL implementation
"""

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from typing import Optional, List
from datetime import datetime

from src.config import settings
from src.credit_scorer import CreditScorer
from src.data_aggregator import DataAggregator


# ============================================================================
# RESPONSE MODELS - Pydantic schemas for REST responses
# ============================================================================

class TokenResponse(BaseModel):
    """Token information"""
    symbol: str
    balance: float
    value_usd: float
    is_stable: bool


class NFTResponse(BaseModel):
    """NFT information"""
    collection: str
    value_usd: float


class POAPResponse(BaseModel):
    """POAP (Proof of Attendance Protocol) information"""
    event_name: str
    date: datetime
    category: str


class RWAResponse(BaseModel):
    """Real World Asset information"""
    asset_type: str
    value_usd: float
    protocol: str


class TransactionResponse(BaseModel):
    """Transaction information"""
    timestamp: datetime
    value_usd: float
    gas_paid_usd: float
    to_address: Optional[str] = None


class DeFiPositionResponse(BaseModel):
    """DeFi position information"""
    protocol: str
    value_usd: float
    is_borrowed: bool


class WalletAssetsResponse(BaseModel):
    """Complete wallet assets listing"""
    address: str
    
    # Token holdings
    tokens: List[TokenResponse]
    total_token_value: float
    
    # NFT holdings
    nfts: List[NFTResponse]
    total_nft_value: float
    
    # POAPs
    poaps: List[POAPResponse]
    poap_count: int
    
    # RWAs
    rwas: List[RWAResponse]
    total_rwa_value: float
    
    # DeFi positions
    defi_positions: List[DeFiPositionResponse]
    total_defi_value: float
    
    # Recent transactions
    recent_transactions: List[TransactionResponse]
    
    # Summary
    total_value: float
    wallet_age_days: int
    last_updated: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                "tokens": [
                    {"symbol": "USDC", "balance": 5000.0, "value_usd": 5000.0, "is_stable": True},
                    {"symbol": "ETH", "balance": 2.5, "value_usd": 7500.0, "is_stable": False}
                ],
                "total_token_value": 12500.0,
                "nfts": [
                    {"collection": "Bored Apes", "value_usd": 50000.0}
                ],
                "total_nft_value": 50000.0,
                "poaps": [],
                "poap_count": 0,
                "rwas": [],
                "total_rwa_value": 0.0,
                "defi_positions": [],
                "total_defi_value": 0.0,
                "recent_transactions": [],
                "total_value": 62500.0,
                "wallet_age_days": 180,
                "last_updated": "2024-01-15T10:30:00"
            }
        }


class ScoreBreakdownResponse(BaseModel):
    """Detailed score breakdown"""
    total_score: int
    grade: str
    portfolio_score: float
    activity_score: float
    defi_score: float
    risk_score: float
    summary: str


class WalletProfileResponse(BaseModel):
    """Complete wallet profile with credit score"""
    address: str
    credit_score: int
    grade: str
    breakdown: ScoreBreakdownResponse
    
    # Asset summary
    total_value: float
    token_count: int
    nft_count: int
    
    # Activity summary
    wallet_age_days: int
    transaction_count: int
    
    # Metadata
    last_updated: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                "credit_score": 750,
                "grade": "A",
                "breakdown": {
                    "total_score": 750,
                    "grade": "A",
                    "portfolio_score": 85.0,
                    "activity_score": 75.0,
                    "defi_score": 65.0,
                    "risk_score": 90.0,
                    "summary": "Strong portfolio with consistent activity"
                },
                "total_value": 62500.0,
                "token_count": 2,
                "nft_count": 1,
                "wallet_age_days": 180,
                "transaction_count": 50,
                "last_updated": "2024-01-15T10:30:00"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str


# ============================================================================
# DATA SERVICE - Business Logic (same as GraphQL version)
# ============================================================================

class ScoringService:
    """Handles data fetching and scoring"""
    
    def __init__(self, alchemy_key: Optional[str] = None):
        self.aggregator = DataAggregator(alchemy_key)
        self.scorer = CreditScorer()
    
    async def get_wallet_profile(self, address: str) -> WalletProfileResponse:
        """Get complete wallet profile with credit score"""
        
        # Fetch on-chain data
        wallet_data = await self.aggregator.get_wallet_data(address)
        
        # Calculate credit score
        score = self.scorer.calculate_score(wallet_data)
        
        # Calculate summary stats
        total_value = (
            sum(t.value_usd for t in wallet_data.tokens) +
            sum(n.value_usd for n in wallet_data.nfts)
        )
        
        return WalletProfileResponse(
            address=address,
            credit_score=score.total_score,
            grade=score.grade,
            breakdown=ScoreBreakdownResponse(
                total_score=score.total_score,
                grade=score.grade,
                portfolio_score=score.portfolio_score,
                activity_score=score.activity_score,
                defi_score=score.defi_score,
                risk_score=score.risk_score,
                summary=score.summary
            ),
            total_value=total_value,
            token_count=len(wallet_data.tokens),
            nft_count=len(wallet_data.nfts),
            wallet_age_days=wallet_data.wallet_age_days,
            transaction_count=len(wallet_data.transactions),
            last_updated=datetime.now()
        )
    
    async def get_score_breakdown(self, address: str) -> ScoreBreakdownResponse:
        """Get just the score breakdown (lighter query)"""
        profile = await self.get_wallet_profile(address)
        return profile.breakdown
    
    async def get_wallet_assets(self, address: str) -> WalletAssetsResponse:
        """Get complete wallet assets listing"""
        
        # Fetch on-chain data
        wallet_data = await self.aggregator.get_wallet_data(address)
        
        # Convert to response models
        tokens = [
            TokenResponse(
                symbol=t.symbol,
                balance=t.balance,
                value_usd=t.value_usd,
                is_stable=t.is_stable
            )
            for t in wallet_data.tokens
        ]
        
        nfts = [
            NFTResponse(
                collection=n.collection,
                value_usd=n.value_usd
            )
            for n in wallet_data.nfts
        ]
        
        poaps = [
            POAPResponse(
                event_name=p.event_name,
                date=p.date,
                category=p.category
            )
            for p in wallet_data.poaps
        ]
        
        rwas = [
            RWAResponse(
                asset_type=r.asset_type,
                value_usd=r.value_usd,
                protocol=r.protocol
            )
            for r in wallet_data.rwas
        ]
        
        defi_positions = [
            DeFiPositionResponse(
                protocol=d.protocol,
                value_usd=d.value_usd,
                is_borrowed=d.is_borrowed
            )
            for d in wallet_data.defi_positions
        ]
        
        # Get recent transactions (last 10)
        recent_txs = [
            TransactionResponse(
                timestamp=tx.timestamp,
                value_usd=tx.value_usd,
                gas_paid_usd=tx.gas_paid_usd,
                to_address=tx.to_address
            )
            for tx in wallet_data.transactions[:10]
        ]
        
        # Calculate totals
        total_token_value = sum(t.value_usd for t in wallet_data.tokens)
        total_nft_value = sum(n.value_usd for n in wallet_data.nfts)
        total_rwa_value = sum(r.value_usd for r in wallet_data.rwas)
        total_defi_value = sum(d.value_usd for d in wallet_data.defi_positions)
        total_value = total_token_value + total_nft_value + total_rwa_value + total_defi_value
        
        return WalletAssetsResponse(
            address=address,
            tokens=tokens,
            total_token_value=total_token_value,
            nfts=nfts,
            total_nft_value=total_nft_value,
            poaps=poaps,
            poap_count=len(poaps),
            rwas=rwas,
            total_rwa_value=total_rwa_value,
            defi_positions=defi_positions,
            total_defi_value=total_defi_value,
            recent_transactions=recent_txs,
            total_value=total_value,
            wallet_age_days=wallet_data.wallet_age_days,
            last_updated=datetime.now()
        )


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="On-Chain Credit Scoring API",
    description="Calculate credit scores from blockchain data - REST API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
service = ScoringService(
    alchemy_key=settings.ALCHEMY_API_KEY,
)


# ============================================================================
# REST ENDPOINTS
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """API root - welcome message"""
    return {
        "message": "On-Chain Credit Scoring API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "wallet_score": "/wallets/{address}/score",
            "score_breakdown": "/wallets/{address}/breakdown",
            "wallet_assets": "/wallets/{address}/assets"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0"
    )


@app.get(
    "/wallets/{address}/score",
    response_model=WalletProfileResponse,
    responses={
        200: {"description": "Wallet profile with credit score"},
        400: {"model": ErrorResponse, "description": "Invalid wallet address"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get wallet credit score",
    description="Retrieve complete wallet profile including credit score, breakdown, and asset summary"
)
async def get_wallet_score(
    address: str = Path(
        ...,
        description="Ethereum wallet address (0x...)",
        example="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    )
):
    """
    Get complete wallet credit score and profile.
    
    This endpoint analyzes on-chain data including:
    - Token holdings
    - NFT collections
    - Transaction history
    - DeFi positions
    - Wallet age and activity
    
    Returns a comprehensive credit score (300-850) with detailed breakdown.
    """
    try:
        # Validate address format
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format. Must be 42 characters starting with 0x"
            )
        
        profile = await service.get_wallet_profile(address)
        return profile
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching wallet data: {str(e)}"
        )


@app.get(
    "/wallets/{address}/breakdown",
    response_model=ScoreBreakdownResponse,
    responses={
        200: {"description": "Score breakdown details"},
        400: {"model": ErrorResponse, "description": "Invalid wallet address"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get score breakdown only",
    description="Retrieve just the credit score breakdown (lighter query than full profile)"
)
async def get_score_breakdown(
    address: str = Path(
        ...,
        description="Ethereum wallet address (0x...)",
        example="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    )
):
    """
    Get just the score breakdown without full profile data.
    
    This is a lighter endpoint that returns only:
    - Total credit score
    - Grade (AAA to F)
    - Component scores (portfolio, activity, DeFi, risk)
    - Summary explanation
    
    Use this when you don't need the full asset list and transaction details.
    """
    try:
        # Validate address format
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format. Must be 42 characters starting with 0x"
            )
        
        breakdown = await service.get_score_breakdown(address)
        return breakdown
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating score: {str(e)}"
        )


@app.get(
    "/wallets/{address}/assets",
    response_model=WalletAssetsResponse,
    responses={
        200: {"description": "Complete wallet assets listing"},
        400: {"model": ErrorResponse, "description": "Invalid wallet address"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get wallet assets",
    description="Retrieve complete listing of all wallet assets including tokens, NFTs, POAPs, RWAs, and DeFi positions"
)
async def get_wallet_assets(
    address: str = Path(
        ...,
        description="Ethereum wallet address (0x...)",
        example="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    )
):
    """
    Get complete wallet assets listing.
    
    This endpoint provides detailed information about all assets:
    - **Tokens**: ERC20 token balances with USD values
    - **NFTs**: NFT collections and estimated values
    - **POAPs**: Proof of Attendance Protocol badges
    - **RWAs**: Real World Assets (tokenized real estate, bonds, etc.)
    - **DeFi Positions**: Active positions in DeFi protocols
    - **Recent Transactions**: Last 10 transactions
    
    Returns comprehensive asset breakdown with totals for each category.
    """
    try:
        # Validate address format
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format. Must be 42 characters starting with 0x"
            )
        
        assets = await service.get_wallet_assets(address)
        return assets
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching wallet assets: {str(e)}"
        )


# Alternative simpler endpoint (backward compatible)
@app.get(
    "/score/{address}",
    response_model=WalletProfileResponse,
    deprecated=True,
    summary="Get wallet score (deprecated)",
    description="Legacy endpoint. Use /wallets/{address}/score instead"
)
async def get_score_legacy(address: str):
    """Legacy endpoint for backward compatibility"""
    return await get_wallet_score(address)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "detail": "The requested endpoint does not exist",
        "available_endpoints": {
            "wallet_score": "/wallets/{address}/score",
            "score_breakdown": "/wallets/{address}/breakdown",
            "wallet_assets": "/wallets/{address}/assets",
            "health": "/health",
            "docs": "/docs"
        }
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":    
    print("\n" + "="*60)
    print("🚀 Credit Scoring REST API Server")
    print("="*60)
    print("\n📊 Main Endpoints:")
    print("   GET  /wallets/{address}/score      - Full wallet profile")
    print("   GET  /wallets/{address}/breakdown  - Score breakdown only")
    print("   GET  /wallets/{address}/assets     - All assets listing")
    print("\n📖 Documentation:")
    print("   Interactive API Docs: http://localhost:8000/docs")
    print("   ReDoc: http://localhost:8000/redoc")
    print("\n🔍 Example:")
    print("   http://localhost:8000/wallets/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0/score")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
