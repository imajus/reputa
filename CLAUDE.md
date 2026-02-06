<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reputa - DeFi reputation migration system bridging EVM transaction history to Sui blockchain via TEE oracle with AI-powered creditworthiness scoring.

**User Flow:** EVM Address Input → Questionnaire → AI Scoring (Oracle) → Score Review → Sui Wallet Connect → On-Chain Recording

**Components:**
- `frontend/` - React/TypeScript app (Vite, shadcn/ui)
- `oracle/` - TEE oracle with Move contracts + Node.js enclave + Ollama AI

**Enhanced Scoring:**
The oracle analyzes both on-chain activity (via n8n webhook) and user questionnaire responses using Ollama LLM to generate:
- **Total reputation score** (0-1000): Signed and stored on Sui blockchain
- **5-dimension breakdown** (each 0-100): Unsigned metadata for frontend display
  - Transaction Activity - engagement frequency and volume
  - Account Maturity - age and consistency
  - Protocol & Token Diversity - DeFi sophistication
  - Financial Health - liquidation risk and borrow behavior
  - Intent Alignment - coherence between questionnaire and on-chain activity

Each subdirectory has its own `CLAUDE.md` with detailed architecture and commands.

## Quick Commands

### Initial Setup

```bash
git clone <repository-url>
cd reputa

# Install all dependencies
cd frontend && npm install && cd ..
cd oracle/app && npm install && cd ../..
```

### Environment Configuration

**Oracle deployment requires:**
- `PRIVATE_KEY` - Sui wallet private key for contract deployment
- `DOCKER_REGISTRY` - DockerHub username for image push

Add to shell profile or use:

```bash
export PRIVATE_KEY="your_sui_private_key"
export DOCKER_REGISTRY="your_dockerhub_username"
```

### Development Workflow

```bash
# Frontend
cd frontend && npm run dev       # Dev server on http://[::]:8080

# Oracle - Smart Contracts
cd oracle/contracts && sui move build

# Oracle - Full Deployment
cd oracle && ./deploy.sh         # Requires PRIVATE_KEY and DOCKER_REGISTRY env vars
```

### End-to-End Testing

```bash
# 1. Start frontend
cd frontend && npm run dev

# 2. Test oracle API (if deployed)
source oracle/deployment.env
curl "http://${PUBLIC_IP}:3000/score?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba"

# 3. Frontend connects to oracle at http://${PUBLIC_IP}:3000
```

## Integration Architecture

**Data Flow:**

```
Frontend → POST /score (address + questionnaire) → Oracle API
                                                        ↓
                                            n8n Webhook (rich EVM analytics)
                                                        ↓
                            extractWalletFeatures() + formatQuestionnaireForAI()
                                                        ↓
                            Ollama AI Scoring (total + 5-dimension breakdown)
                                                        ↓
                                Sign score with TEE secp256k1 Key
                                                        ↓
                        Return {score, signature, metadata {scoreBreakdown}}
                                                        ↓
Display Score Review → Connect Sui Wallet → Call update_wallet_score(score, signature) → Verify & Store
```