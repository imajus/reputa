## What? Why? Who?

🐡 Reputa -- omni-chain credit scoring with verifiable off-chain logic.

Cooked for ETHGlobal [HackMoney 2026 hackathon](https://ethglobal.com/events/hackmoney2026).

Builders:
- Mark Verhoeven: Research/Presentation
- [Alex Naskidashvili](https://github.com/AlexNaskida): Data Aggregator
- [Denis Perov](https://github.com/imajus): Smart Contracts/Oracle/Scoring Framework

## Problem

DeFi protocols **lack reliable reputation data**, preventing them from offering trustless personalized terms to anonymous users. DeFi users **lose their blockchain activity data** when moving between blockchains. Meanwhile, **current credit scoring is expensive** (high gas fees for on-chain computation) **and limited** (centralized, backward-looking frameworks).

## Solution

A **cross-chain reputation bridge** that:
- Analyzes complete DeFi history from EVM chains
- Generates AI-powered credit scores (0-1000) off-chain in a secure environment
- Records verified scores on Sui blockchain via oracle
- Enables protocols to offer personalized terms based on proven track record

## Innovation

1. **Portable Reputation:** Users carry their hard-earned track record across chains instead of restarting
2. **Predictive AI Scoring:** LLM-based analysis identifies patterns predictive of future behavior, not just historical metrics
3. **Multi-Dimensional Framework**: Evaluates: activity history, account maturity, portfolio diversity, risk behavior, user intent.
4. **Off-Chain Efficiency**: Reduces gas costs, protects privacy, enables complex analysis impossible on-chain
5. **Verifiable Result**: Computation runs in a TEE, producing cryptographic proof of correct execution that can be verified on-chain without repeating the calculation.

## Scoring Framework

- Credit performance (borrow/repay patterns, liquidations)
- Balance sheet health (net asset value, volatility, concentration)
- Risk indicators (capital looping, liquidity buffers)
- Cash flow capacity (debt coverage ratios, stress scenarios)

## How Its Made

**Frontend**: Built with React, Tailwind, Vite, Sui dApp Kit.

**Oracle**:
- **Blockchain:** Sui (score recording, DeFi integration)
- **Smart Contracts:** Sui Move
- **TEE:** Sui Nautilus via Marlin Oyster CVM on AWS Nitro Enclaves
- **Cryptography:** @noble/secp256k1 + @noble/hashes (SHA256)
- **LLM:** Ollama Llama3.2:1b

**Data Aggregator**:
- **Blochchain:** Ethereum/EVM (data source)
- **Framework:** Python + FastAPI + Uvicorn (Python ASGI)
- **APIs:** Alchemy, EtherScan, OpenSea
- **Reputation Signals:** POAPs, ENS, verified/blue-chip NFTs, clean lending history.
- **Risk Signals:**: Tornado Cash, span NFTs, drainer patterns, high portfolio concentration.
- **Protocol Coverage:** Aave V2/V3, Compound V2/V3, Uniswap V2/V3, Curve Finance, Ethena (USDe, deUSD), Lido (stETH).

## Links

- [Project page](https://ethglobal.com/showcase/reputa-wda0t) @ ETHGlobal.
- [Presentation](https://www.canva.com/design/DAHAXlWJGDk/YDdKRy8GO015gLjuMasXDw/edit) @ Canva.
- [Live demo](https://reputa.pages.dev)
