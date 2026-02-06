# Change: Add Sui Wallet Integration

## Why

The application currently uses mock implementations for Sui wallet connection and oracle score recording. Users cannot actually record their reputation scores on the Sui blockchain, which is the core value proposition of migrating DeFi reputation from EVM to Sui. Real wallet integration and smart contract interaction are essential for production functionality.

## What Changes

- Integrate `@mysten/dapp-kit` for Sui wallet connection and transaction signing
- Replace mock oracle score generation with real HTTP API calls to TEE oracle
- Enable calling `update_wallet_score` Move entry function on Sui testnet
- Store oracle signature data in ReputaContext for later transaction use
- Add real transaction hash display with Suiscan explorer links
- Support major Sui wallets (Sui Wallet, Suiet, Ethos)

## Impact

- **Affected specs**: `sui-wallet-connection` (new capability), `oracle-integration` (new capability)
- **Affected code**:
  - `frontend/src/App.tsx` - Add SuiClientProvider and WalletProvider
  - `frontend/src/pages/WalletConnect.tsx` - Replace mock with real wallet hooks
  - `frontend/src/pages/Analyzing.tsx` - Replace mock with real oracle API calls
  - `frontend/src/pages/Success.tsx` - Add real explorer links
  - `frontend/src/contexts/ReputaContext.tsx` - Add oracle signature fields
  - `frontend/src/lib/suiNetwork.ts` - New network configuration
  - `frontend/src/lib/oracleService.ts` - New oracle API client
  - `frontend/src/types/oracle.d.ts` - New type definitions
- **New dependencies**: `@mysten/dapp-kit@^1.0.1`, `@mysten/sui@^1.31.0`
- **Environment variables**:
  - `VITE_SUI_NETWORK` - Network name (testnet/mainnet)
  - `VITE_ORACLE_API_URL` - Oracle API endpoint
  - `VITE_ORACLE_PACKAGE_ID` - Published Move package ID
  - `VITE_ORACLE_OBJECT_ID` - Shared ScoreOracle object ID
  - `VITE_ENCLAVE_OBJECT_ID` - Shared Enclave object ID
- **Works alongside**: `add-rainbowkit-wallet-connection` (EVM wallet input remains separate from Sui wallet recording)
