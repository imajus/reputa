# Oracle Integration Specification

## ADDED Requirements

### Requirement: Oracle API Client
The application SHALL provide a service module for communicating with the TEE oracle API.

#### Scenario: Fetch score from oracle
- **WHEN** fetchScoreFromOracle is called with an EVM address
- **THEN** it SHALL make a GET request to `<ORACLE_API_URL>/score?address=<address>`
- **AND** it SHALL include "Accept: application/json" header
- **AND** it SHALL parse the JSON response

#### Scenario: Oracle API success
- **WHEN** oracle responds with 200 status
- **THEN** it SHALL validate response contains score (number)
- **AND** it SHALL validate response contains signature (string)
- **AND** it SHALL validate response contains walletAddress (string)
- **AND** it SHALL return OracleScoreResponse with all fields

#### Scenario: Oracle API failure
- **WHEN** oracle responds with non-200 status
- **THEN** it SHALL read the response body as text
- **AND** it SHALL throw Error with format "Oracle API error: <status> <body>"

#### Scenario: Invalid response format
- **WHEN** oracle response is missing required fields
- **THEN** it SHALL throw Error "Invalid oracle response format"
- **AND** it SHALL not proceed with incomplete data

### Requirement: Oracle Data Storage
The application SHALL extend ReputaContext to store oracle signature data for transaction use.

#### Scenario: Context state extension
- **WHEN** ReputaContext is defined
- **THEN** it SHALL include oracleSignature field (string)
- **AND** it SHALL include oracleTimestamp field (number)
- **AND** both fields SHALL initialize to empty/zero in initialState

#### Scenario: Set oracle data method
- **WHEN** setOracleData is called with signature and timestamp
- **THEN** it SHALL update state.oracleSignature
- **AND** it SHALL update state.oracleTimestamp
- **AND** both values SHALL be accessible via useReputa hook

### Requirement: Score Analysis Integration
The application SHALL replace mock score generation with real oracle API calls in the Analyzing page.

#### Scenario: Trigger oracle fetch
- **WHEN** analysis steps complete in Analyzing component
- **THEN** it SHALL call fetchScoreFromOracle with resolved or EVM address
- **AND** it SHALL use resolvedAddress if available, else evmAddress
- **AND** it SHALL throw error if no address is available

#### Scenario: Store oracle response
- **WHEN** oracle API returns successfully
- **THEN** it SHALL call setOracleData with signature and timestamp
- **AND** it SHALL call setScore with score and breakdown
- **AND** it SHALL mark all analysis steps as completed
- **AND** it SHALL navigate to /score page after 500ms delay

#### Scenario: Handle oracle errors
- **WHEN** oracle API call fails
- **THEN** it SHALL set error state with error message
- **AND** it SHALL display error UI with destructive Card styling
- **AND** it SHALL show "Try Again" button that navigates to /analyze

#### Scenario: Error UI display
- **WHEN** error state is set
- **THEN** it SHALL render error Card instead of progress UI
- **AND** it SHALL display error message to user
- **AND** it SHALL provide Button to restart from address input

### Requirement: Environment Configuration
The application SHALL use environment variables for oracle and Sui network configuration.

#### Scenario: Required environment variables
- **WHEN** application starts
- **THEN** it SHALL read VITE_ORACLE_API_URL for oracle endpoint
- **AND** it SHALL read VITE_SUI_NETWORK for network selection
- **AND** it SHALL read VITE_ORACLE_PACKAGE_ID for Move package reference
- **AND** it SHALL read VITE_ORACLE_OBJECT_ID for oracle object reference
- **AND** it SHALL read VITE_ENCLAVE_OBJECT_ID for enclave object reference

#### Scenario: Environment file location
- **WHEN** configuring local development
- **THEN** variables SHALL be defined in frontend/.env.local
- **AND** they SHALL be accessible via import.meta.env in Vite
- **AND** they SHALL use VITE_ prefix for exposure to client code

### Requirement: Type Definitions
The application SHALL define TypeScript interfaces for oracle API responses.

#### Scenario: OracleScoreResponse interface
- **WHEN** oracle types are defined
- **THEN** it SHALL include score: number
- **AND** it SHALL include walletAddress: string
- **AND** it SHALL include signature: string
- **AND** it SHALL include publicKey: string
- **AND** it SHALL include timestamp: number

#### Scenario: Type file location
- **WHEN** types are created
- **THEN** they SHALL be in frontend/src/types/oracle.d.ts
- **AND** they SHALL be importable from @/types/oracle
