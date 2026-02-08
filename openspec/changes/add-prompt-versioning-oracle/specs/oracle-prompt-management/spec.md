# Spec: Oracle Prompt Management

## ADDED Requirements

### Requirement: Prompt Version Structure

The oracle MUST define prompts with semantic versioning and hash-based identification.

#### Scenario: Prompt object structure

**Given** a prompt definition
**When** defining the prompt
**Then** it MUST include:
- `version` field (semantic version string, e.g., "1.0.0")
- `hash` field (8-character SHA-256 hash of template function)
- `template` field (function accepting features and questionnaire, returning prompt string)

#### Scenario: Prompt hash computation

**Given** a prompt template function
**When** computing the hash
**Then** the hash MUST be:
- SHA-256 of template function toString()
- Truncated to first 8 characters (hex)
- Computed once at module load time

#### Scenario: Multiple prompt versions coexist

**Given** multiple prompt definitions (V1, V2, etc.)
**When** the prompts module loads
**Then** all versions MUST be available as named exports

---

### Requirement: Active Prompt Selection

The oracle MUST support dynamic prompt selection for gradual rollout.

#### Scenario: ACTIVE_PROMPT export

**Given** the prompts module
**When** importing the module
**Then** ACTIVE_PROMPT MUST be exported as the currently deployed version

#### Scenario: Change active prompt without code changes

**Given** a new prompt version ready for deployment
**When** updating ACTIVE_PROMPT assignment
**Then** only one line needs to change (ACTIVE_PROMPT = PROMPT_VX)

---

### Requirement: Prompt Metadata in Responses

The oracle MUST include prompt version and hash in API response metadata for debugging.

#### Scenario: Metadata includes version

**Given** a scoring response
**When** constructing the metadata object
**Then** metadata MUST include `prompt_version` field with active prompt version

#### Scenario: Metadata includes hash

**Given** a scoring response
**When** constructing the metadata object
**Then** metadata MUST include `prompt_hash` field with active prompt hash

#### Scenario: Metadata is not signed

**Given** prompt version and hash in metadata
**When** signing the response
**Then** only score, wallet_address, timestamp_ms MUST be signed
**And** prompt metadata MUST remain unsigned

---

### Requirement: Prompt Immutability

Once defined, prompt versions MUST remain immutable for audit trail.

#### Scenario: Prompts are immutable

**Given** a prompt version deployed to production
**When** making prompt improvements
**Then** a new version MUST be created (do not modify existing versions)

#### Scenario: Git history tracks versions

**Given** prompt changes over time
**When** reviewing git history
**Then** each semantic version MUST correspond to a distinct git commit

---

### Requirement: Backward Compatibility

Prompt versioning MUST not break existing API contracts.

#### Scenario: Response format unchanged

**Given** prompt versioning enabled
**When** clients request scores
**Then** response structure MUST match pre-versioning format
**And** new metadata fields MUST be additive only

#### Scenario: Signature format unchanged

**Given** prompt versioning enabled
**When** signing scores
**Then** signature MUST cover same fields as before (score, wallet_address, timestamp_ms)
