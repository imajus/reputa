# routers.py
from fastapi import APIRouter, HTTPException
from src.models import WalletRequest, AssetTransferParams
from src.services import fetch_all_nfts, fetch_token_balances, fetch_asset_transfers
from src.classifiers import classify_nfts
from src.scoring import calculate_credit_score

api_router = APIRouter()

@api_router.post("/assets/nfts")
async def get_nfts(request: WalletRequest):
    try:
        raw_nfts = fetch_all_nfts(request.wallet_address)
        classified = classify_nfts(raw_nfts)
        return classified
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/assets/tokens")
async def get_tokens(request: WalletRequest):
    try:
        tokens = fetch_token_balances(request.wallet_address)
        return {"tokens": tokens}
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/history/transfers")
async def get_transfers(request: WalletRequest, params: AssetTransferParams = AssetTransferParams()):
    try:
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)
        return {"incoming": incoming, "outgoing": outgoing}
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/aggregate")
async def aggregate_data(request: WalletRequest):
    try:
        nfts = fetch_all_nfts(request.wallet_address)
        classified_nfts = classify_nfts(nfts)
        tokens = fetch_token_balances(request.wallet_address)
        params = AssetTransferParams()
        incoming = fetch_asset_transfers(request.wallet_address, params, is_from=False)
        outgoing = fetch_asset_transfers(request.wallet_address, params, is_from=True)

        aggregated = {
            "wallet": request.wallet_address,
            "nfts": classified_nfts,
            "tokens": tokens,
            "transfers": {"incoming": incoming, "outgoing": outgoing}
        }
        return aggregated
    except Exception as e:
        raise HTTPException(500, str(e))

@api_router.post("/score")
async def get_credit_score(request: WalletRequest):
    try:
        aggregated = await aggregate_data(request)  # Reuse aggregate
        score = calculate_credit_score(aggregated)
        return score
    except Exception as e:
        raise HTTPException(500, str(e))