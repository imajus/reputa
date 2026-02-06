# Sui Wallet Connection Specification

## ADDED Requirements

### Requirement: Sui Wallet Provider Setup
The frontend application SHALL configure Sui blockchain network providers using @mysten/dapp-kit to enable wallet connections and transaction signing.

#### Scenario: Network configuration
- **WHEN** the application initializes
- **THEN** it SHALL create network configuration for testnet and mainnet using createNetworkConfig
- **AND** it SHALL set testnet as the default network
- **AND** it SHALL wrap the application with SuiClientProvider and WalletProvider

#### Scenario: Provider hierarchy
- **WHEN** setting up React providers
- **THEN** SuiClientProvider SHALL be outside WalletProvider
- **AND** WalletProvider SHALL have autoConnect enabled for session persistence

### Requirement: Wallet Connection UI
The application SHALL provide a user interface for connecting Sui wallets using the built-in ConnectButton component.

#### Scenario: Disconnected state
- **WHEN** user navigates to /record without a connected wallet
- **THEN** it SHALL display the ConnectButton component
- **AND** it SHALL show explanatory text about signing a transaction
- **AND** it SHALL display estimated gas cost

#### Scenario: Wallet selection
- **WHEN** user clicks ConnectButton
- **THEN** it SHALL display available Sui wallets (Sui Wallet, Suiet, Ethos, etc.)
- **AND** it SHALL show "Install Wallet" option if no wallet is detected

#### Scenario: Connection success
- **WHEN** wallet connection succeeds
- **THEN** it SHALL automatically store the wallet address in ReputaContext
- **AND** it SHALL display the connected address (truncated format)
- **AND** it SHALL show transaction preview UI

### Requirement: Transaction Construction
The application SHALL construct Move contract transactions using the Transaction builder from @mysten/sui.

#### Scenario: Build update_wallet_score transaction
- **WHEN** user clicks "Sign Transaction" button
- **THEN** it SHALL create a new Transaction object
- **AND** it SHALL call moveCall with target `<packageId>::score_oracle::update_wallet_score`
- **AND** it SHALL pass oracle object reference from VITE_ORACLE_OBJECT_ID
- **AND** it SHALL pass enclave object reference from VITE_ENCLAVE_OBJECT_ID
- **AND** it SHALL pass score as u64 from ReputaContext
- **AND** it SHALL convert EVM address hex string to vector<u8> bytes
- **AND** it SHALL pass timestamp as u64 from oracle response
- **AND** it SHALL convert oracle signature hex string to vector<u8> bytes

#### Scenario: Hex to bytes conversion
- **WHEN** converting hex strings to byte arrays
- **THEN** it SHALL strip "0x" prefix if present
- **AND** it SHALL parse each pair of hex characters as a byte
- **AND** it SHALL return Uint8Array for use in transaction arguments

### Requirement: Transaction Signing and Execution
The application SHALL sign and execute transactions using the useSignAndExecuteTransaction hook.

#### Scenario: Transaction submission
- **WHEN** transaction is built
- **THEN** it SHALL call signAndExecute mutation with the transaction
- **AND** it SHALL display "Signing..." loading state while pending
- **AND** it SHALL disable the sign button while transaction is in progress

#### Scenario: Transaction success
- **WHEN** transaction executes successfully
- **THEN** it SHALL extract the digest from the response
- **AND** it SHALL store the digest in ReputaContext as txHash
- **AND** it SHALL navigate to /success page after 1 second delay

#### Scenario: Transaction failure
- **WHEN** transaction execution fails
- **THEN** it SHALL display the error message in a destructive Alert component
- **AND** it SHALL allow the user to retry signing
- **AND** it SHALL log the error to console for debugging

### Requirement: Navigation Guards
The application SHALL prevent users from accessing wallet connection page without required oracle data.

#### Scenario: Missing oracle data
- **WHEN** user navigates to /record without score or signature
- **THEN** it SHALL redirect to /analyze page
- **AND** it SHALL not display wallet connection UI

#### Scenario: Valid navigation
- **WHEN** user navigates to /record with valid score and signature
- **THEN** it SHALL allow access to wallet connection page
- **AND** it SHALL display transaction preview with oracle data

### Requirement: Transaction Verification Display
The application SHALL display transaction details on the success page with explorer links.

#### Scenario: Success page with transaction hash
- **WHEN** user lands on /success page after transaction
- **THEN** it SHALL display the transaction hash from ReputaContext
- **AND** it SHALL provide a "View on Explorer" link to Suiscan testnet
- **AND** the link SHALL construct URL as `https://suiscan.xyz/testnet/tx/<digest>`

#### Scenario: Missing transaction hash
- **WHEN** transaction hash is not available
- **THEN** it SHALL disable the "View on Explorer" button
- **AND** it SHALL not crash or show broken links
