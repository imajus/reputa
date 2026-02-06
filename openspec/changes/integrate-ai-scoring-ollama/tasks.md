# Implementation Tasks: AI Scoring Integration

## Phase 1: Dependencies & Configuration

### Task 1.1: Update package.json with Ollama dependency
**What:** Add ollama npm package to dependencies
**Files:** `oracle/app/package.json`
**Actions:**
- Add `"ollama": "^0.6.0"` to dependencies object
- Update version field to `"0.2.0"`
**Validation:** File parses as valid JSON

### Task 1.2: Install dependencies and update lock file
**What:** Run npm install to generate updated package-lock.json
**Files:** `oracle/app/package-lock.json` (generated)
**Actions:**
- Run `cd oracle/app && npm install`
- Verify ollama package and dependencies installed
**Validation:** `npm install` succeeds without errors, ollama appears in package-lock.json

### Task 1.3: Update Nix build configuration hash
**What:** Update npmDepsHash in build.nix to match new package-lock.json
**Files:** `oracle/app/build.nix`
**Actions:**
- Run `./nix.sh build-node-amd64` (will fail with hash mismatch)
- Copy correct hash from error message
- Update `npmDepsHash` value in build.nix
- Re-run build to verify
**Validation:** Nix build completes successfully, generates node-amd64-image.tar.gz

## Phase 2: Docker Orchestration

### Task 2.1: Create multi-service docker-compose.yml
**What:** Transform single-service compose file to multi-service orchestration
**Files:** `oracle/app/docker-compose.yml`
**Actions:**
- Add `ollama_server` service with ollama/ollama:0.5.4 image
- Add `ollama_model` service with pull llama3.2:1b command
- Update `evm-score-oracle` service to depend on ollama_model
- Add OLLAMA_HOST environment variable to evm-score-oracle
- Configure health checks for all services
**Validation:** `docker-compose config` parses successfully, shows 3 services

### Task 2.2: Configure service health checks
**What:** Add health check definitions with appropriate timing
**Files:** `oracle/app/docker-compose.yml` (continued from 2.1)
**Actions:**
- ollama_server: health check "ollama --version", interval 10s, start_period 30s
- ollama_model: health check "ollama list | grep llama3.2:1b", interval 15s, start_period 3m
- Define service dependencies with condition: service_healthy
**Validation:** Health check commands are valid shell syntax

### Task 2.3: Update deployment script health checks
**What:** Extend deploy.sh to wait for Ollama readiness
**Files:** `oracle/deploy.sh`
**Actions:**
- Add Ollama health check loop after line 230 (after basic health check)
- Poll `/health` endpoint for `"ollama":"connected"` status
- Retry up to 30 times at 10 second intervals (5 minutes total)
- Log warning if timeout but allow continuation
**Validation:** Script syntax valid (`bash -n deploy.sh`), health check logic present

## Phase 3: Feature Extraction

### Task 3.1: Implement extractTransactionFeatures function
**What:** Create function to extract DeFi metrics from EVM data
**Files:** `oracle/app/src/index.js`
**Actions:**
- Add extractTransactionFeatures function before fetchTransactionCount
- Implement temporal analysis (accountAgeDays, recentActivity)
- Implement diversity analysis (uniqueContracts, protocolsUsed)
- Implement value analysis (totalValue, avgValue)
- Return complete features object
**Validation:** Function returns object with all required fields (totalTransactions, accountAgeDays, recentActivity, uniqueContracts, protocolsUsed, valueStats)

### Task 3.2: Add protocol detection logic
**What:** Detect DeFi protocols by contract address patterns
**Files:** `oracle/app/src/index.js` (within extractTransactionFeatures)
**Actions:**
- Check if Log.Address starts with 0xa0b8 → add 'Uniswap'
- Check if Log.Address starts with 0x7a25 → add 'Aave'
- Check if Log.Address starts with 0x1f98 → add 'Uniswap V3'
- Return protocols as array
**Validation:** Protocol detection identifies known addresses correctly

## Phase 4: AI Scoring Engine

### Task 4.1: Initialize Ollama client
**What:** Import and configure Ollama client
**Files:** `oracle/app/src/index.js`
**Actions:**
- Add `import { Ollama } from 'ollama';` at top of file
- Create ollamaClient after httpClient initialization
- Read host from `process.env.OLLAMA_HOST || 'http://127.0.0.1:11434'`
**Validation:** Import statement present, client initialized with host configuration

### Task 4.2: Implement generateAIScore function
**What:** Create AI scoring function with Ollama integration
**Files:** `oracle/app/src/index.js`
**Actions:**
- Add generateAIScore function accepting address and evmData
- Call extractTransactionFeatures
- Build structured prompt with 5 scoring criteria
- Call ollamaClient.generate with model llama3.2:1b, format 'json', temperature 0.3, num_predict 500
- Parse JSON response
- Clamp score to 0-1000
- Return {score, reasoning, riskFactors, strengths, features}
**Validation:** Function returns object with all required fields

### Task 4.3: Add AI scoring fallback logic
**What:** Implement fallback scoring when Ollama fails
**Files:** `oracle/app/src/index.js` (within generateAIScore)
**Actions:**
- Wrap Ollama call in try-catch
- On error: log to console
- Calculate fallback score as `min(1000, totalTransactions * 10)`
- Set reasoning to 'Fallback: Simple transaction count'
- Set riskFactors to ['AI scoring unavailable']
- Set strengths to empty array
**Validation:** Fallback path returns valid response structure

### Task 4.4: Create structured AI prompt template
**What:** Design prompt with explicit criteria and JSON schema
**Files:** `oracle/app/src/index.js` (within generateAIScore)
**Actions:**
- Include wallet address and feature summary
- Enumerate 5 scoring dimensions with point allocations
- Specify JSON output format with schema
- Request reasoning, risk_factors, strengths fields
**Validation:** Prompt includes all required elements (criteria, schema, fields)

## Phase 5: API Endpoint Updates

### Task 5.1: Rename fetchTransactionCount to fetchEVMData
**What:** Modify function to return full EVM response instead of count
**Files:** `oracle/app/src/index.js`
**Actions:**
- Rename function from fetchTransactionCount to fetchEVMData
- Change return statement from `response.data.EVM.Events.length` to `response.data`
- Update function comment
**Validation:** Function returns full data object with EVM.Events

### Task 5.2: Update /score endpoint to use AI scoring
**What:** Replace simple count with generateAIScore call
**Files:** `oracle/app/src/index.js`
**Actions:**
- Change fetchTransactionCount call to fetchEVMData
- Call generateAIScore with address and evmData
- Extract score from AI result
- Log AI score and reasoning
- Keep existing signScoreData call unchanged
**Validation:** Endpoint calls AI scoring function

### Task 5.3: Enhance /score response with metadata
**What:** Add metadata field to API response
**Files:** `oracle/app/src/index.js`
**Actions:**
- Keep existing response fields (score, wallet_address, timestamp_ms, signature)
- Add metadata object with reasoning, risk_factors, strengths, features
- Ensure metadata is NOT included in signature
**Validation:** Response includes both signed fields and metadata object

### Task 5.4: Enhance /health endpoint with Ollama status
**What:** Add Ollama connectivity check to health endpoint
**Files:** `oracle/app/src/index.js`
**Actions:**
- Initialize health object with status 'ok', timestamp, ollama 'unknown'
- Try to call ollamaClient.list()
- On success: set ollama to 'connected'
- On failure: set ollama to 'unavailable', status to 'degraded'
- Return health JSON
**Validation:** Health endpoint returns object with status, timestamp, ollama fields

## Phase 6: Local Testing

### Task 6.1: Test with local Ollama instance
**What:** Verify AI scoring works outside TEE
**Actions:**
- Start local Ollama: `docker run -d --name ollama -p 11434:11434 ollama/ollama:0.5.4`
- Pull model: `docker exec ollama ollama pull llama3.2:1b`
- Run app: `OLLAMA_HOST=http://localhost:11434 node oracle/app/src/index.js /tmp/test-key.bin`
- Test health: `curl http://localhost:3000/health`
- Test score: `curl "http://localhost:3000/score?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba"`
**Validation:**
- Health shows `"ollama":"connected"`
- Score response includes metadata.reasoning
- Response time < 15 seconds

### Task 6.2: Verify response structure
**What:** Validate API response matches specification
**Actions:**
- Parse score response as JSON
- Verify score is number 0-1000
- Verify wallet_address, timestamp_ms, signature are strings
- Verify metadata object exists
- Verify metadata contains reasoning (string), risk_factors (array), strengths (array), features (object)
**Validation:** All fields present with correct types

### Task 6.3: Test fallback scoring
**What:** Verify fallback works when Ollama unavailable
**Actions:**
- Stop Ollama container: `docker stop ollama`
- Call /score endpoint
- Verify response still returns (no crash)
- Verify metadata.reasoning contains "Fallback"
- Verify metadata.risk_factors includes "AI scoring unavailable"
**Validation:** Service remains available, returns fallback score

## Phase 7: Build & Deploy

### Task 7.1: Build Docker image with Nix
**What:** Create reproducible image with AI scoring changes
**Actions:**
- Run `cd oracle && ./nix.sh build-node-amd64`
- Verify build completes without hash errors
- Check output: node-amd64-image.tar.gz exists
**Validation:** Nix build succeeds, generates image file

### Task 7.2: Deploy to TEE enclave
**What:** Run full deployment to Oyster CVM
**Prerequisites:** PRIVATE_KEY and DOCKER_REGISTRY environment variables set
**Actions:**
- Run `cd oracle && ./deploy.sh`
- Monitor Ollama health check polling (should take 2-5 minutes)
- Wait for "Ollama is ready and connected!" message
- Verify all deployment steps complete
**Validation:** deployment.env file created with all IDs, no errors in output

### Task 7.3: Verify TEE health endpoint
**What:** Confirm Ollama running in enclave
**Actions:**
- Source deployment.env
- Call `curl "http://${PUBLIC_IP}:3000/health" | jq`
- Verify response has `"status":"ok"` and `"ollama":"connected"`
**Validation:** Health endpoint confirms Ollama ready

### Task 7.4: Test AI scoring in TEE
**What:** Verify AI analysis works in production enclave
**Actions:**
- Call `curl "http://${PUBLIC_IP}:3000/score?address=0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba" | jq`
- Verify response includes metadata
- Check metadata.reasoning is meaningful (not fallback)
- Verify response time < 15 seconds
**Validation:** AI-generated reasoning returned, not fallback message

### Task 7.5: Verify on-chain signature validation
**What:** Confirm Move contract accepts AI-generated scores
**Actions:**
- `cd oracle/contracts/script`
- Run `bash update_score.sh $PUBLIC_IP $PACKAGE_ID $ORACLE_ID $ENCLAVE_ID 0xebd69ba1ee65c712db335a2ad4b6cb60d2fa94ba`
- Verify transaction succeeds (no signature verification error)
- Run `bash get_score.sh $PACKAGE_ID $ORACLE_ID`
- Verify score matches enclave response
**Validation:** On-chain score stored successfully, signature verified

## Phase 8: Performance Validation

### Task 8.1: Measure cold start time
**What:** Verify deployment completes within acceptable timeframe
**Actions:**
- Redeploy from scratch
- Measure time from `./deploy.sh` start to "Ollama is ready" message
- Record duration
**Validation:** Cold start completes in < 5 minutes

### Task 8.2: Measure request latency
**What:** Benchmark score endpoint performance
**Actions:**
- Make 10 consecutive /score requests with different addresses
- Measure response times
- Calculate p50, p95, p99 percentiles
**Validation:** p95 latency < 15 seconds

### Task 8.3: Monitor memory usage
**What:** Ensure enclave stays within resource limits
**Actions:**
- SSH into Oyster instance or use monitoring
- Check memory usage during AI inference
- Verify no OOM kills
**Validation:** Peak memory usage < 6GB (75% of 8GB limit)

## Dependencies Between Tasks

**Blocking Dependencies:**
- Task 1.2 depends on 1.1 (need package.json before npm install)
- Task 1.3 depends on 1.2 (need package-lock.json before Nix build)
- Task 2.3 depends on 2.1 (need docker-compose before deploy.sh update)
- Task 4.2 depends on 3.1 (generateAIScore calls extractTransactionFeatures)
- Task 4.2 depends on 4.1 (needs ollamaClient)
- Task 5.2 depends on 4.2 and 5.1 (needs AI function and fetchEVMData)
- Task 5.3 depends on 5.2 (needs AI result to add to response)
- Task 6.x depends on Phase 1-5 completion
- Task 7.1 depends on 1.3 (need Nix hash update)
- Task 7.2 depends on 7.1 and 2.1-2.3 (need image and docker-compose)
- Task 7.3-7.5 depend on 7.2 (need deployment)
- Task 8.x depends on 7.2 (need running deployment)

**Parallelizable Work:**
- Task 2.1-2.2 can be done in parallel with 3.1-3.2 (different files)
- Task 4.3-4.4 can be merged into 4.2 (same function)
- Task 5.1-5.4 can be done sequentially but independently tested
- Task 8.1-8.3 can be done in parallel (independent measurements)

## Estimated Task Count

Total tasks: 30
- Phase 1: 3 tasks (dependencies)
- Phase 2: 3 tasks (docker orchestration)
- Phase 3: 2 tasks (feature extraction)
- Phase 4: 4 tasks (AI engine)
- Phase 5: 4 tasks (API updates)
- Phase 6: 3 tasks (local testing)
- Phase 7: 5 tasks (deployment)
- Phase 8: 3 tasks (performance)
- Additional validation: 3 tasks (integrated testing)
