# AI Scoring Engine Specification

## ADDED Requirements

### Requirement: Feature Extraction from EVM Data
The oracle application SHALL extract DeFi-relevant features from EVM transaction data for AI analysis.

#### Scenario: Temporal feature extraction
- **WHEN** extractTransactionFeatures is called with EVM data
- **THEN** it SHALL extract timestamps from Block.Timestamp fields
- **AND** it SHALL calculate accountAgeDays as (now - oldest_timestamp) / ONE_DAY
- **AND** it SHALL count recentActivity.day as transactions within 24 hours
- **AND** it SHALL count recentActivity.week as transactions within 7 days
- **AND** it SHALL count recentActivity.month as transactions within 30 days

#### Scenario: Diversity feature extraction
- **WHEN** extractTransactionFeatures analyzes events
- **THEN** it SHALL count uniqueContracts as Set of Log.Address values
- **AND** it SHALL detect protocolsUsed by checking address prefixes
- **AND** it SHALL recognize Uniswap addresses starting with 0xa0b8
- **AND** it SHALL recognize Aave addresses starting with 0x7a25
- **AND** it SHALL recognize Uniswap V3 addresses starting with 0x1f98
- **AND** it SHALL return protocolsUsed as array of protocol names

#### Scenario: Value feature extraction
- **WHEN** extractTransactionFeatures processes transactions
- **THEN** it SHALL extract Transaction.Value as float
- **AND** it SHALL filter out zero values
- **AND** it SHALL calculate valueStats.total as sum of all values
- **AND** it SHALL calculate valueStats.average as total / count
- **AND** it SHALL set average to 0 if no non-zero values exist

#### Scenario: Complete feature object
- **WHEN** extractTransactionFeatures returns
- **THEN** the result SHALL include totalTransactions (number)
- **AND** it SHALL include accountAgeDays (number)
- **AND** it SHALL include recentActivity object with day, week, month counts
- **AND** it SHALL include uniqueContracts (number)
- **AND** it SHALL include protocolsUsed (array of strings)
- **AND** it SHALL include valueStats object with total, average, count

### Requirement: AI Score Generation
The oracle SHALL use Ollama LLM to generate reputation scores with reasoning.

#### Scenario: Ollama client initialization
- **WHEN** application starts
- **THEN** it SHALL import Ollama from 'ollama' package
- **AND** it SHALL create client with host from OLLAMA_HOST environment variable
- **AND** it SHALL default to http://127.0.0.1:11434 if OLLAMA_HOST not set

#### Scenario: AI scoring request
- **WHEN** generateAIScore is called with address and EVM data
- **THEN** it SHALL call extractTransactionFeatures first
- **AND** it SHALL build structured prompt with wallet address and features
- **AND** it SHALL include 5 scoring criteria in prompt (volume, maturity, diversity, activity, value)
- **AND** it SHALL request JSON format output
- **AND** it SHALL specify schema with score, reasoning, risk_factors, strengths fields

#### Scenario: Ollama API invocation
- **WHEN** calling Ollama for score generation
- **THEN** it SHALL use model llama3.2:1b
- **AND** it SHALL set format to 'json'
- **AND** it SHALL set temperature to 0.3
- **AND** it SHALL set num_predict to 500 tokens
- **AND** it SHALL await response from ollamaClient.generate

#### Scenario: AI response parsing
- **WHEN** Ollama returns response
- **THEN** it SHALL parse response.response as JSON
- **AND** it SHALL extract score field as integer
- **AND** it SHALL clamp score to range 0-1000 using Math.max and Math.min
- **AND** it SHALL extract reasoning as string (default 'AI analysis generated')
- **AND** it SHALL extract risk_factors as array (default empty array)
- **AND** it SHALL extract strengths as array (default empty array)

#### Scenario: AI scoring failure fallback
- **WHEN** Ollama API call fails or throws error
- **THEN** it SHALL log error with message 'AI scoring failed, falling back to simple count'
- **AND** it SHALL calculate fallback score as totalTransactions * 10
- **AND** it SHALL cap fallback score at 1000
- **AND** it SHALL set reasoning to 'Fallback: Simple transaction count'
- **AND** it SHALL set risk_factors to ['AI scoring unavailable']
- **AND** it SHALL set strengths to empty array
- **AND** it SHALL include features in response

#### Scenario: AI result structure
- **WHEN** generateAIScore returns
- **THEN** result SHALL include score (number 0-1000)
- **AND** it SHALL include reasoning (string)
- **AND** it SHALL include riskFactors (array)
- **AND** it SHALL include strengths (array)
- **AND** it SHALL include features (object from extraction)

### Requirement: Enhanced Health Check
The application SHALL report Ollama connectivity status in health endpoint.

#### Scenario: Ollama connectivity check
- **WHEN** /health endpoint is requested
- **THEN** it SHALL initialize health object with status 'ok' and timestamp
- **AND** it SHALL set ollama field to 'unknown' initially
- **AND** it SHALL attempt to call ollamaClient.list()
- **AND** if successful it SHALL set ollama to 'connected'
- **AND** if failed it SHALL set ollama to 'unavailable' and status to 'degraded'

#### Scenario: Health response format
- **WHEN** /health endpoint responds
- **THEN** response SHALL include status field ('ok' or 'degraded')
- **AND** it SHALL include timestamp field (number)
- **AND** it SHALL include ollama field ('connected', 'unavailable', or 'unknown')
- **AND** it SHALL return JSON content type

## MODIFIED Requirements

### Requirement: Score Endpoint Enhancement
The /score endpoint SHALL use AI scoring instead of simple transaction count.

#### Scenario: Fetch full EVM data
- **WHEN** /score endpoint is called with address parameter
- **THEN** it SHALL call fetchEVMData (renamed from fetchTransactionCount)
- **AND** fetchEVMData SHALL return full response.data object
- **AND** fetchEVMData SHALL NOT return just Events.length
- **AND** it SHALL validate response.data.EVM.Events exists

#### Scenario: Generate AI score
- **WHEN** EVM data is fetched successfully
- **THEN** it SHALL call generateAIScore with address and evmData
- **AND** it SHALL extract score from AI result
- **AND** it SHALL log score and reasoning to console
- **AND** it SHALL proceed with existing signature generation

#### Scenario: Enhanced response with metadata
- **WHEN** /score endpoint returns response
- **THEN** it SHALL include existing fields: score, wallet_address, timestamp_ms, signature
- **AND** it SHALL add new metadata field as object
- **AND** metadata SHALL include reasoning (string)
- **AND** metadata SHALL include risk_factors (array)
- **AND** metadata SHALL include strengths (array)
- **AND** metadata SHALL include features (object)
- **AND** metadata SHALL NOT be included in signature (informational only)

#### Scenario: Error handling with AI
- **WHEN** generateAIScore fails
- **THEN** it SHALL use fallback score
- **AND** response SHALL still be returned (no hard failure)
- **AND** metadata SHALL indicate fallback was used
- **AND** signature SHALL be generated with fallback score

### Requirement: Dependency Management
The application SHALL include Ollama npm package.

#### Scenario: Package.json update
- **WHEN** package.json is read
- **THEN** dependencies SHALL include "ollama": "^0.6.0"
- **AND** version SHALL be updated to "0.2.0"
- **AND** other dependencies SHALL remain unchanged

#### Scenario: Package lock update
- **WHEN** npm install is run
- **THEN** package-lock.json SHALL be updated with ollama dependency tree
- **AND** integrity hashes SHALL be computed
- **AND** npm install SHALL succeed without errors

## REMOVED Requirements

None - existing signature logic and BCS serialization remain unchanged
