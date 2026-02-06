# Implementation Tasks

## 1. Dependencies and Configuration
- [x] 1.1 Install @mysten/dapp-kit and @mysten/sui packages
- [x] 1.2 Create frontend/.env.local with Sui configuration
- [x] 1.3 Create frontend/src/types/oracle.d.ts type definitions
- [x] 1.4 Create frontend/src/lib/suiNetwork.ts network configuration

## 2. Provider Setup
- [x] 2.1 Update frontend/src/App.tsx with SuiClientProvider and WalletProvider
- [x] 2.2 Import @mysten/dapp-kit CSS styles in App.tsx
- [x] 2.3 Configure testnet as default network

## 3. Oracle API Integration
- [x] 3.1 Create frontend/src/lib/oracleService.ts with fetchScoreFromOracle function
- [x] 3.2 Add hexToUint8Array utility for signature conversion
- [x] 3.3 Extend ReputaContext with oracleSignature and oracleTimestamp fields
- [x] 3.4 Add setOracleData method to ReputaContext
- [x] 3.5 Update frontend/src/pages/Analyzing.tsx to call real oracle API
- [x] 3.6 Add error handling UI in Analyzing.tsx for API failures

## 4. Wallet Connection Implementation
- [x] 4.1 Replace mock implementation in frontend/src/pages/WalletConnect.tsx
- [x] 4.2 Add useCurrentAccount hook for wallet address
- [x] 4.3 Add useSignAndExecuteTransaction hook for transaction signing
- [x] 4.4 Integrate ConnectButton component from @mysten/dapp-kit
- [x] 4.5 Add navigation guard to prevent accessing /record without oracle data
- [x] 4.6 Sync connected wallet address to ReputaContext automatically

## 5. Transaction Construction
- [x] 5.1 Build Transaction object with moveCall to update_wallet_score
- [x] 5.2 Convert EVM address hex to vector<u8> for Move contract
- [x] 5.3 Convert oracle signature hex to vector<u8> for Move contract
- [x] 5.4 Pass all six required arguments (oracle, enclave, score, wallet_address, timestamp, signature)
- [x] 5.5 Use environment variables for package/object IDs

## 6. Transaction Execution and Feedback
- [x] 6.1 Execute transaction with signAndExecute mutation
- [x] 6.2 Display transaction error messages in Alert component
- [x] 6.3 Store transaction hash in ReputaContext on success
- [x] 6.4 Auto-navigate to /success after transaction confirmation

## 7. Success Page Enhancement
- [x] 7.1 Add getSuiExplorerUrl utility in frontend/src/pages/Success.tsx
- [x] 7.2 Update "View on Explorer" button with real txHash link
- [x] 7.3 Link to Suiscan testnet explorer

## 8. Testing
- [x] 8.1 Test oracle API calls with real EVM addresses
- [x] 8.2 Test wallet connection with Sui Wallet browser extension
- [x] 8.3 Test transaction signing and on-chain recording
- [x] 8.4 Verify transaction appears on Suiscan explorer
- [x] 8.5 Test error cases (no wallet, insufficient gas, invalid signature)
- [x] 8.6 Test navigation guards (direct /record access without data)

## 9. Documentation
- [ ] 9.1 Update frontend/CLAUDE.md with Sui integration details
- [ ] 9.2 Document environment variables in CLAUDE.md
- [ ] 9.3 Add troubleshooting section for common issues
