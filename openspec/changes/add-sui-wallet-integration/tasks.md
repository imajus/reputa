# Implementation Tasks

## 1. Dependencies and Configuration
- [ ] 1.1 Install @mysten/dapp-kit and @mysten/sui packages
- [ ] 1.2 Create frontend/.env.local with Sui configuration
- [ ] 1.3 Create frontend/src/types/oracle.d.ts type definitions
- [ ] 1.4 Create frontend/src/lib/suiNetwork.ts network configuration

## 2. Provider Setup
- [ ] 2.1 Update frontend/src/App.tsx with SuiClientProvider and WalletProvider
- [ ] 2.2 Import @mysten/dapp-kit CSS styles in App.tsx
- [ ] 2.3 Configure testnet as default network

## 3. Oracle API Integration
- [ ] 3.1 Create frontend/src/lib/oracleService.ts with fetchScoreFromOracle function
- [ ] 3.2 Add hexToUint8Array utility for signature conversion
- [ ] 3.3 Extend ReputaContext with oracleSignature and oracleTimestamp fields
- [ ] 3.4 Add setOracleData method to ReputaContext
- [ ] 3.5 Update frontend/src/pages/Analyzing.tsx to call real oracle API
- [ ] 3.6 Add error handling UI in Analyzing.tsx for API failures

## 4. Wallet Connection Implementation
- [ ] 4.1 Replace mock implementation in frontend/src/pages/WalletConnect.tsx
- [ ] 4.2 Add useCurrentAccount hook for wallet address
- [ ] 4.3 Add useSignAndExecuteTransaction hook for transaction signing
- [ ] 4.4 Integrate ConnectButton component from @mysten/dapp-kit
- [ ] 4.5 Add navigation guard to prevent accessing /record without oracle data
- [ ] 4.6 Sync connected wallet address to ReputaContext automatically

## 5. Transaction Construction
- [ ] 5.1 Build Transaction object with moveCall to update_wallet_score
- [ ] 5.2 Convert EVM address hex to vector<u8> for Move contract
- [ ] 5.3 Convert oracle signature hex to vector<u8> for Move contract
- [ ] 5.4 Pass all six required arguments (oracle, enclave, score, wallet_address, timestamp, signature)
- [ ] 5.5 Use environment variables for package/object IDs

## 6. Transaction Execution and Feedback
- [ ] 6.1 Execute transaction with signAndExecute mutation
- [ ] 6.2 Display transaction error messages in Alert component
- [ ] 6.3 Store transaction hash in ReputaContext on success
- [ ] 6.4 Auto-navigate to /success after transaction confirmation

## 7. Success Page Enhancement
- [ ] 7.1 Add getSuiExplorerUrl utility in frontend/src/pages/Success.tsx
- [ ] 7.2 Update "View on Explorer" button with real txHash link
- [ ] 7.3 Link to Suiscan testnet explorer

## 8. Testing
- [ ] 8.1 Test oracle API calls with real EVM addresses
- [ ] 8.2 Test wallet connection with Sui Wallet browser extension
- [ ] 8.3 Test transaction signing and on-chain recording
- [ ] 8.4 Verify transaction appears on Suiscan explorer
- [ ] 8.5 Test error cases (no wallet, insufficient gas, invalid signature)
- [ ] 8.6 Test navigation guards (direct /record access without data)

## 9. Documentation
- [ ] 9.1 Update frontend/CLAUDE.md with Sui integration details
- [ ] 9.2 Document environment variables in CLAUDE.md
- [ ] 9.3 Add troubleshooting section for common issues
