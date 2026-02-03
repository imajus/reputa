import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.config import Settings

app = FastAPI(title="On-Chain Credit Profile API", version="0.2.0")
settings = Settings()

# === HELPERS ===
def is_poap(nft: Dict) -> bool:   
    token_uri = (nft.get("tokenUri") or nft.get("raw", {}).get("tokenUri", "") or "").lower()
    if "poap.tech" in token_uri:
        return True
    tags = nft.get("raw", {}).get("metadata", {}).get("tags", []) or []
    if any("poap" in str(t).lower() for t in tags):
        return True
    return False

def is_spam(nft: Dict) -> bool:
    return nft.get("isSpam", False) or nft.get("contract", {}).get("isSpam", False)

def safelist_status(nft: Dict) -> str:
    osm = nft.get("contract", {}).get("openSeaMetadata", {})
    return osm.get("safelistRequestStatus", "unknown")

def is_ens(nft: Dict) -> bool:
    contract_addr = nft.get("contract", {}).get("address", "").lower()
    return contract_addr == settings.ENS_NAMEWRAPPER.lower() or nft.get("name", "").endswith(".eth")

def classify_nfts(nfts: List[Dict]) -> Dict[str, Any]:
    poaps = []
    legit_nfts = []
    spam_nfts = []
    ens_domains = []

    for nft in nfts:
        nft["classification"] = {
            "is_poap": is_poap(nft),
            "is_spam": is_spam(nft),
            "safelist": safelist_status(nft),
            "is_ens": is_ens(nft)
        }

        if is_spam(nft):
            spam_nfts.append(nft)
        elif is_poap(nft):
            poaps.append(nft)
            legit_nfts.append(nft)  # POAPs count as legit + reputation bonus
        elif is_ens(nft):
            ens_domains.append(nft)
            legit_nfts.append(nft)
        else:
            legit_nfts.append(nft)

    return {
        "all": nfts,
        "poaps": poaps,
        "legit_nfts": legit_nfts,
        "spam_nfts": spam_nfts,
        "ens_domains": ens_domains,
        "counts": {
            "total": len(nfts),
            "poaps": len(poaps),
            "legit": len(legit_nfts),
            "spam": len(spam_nfts),
            "ens": len(ens_domains)
        }
    }

# === FETCHERS (unchanged except added classification) ===
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

# === ENDPOINTS ===
class WalletRequest(BaseModel):
    wallet_address: str

@app.post("/assets/nfts")
async def get_nfts(request: WalletRequest):
    try:
        raw_nfts = fetch_all_nfts(request.wallet_address)
        classified = classify_nfts(raw_nfts)
        return classified
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/aggregate")
async def aggregate(request: WalletRequest):
    # ... (tokens + transfers unchanged) ...
    raw_nfts = fetch_all_nfts(request.wallet_address)
    classified = classify_nfts(raw_nfts)
    # tokens, transfers, etc. (same as before)

    return {
        "wallet": request.wallet_address,
        "nfts": classified,
        # ... other sections ...
        "reputation_signals": {
            "poap_count": classified["counts"]["poaps"],
            "ens_owned": bool(classified["ens_domains"]),
            "has_verified_collections": any(nft["classification"]["safelist"] == "verified" for nft in classified["legit_nfts"])
        }
    }

# === SCORING FRAMEWORK (ready to implement next) ===
def calculate_credit_score(data: Dict) -> dict:
    poap_bonus = data["nfts"]["counts"]["poaps"] * 120      # huge legitimacy boost
    ens_bonus = 80 if data["nfts"]["ens_domains"] else 0
    verified_collections = sum(1 for nft in data["nfts"]["legit_nfts"]
                               if nft["classification"]["safelist"] == "verified")
    verified_bonus = verified_collections * 40

    # TODO: add token value, tx age, etc.
    score = poap_bonus + ens_bonus + verified_bonus + 100  # base
    return {
        "score": min(max(score, 0), 1000),
        "breakdown": {
            "poaps": poap_bonus,
            "ens": ens_bonus,
            "verified_collections": verified_bonus,
            "flags": [nft["classification"] for nft in data["nfts"]["all"][:5]]  # example
        }
    }