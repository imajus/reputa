# Proposal: Integrate AI Scoring with Ollama in TEE Enclave

## Problem Statement

The current oracle scoring system uses a simple transaction count (`EVM.Events.length`) as the reputation score. This approach:
- Lacks sophistication: All transactions weighted equally regardless of recency, value, or protocol
- Misses behavioral patterns: No analysis of DeFi engagement, risk factors, or activity consistency
- Provides no context: Users see only a number with no explanation of how it was calculated

## Proposed Solution

Deploy Ollama LLM (llama3.2:1b) within the TEE enclave to enable AI-powered reputation scoring that analyzes:
- **Temporal patterns**: Recent activity vs historical consistency
- **Protocol diversity**: Interaction with multiple DeFi protocols (Uniswap, Aave, etc.)
- **Risk indicators**: Dormant accounts, unusual spikes, value patterns
- **Contextual weighting**: More recent transactions carry higher weight

All AI inference runs inside the trusted execution environment, preserving cryptographic guarantees while adding interpretability through reasoning metadata.

## User Impact

**Frontend Users:**
- See AI-generated reasoning explaining their score
- Understand specific strengths (e.g., "High protocol diversity")
- Identify risk factors (e.g., "Low recent activity")
- View detailed transaction features (account age, unique contracts, protocols used)

**Developers:**
- API response backward compatible (adds optional `metadata` field)
- Same BCS signature format - no Move contract changes required
- Enhanced `/health` endpoint reports Ollama connectivity status

## Technical Approach

### Architecture Changes

**Current (Single Container):**
```
evm-score-oracle
  ├─ Express API (:3000)
  ├─ Fetch n8n EVM data
  ├─ Calculate score (tx count)
  └─ Sign with TEE key
```

**Proposed (Multi-Container TEE):**
```
┌─────────────────────────────────────────┐
│         Oyster CVM (TEE Enclave)        │
├─────────────────────────────────────────┤
│  evm-score-oracle  →  ollama_server     │
│  (Express :3000)      (API :11434)      │
│         ↓                   ↓            │
│  Feature Extraction   llama3.2:1b       │
│         ↓                   ↓            │
│  AI Prompt Builder → Ollama Inference   │
│         ↓                                │
│  Score + Reasoning                       │
│         ↓                                │
│  Sign with TEE key (unchanged)          │
└─────────────────────────────────────────┘
```

### Key Design Decisions

1. **Model Selection: llama3.2:1b**
   - Size: ~1.3GB (fits in 8GB RAM with 6.7GB headroom)
   - Inference: 3-8s on 4 vCPU (acceptable latency)
   - Capability: Adequate for structured scoring with low temperature

2. **No Persistent Volumes**
   - TEE enclave does not support restarts
   - Model pulled fresh on each deployment (~2-3 min startup time)
   - Acceptable for 60-minute Oyster CVM job duration

3. **Structured JSON Output**
   - Temperature 0.3 for consistency
   - Schema: `{score: 0-1000, reasoning, risk_factors, strengths}`
   - Token limit: 500 to control latency

4. **Fallback Mechanism**
   - If Ollama unavailable: `score = min(1000, transactions * 10)`
   - Graceful degradation preserves service availability

5. **Backward Compatibility**
   - Response adds `metadata` field (optional, not signed)
   - BCS signature format unchanged
   - Frontend can ignore metadata if not ready

## Scope

### In Scope (This Change)
- Docker compose multi-service configuration (ollama_server, ollama_model)
- AI scoring logic in Node.js enclave application
- Feature extraction from EVM transaction data
- Structured prompting for consistent AI responses
- Enhanced health checks for Ollama readiness
- Deployment script updates for extended startup time
- Local testing without TEE deployment

### Out of Scope (Future Work)
- Frontend UI displaying reasoning/metadata (depends on frontend specs)
- Score caching layer for repeat queries
- Multi-chain support (Polygon, Arbitrum)
- Model fine-tuning on DeFi dataset
- Comparative scoring (peer percentiles)
- On-chain reputation NFT/SBT

## Dependencies

**Required Tools:**
- Docker (existing)
- Ollama npm package (new: `"ollama": "^0.6.0"`)
- Nix build system (existing, needs npmDepsHash update)

**External Services:**
- n8n webhook API (existing)
- Ollama Docker image: `ollama/ollama:0.5.4`
- Model: `llama3.2:1b` from Ollama registry

**Specification Dependencies:**
- None (independent change to oracle backend)
- Frontend oracle-integration spec expects same response format (compatible)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Model loading timeout (>3min) | Deployment fails | Extended health check (3min start_period), validation before PCR registration |
| Memory pressure (>8GB) | Enclave crashes | Use small model (1.3GB), monitor metrics, test locally |
| AI response inconsistency | Variable scores for same input | Low temperature (0.3), structured JSON, deterministic feature extraction |
| Increased latency (10s+) | Poor UX | Token limit (500), show loading state in UI, optimize prompt |
| PCR mismatch after rebuild | Signature verification fails | deploy.sh auto-updates PCRs, test locally before production |

## Success Criteria

**Functional:**
- [ ] AI scoring returns 0-1000 values based on multi-factor analysis
- [ ] Metadata includes reasoning, risk_factors, strengths
- [ ] Fallback to simple scoring if Ollama unavailable
- [ ] Signature validates on Sui blockchain (unchanged format)

**Performance:**
- [ ] Cold start completes within 5 minutes
- [ ] Warm request responds within 15 seconds
- [ ] Memory usage stays under 6GB (75% of limit)
- [ ] Health endpoint reports Ollama connectivity

**Reliability:**
- [ ] Graceful degradation on AI failure
- [ ] Health checks prevent deployment of broken state
- [ ] PCR attestation works with new Docker image
- [ ] End-to-end test passes after deployment

## Open Questions

1. Should we expose AI confidence score in metadata?
2. Do we need metrics endpoint for performance monitoring?
3. Should fallback scoring be logged/alerted?
4. Is 15s response time acceptable for frontend UX?

## Timeline Estimate

Not providing time estimates per project guidelines. Work broken into verifiable tasks with clear acceptance criteria.
