# Design: AI-Powered Reputation Scoring in TEE

## System Architecture

### Container Orchestration

**Service Dependency Graph:**
```
evm-score-oracle (depends on ollama_model healthy)
       ↓
ollama_model (depends on ollama_server healthy)
       ↓
ollama_server (base service)
```

**Health Check Strategy:**
- `ollama_server`: Validates `ollama --version` every 10s, 30s start period
- `ollama_model`: Checks `ollama list | grep llama3.2:1b` every 15s, 3min start period (accounts for pull time)
- `evm-score-oracle`: Waits for ollama_model before starting

**Network Configuration:**
- All services use `network_mode: host` (Oyster CVM requirement)
- Inter-service communication via localhost
- Ollama API: `http://127.0.0.1:11434`
- Express API: `http://127.0.0.1:3000`

### AI Scoring Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│ /score?address=0x... Request                                  │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 1. Fetch EVM Data (n8n API)                                   │
│    - GET https://n8n.majus.org/webhook/.../address={ADDRESS}  │
│    - Response: {EVM: {Events: [...]}}                         │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. Extract Features (Deterministic)                           │
│    - totalTransactions: events.length                         │
│    - accountAgeDays: (now - min(timestamps)) / 86400000       │
│    - recentActivity: {day, week, month} counts                │
│    - uniqueContracts: Set(events.map(e => e.Log.Address))     │
│    - protocolsUsed: Detect Uniswap, Aave, etc. by address     │
│    - valueStats: {total, average} from Transaction.Value      │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. Build AI Prompt (Structured)                               │
│    - Template with 5 scoring criteria                         │
│    - JSON schema: {score, reasoning, risk_factors, strengths} │
│    - Temperature: 0.3 (low variance)                          │
│    - Max tokens: 500 (latency control)                        │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. Call Ollama API                                             │
│    - POST http://127.0.0.1:11434/api/generate                 │
│    - model: llama3.2:1b, format: json                         │
│    - Timeout: Inherited from axios (10s default)              │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. Parse & Validate Response                                  │
│    - JSON.parse(response.response)                            │
│    - Clamp score: Math.max(0, Math.min(1000, score))          │
│    - Fallback on error: transactions * 10                     │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. Sign Score (Unchanged)                                     │
│    - BCS serialize: IntentMessage<ScoreUpdatePayload>         │
│    - SHA256 hash                                               │
│    - secp256k1 sign with TEE key                              │
└───────────────────┬──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. Return Response                                             │
│    {                                                           │
│      score,                                                    │
│      wallet_address,                                           │
│      timestamp_ms,                                             │
│      signature,  // <-- Signed fields (backward compatible)   │
│      metadata: {  // <-- New, optional                        │
│        reasoning,                                              │
│        risk_factors,                                           │
│        strengths,                                              │
│        features                                                │
│      }                                                         │
│    }                                                           │
└──────────────────────────────────────────────────────────────┘
```

## Scoring Algorithm

### Multi-Factor Analysis

The AI evaluates 5 dimensions with point allocations:

1. **Transaction Volume (0-250 points)**
   - Raw count of historical transactions
   - Logarithmic scaling for high-volume accounts

2. **Account Maturity (0-200 points)**
   - Age since first transaction
   - Consistency of activity over time (avoid dormant periods)

3. **Protocol Diversity (0-200 points)**
   - Number of unique contracts interacted with
   - Recognition of major DeFi protocols (Uniswap, Aave, etc.)
   - Bonus for cross-protocol activity

4. **Recent Activity (0-200 points)**
   - Higher weight for transactions in last 24h, 7d, 30d
   - Decay function for older transactions
   - Penalty for long dormancy

5. **Value Transacted (0-150 points)**
   - Total and average transaction values
   - Whale detection (very high values)
   - Retail confirmation (consistent moderate values)

**Total Score:** 0-1000 (sum of all dimensions)

### Feature Extraction Logic

**Temporal Analysis:**
```javascript
const timestamps = events.map(e => parseInt(e.Block?.Timestamp || 0) * 1000);
const now = Date.now();
const accountAge = (now - Math.min(...timestamps)) / ONE_DAY;
const recentDay = timestamps.filter(t => now - t < ONE_DAY).length;
const recentWeek = timestamps.filter(t => now - t < ONE_WEEK).length;
const recentMonth = timestamps.filter(t => now - t < ONE_MONTH).length;
```

**Diversity Detection:**
```javascript
const uniqueContracts = new Set(
  events.map(e => e.Log?.Address).filter(Boolean)
).size;

const protocols = new Set();
events.forEach(e => {
  const addr = e.Log?.Address?.toLowerCase();
  if (addr?.startsWith('0xa0b8')) protocols.add('Uniswap');
  if (addr?.startsWith('0x7a25')) protocols.add('Aave');
  // ... additional protocol detection
});
```

**Value Aggregation:**
```javascript
const values = events
  .map(e => parseFloat(e.Transaction?.Value || 0))
  .filter(v => v > 0);
const totalValue = values.reduce((sum, v) => sum + v, 0);
const avgValue = values.length > 0 ? totalValue / values.length : 0;
```

### Prompt Engineering

**Key Design Principles:**
1. **Explicit Criteria:** Enumerate 5 scoring dimensions with point ranges
2. **Structured Output:** Enforce JSON schema with `format: 'json'`
3. **Example-Free:** No few-shot examples (model is instruction-tuned)
4. **Constraint Explicit:** "Output Format (JSON):" section before closing
5. **Temperature Control:** 0.3 balances consistency with nuance

**Prompt Template:**
```
You are a DeFi reputation analyzer. Analyze this Ethereum wallet activity and provide a reputation score.

Wallet: {address}

Activity Summary:
- Total Transactions: {totalTransactions}
- Account Age: {accountAgeDays} days
- Recent Activity: {day} (24h), {week} (7d), {month} (30d)
- Unique Contracts Interacted: {uniqueContracts}
- DeFi Protocols Used: {protocols}
- Transaction Value: Total={total} ETH, Avg={avg} ETH

Scoring Criteria:
1. Transaction Volume (0-250 points): More transactions indicate higher engagement
2. Account Maturity (0-200 points): Older accounts with consistent activity score higher
3. Protocol Diversity (0-200 points): Interaction with multiple DeFi protocols shows sophistication
4. Recent Activity (0-200 points): Recent engagement indicates active participation
5. Value Transacted (0-150 points): Higher value transactions (within normal ranges) show trust

Output Format (JSON):
{
  "score": <integer 0-1000>,
  "reasoning": "<2-3 sentence explanation>",
  "risk_factors": ["<factor1>", "<factor2>"],
  "strengths": ["<strength1>", "<strength2>"]
}

Analyze and respond with JSON only.
```

### Fallback Strategy

**Trigger Conditions:**
- Ollama API unreachable (network error)
- JSON parsing fails
- Response timeout (>10s)
- Invalid score value (NaN, negative, >1000)

**Fallback Calculation:**
```javascript
score = Math.min(1000, features.totalTransactions * 10);
reasoning = 'Fallback: Simple transaction count';
riskFactors = ['AI scoring unavailable'];
strengths = [];
```

**Logging:**
```javascript
console.error('AI scoring failed, falling back to simple count:', error);
```

Frontend receives same response structure, but with minimal metadata.

## Deployment Considerations

### Resource Constraints

**Oyster CVM c6a.xlarge:**
- 4 vCPU
- 8GB RAM
- No persistent storage

**Memory Budget:**
- Ollama server: ~500MB
- llama3.2:1b model: ~1.3GB
- Node.js heap: ~512MB
- System overhead: ~1GB
- **Total:** ~3.3GB (41% of 8GB - safe margin)

### Startup Sequence

1. **ollama_server starts** → Health check passes in ~5s
2. **ollama_model pulls llama3.2:1b** → Takes 90-180s depending on network
3. **ollama_model health check** → Verifies model loaded
4. **evm-score-oracle starts** → Express server + Ollama client
5. **deploy.sh health check** → Waits for `"ollama":"connected"` response

**Total Cold Start:** 3-5 minutes

### Performance Expectations

**Request Latency Breakdown:**
- n8n API fetch: 1-3s
- Feature extraction: <100ms (deterministic, in-memory)
- AI inference: 3-8s (depends on feature complexity, model load)
- Signature generation: <50ms
- **Total:** 5-12s per request

**Throughput:**
- Single request processing (no concurrency in scoring logic)
- Ollama can handle concurrent requests, but we serialize for determinism
- ~5-10 requests/minute sustainable

## Error Handling

### Ollama Connection Failures

**Detection:**
```javascript
try {
  await ollamaClient.list();
  health.ollama = 'connected';
} catch (error) {
  health.ollama = 'unavailable';
  health.status = 'degraded';
}
```

**Response:**
- `/health` endpoint returns `{status: 'degraded', ollama: 'unavailable'}`
- `/score` falls back to simple counting
- No hard failure - service remains available

### AI Response Malformation

**Validation:**
```javascript
const analysis = JSON.parse(response.response);
const score = Math.max(0, Math.min(1000, parseInt(analysis.score || 0)));

if (isNaN(score)) {
  throw new Error('Invalid score from AI');
}
```

**Recovery:**
- Catch block triggers fallback scoring
- Error logged with original AI response for debugging
- Client receives valid response (never fails)

### Model Loading Timeout

**Prevention:**
- Health check `start_period: 3m` allows full model pull time
- `retries: 20` with `interval: 15s` = 5 minutes total wait
- deploy.sh waits for health before PCR registration

**Detection:**
```bash
if [ $OLLAMA_RETRY_COUNT -eq $MAX_OLLAMA_RETRIES ]; then
  echo "Warning: Ollama health check timeout"
  # Continue anyway - service may still work
fi
```

## Security Considerations

### TEE Isolation Preserved

- All computation (feature extraction, AI inference) inside enclave
- No external API calls beyond existing n8n webhook
- Ollama runs on localhost within TEE boundary
- PCR attestation validates entire image (including Ollama)

### Signature Integrity

- BCS serialization unchanged
- Only `score`, `wallet_address`, `timestamp_ms` are signed
- Metadata NOT signed (informational only)
- Move contract verification logic untouched

### Determinism Considerations

**Deterministic Components:**
- Feature extraction (pure functions)
- Score bounds clamping
- BCS serialization
- Cryptographic signing

**Non-Deterministic Component:**
- AI inference (temperature 0.3, not 0.0)
- Reasoning text varies between runs

**Impact:** Same address may get slightly different reasoning text, but score should be stable (±5% variance expected at temperature 0.3).

**Mitigation:** If perfect determinism required in future, set `temperature: 0.0` at cost of less nuanced explanations.

## Testing Strategy

### Local Testing Workflow

1. **Start Ollama locally:**
   ```bash
   docker run -d --name ollama -p 11434:11434 ollama/ollama:0.5.4
   docker exec ollama ollama pull llama3.2:1b
   ```

2. **Run application:**
   ```bash
   cd oracle/app
   npm install
   OLLAMA_HOST=http://localhost:11434 node src/index.js /tmp/test-key.bin
   ```

3. **Test endpoints:**
   ```bash
   curl http://localhost:3000/health | jq
   curl "http://localhost:3000/score?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba" | jq
   ```

4. **Validate response structure:**
   - Verify `metadata.reasoning` is a string
   - Verify `metadata.risk_factors` is an array
   - Verify `metadata.strengths` is an array
   - Verify `score` is 0-1000 integer

### TEE Integration Testing

After `./deploy.sh` completes:

1. **Health check:**
   ```bash
   curl "http://${PUBLIC_IP}:3000/health" | jq
   # Expected: {"status":"ok","ollama":"connected","timestamp":...}
   ```

2. **AI scoring:**
   ```bash
   curl "http://${PUBLIC_IP}:3000/score?address=0x..." | jq .metadata
   # Expected: reasoning, risk_factors, strengths present
   ```

3. **On-chain verification:**
   ```bash
   cd oracle/contracts/script
   bash update_score.sh $PUBLIC_IP $PACKAGE_ID $ORACLE_ID $ENCLAVE_ID 0x...
   bash get_score.sh $PACKAGE_ID $ORACLE_ID
   # Expected: Score matches enclave response, no signature error
   ```

### Performance Validation

**Acceptance Criteria:**
- Cold start completes in <5 minutes
- Request latency <15 seconds (p95)
- Memory usage <6GB (docker stats)
- Health endpoint responds in <1s
- No OOM crashes during 10 consecutive requests

## Trade-offs & Alternatives

### Why llama3.2:1b over Larger Models?

**Considered:**
- llama3.2:3b (~4GB RAM)
- llama3:8b (~8GB RAM)

**Decision: 1b**
- Pros: Fast inference (3-8s), fits comfortably in 8GB with headroom
- Cons: Less sophisticated reasoning than 3b/8b
- Rationale: Performance > marginal quality gain; can upgrade to c6a.2xlarge (16GB) later if needed

### Why Ollama over Custom Python/TensorFlow Model?

**Alternatives:**
- scikit-learn (deterministic ML)
- TensorFlow.js (lightweight)
- External API (OpenAI)

**Decision: Ollama**
- Pros: Self-hosted (TEE compatible), good reasoning quality, easy integration
- Cons: Larger memory footprint than deterministic ML
- Rationale: Interpretability (reasoning text) is critical for user trust; no training data available for supervised ML

### Why No Score Caching?

**Alternative:** Cache scores for 1 hour per address

**Decision: No caching initially**
- Pros of caching: Fast repeat queries, reduced compute
- Cons of caching: TEE has no persistent storage, adds complexity
- Rationale: Premature optimization; add if query patterns show high repeat rate

## Future Enhancements

**Phase 2 (Post-MVP):**
- Frontend UI displaying reasoning/strengths/risks
- Score caching layer (external to TEE, in frontend or API gateway)
- Metrics endpoint (`/metrics`) for observability

**Phase 3 (Advanced):**
- Fine-tuned model on labeled DeFi reputation dataset
- Multi-step reasoning (reflection pass for high-stakes scores)
- Comparative scoring (percentile within peer cohort)

**Phase 4 (Multi-Chain):**
- Extend to Polygon, Arbitrum, Base
- Cross-chain reputation aggregation
- Weighted multi-chain scoring formula
