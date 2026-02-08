# Spec: Oracle Reproducible Scoring

## ADDED Requirements

### Requirement: Deterministic Seed Generation from Wallet Address

The oracle MUST generate a deterministic seed from the wallet address for reproducible AI scoring.

#### Scenario: Normalize wallet address

**Given** a wallet address (with or without 0x prefix, mixed case)
**When** generating a seed
**Then** the address MUST be normalized:
- Converted to lowercase
- 0x prefix removed if present

#### Scenario: Hash with SHA-256

**Given** a normalized wallet address
**When** generating a seed
**Then** the address MUST be hashed using SHA-256

#### Scenario: Extract 32-bit seed

**Given** a SHA-256 hash (32 bytes)
**When** extracting the seed value
**Then** the first 4 bytes MUST be read as unsigned 32-bit big-endian integer

#### Scenario: Same address produces same seed

**Given** the same wallet address
**When** generating seeds multiple times
**Then** the seed value MUST be identical across all calls

#### Scenario: Different addresses produce different seeds

**Given** two different wallet addresses
**When** generating seeds
**Then** the seed values MUST be different (collision probability negligible with SHA-256)

---

### Requirement: Seed Integration with Ollama

The deterministic seed MUST be passed to Ollama for consistent AI generation.

#### Scenario: Pass seed parameter

**Given** a generated seed value
**When** calling Ollama generate API
**Then** the seed MUST be passed via `options.seed` parameter

#### Scenario: Reduce temperature for determinism

**Given** the seeded request
**When** setting generation parameters
**Then** temperature MUST be 0.1 (reduced from 0.3)

#### Scenario: Graceful degradation

**Given** Ollama version that doesn't support seed parameter
**When** the seed parameter is ignored
**Then** the system MUST continue to function without error

---

### Requirement: Reproducibility Guarantees

The system MUST achieve high reproducibility for same wallet scoring while documenting limitations.

#### Scenario: High reproducibility rate

**Given** the same wallet scored multiple times
**When** measuring score consistency
**Then** reproducibility rate MUST be >90% (same score ±20 points)

#### Scenario: Low score variance

**Given** 10 scoring runs for the same wallet
**When** calculating standard deviation
**Then** std dev MUST be <20 points

#### Scenario: Document limitations

**Given** the reproducibility feature
**When** documenting the system
**Then** documentation MUST state:
- Reproducibility is not 100% guaranteed
- Platform factors (GPU, floating-point) may cause variation
- First-run inconsistencies are common with LLMs
- Subsequent runs for same wallet are highly consistent

---

### Requirement: Performance and Compatibility

Seeding MUST not degrade performance or break existing functionality.

#### Scenario: Minimal hashing overhead

**Given** a wallet address to hash
**When** generating the seed
**Then** overhead MUST be ≤10ms

#### Scenario: No latency regression

**Given** requests with seeding enabled
**When** measuring P50 and P95 latency
**Then** latency MUST not increase (may decrease slightly due to lower temperature)

#### Scenario: Backward compatibility

**Given** the seeding feature
**When** enabled
**Then** API response format and signature format MUST remain unchanged
