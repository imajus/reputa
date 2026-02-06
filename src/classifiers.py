# classifiers.py
from typing import Dict, List, Any
from src.config import Settings

settings = Settings()
POAP_CONTRACT = settings.POAP_CONTRACT.lower()
ENS_NAMEWRAPPER = settings.ENS_NAMEWRAPPER.lower()

def is_poap(nft: Dict) -> bool:
    contract_addr = nft.get("contract", {}).get("address", "").lower()
    if contract_addr == POAP_CONTRACT:
        return True
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
    name = nft.get("name") or ""
    return contract_addr == ENS_NAMEWRAPPER or name.endswith(".eth")

def strip_data_image(nft: Dict) -> None:
    """
    If an NFT image is stored as data:image/... (on-chain base64),
    replace image-related fields with nulls.
    """
    image = nft.get("image")
    if not image:
        return

    for key in ["originalUrl", "cachedUrl", "thumbnailUrl", "pngUrl"]:
        value = image.get(key)
        if isinstance(value, str) and value.startswith("data:image"):
            image[key] = None

    # Optional: also clean raw metadata if present
    raw = nft.get("raw", {})
    metadata = raw.get("metadata", {})
    img = metadata.get("image")
    if isinstance(img, str) and img.startswith("data:image"):
        metadata["image"] = None


def classify_nfts(nfts: List[Dict]) -> Dict[str, Any]:
    poaps = []
    legit_nfts = []
    spam_nfts = []
    ens_domains = []

    for nft in nfts:
        strip_data_image(nft)

        nft["classification"] = {
            "is_poap": is_poap(nft),
            "safelist": safelist_status(nft),
            "is_ens": is_ens(nft)
        }

        if nft["classification"]["is_poap"]:
            poaps.append(nft)
            legit_nfts.append(nft)
        elif nft["classification"]["is_ens"]:
            ens_domains.append(nft)
            legit_nfts.append(nft)
        else:
            legit_nfts.append(nft)

    return {
        "poaps": poaps,
        "legit_nfts": legit_nfts,
        "ens_domains": ens_domains,
        "counts": {
            "total": len(nfts),
            "poaps": len(poaps),
            "legit": len(legit_nfts),
            "spam": len(spam_nfts),
            "ens": len(ens_domains)
        }
    }
