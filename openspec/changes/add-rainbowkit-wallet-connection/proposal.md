# Change: Add RainbowKit Wallet Connection

## Why

The current address input requires manual copy-paste of EVM addresses or ENS names, which is error-prone and provides poor UX. Users must trust they're entering the correct address, and ENS resolution is currently mocked. Industry-standard Web3 applications use direct wallet connection for security, convenience, and better user experience.

## What Changes

- Replace manual address input field with RainbowKit's Connect Wallet button
- Integrate wagmi for real-time wallet connection and ENS resolution
- Auto-navigate to questionnaire when wallet successfully connects
- Maintain existing ReputaContext state management (no breaking changes)
- Support major EVM chains (Ethereum mainnet, Optimism, Arbitrum, Base, Polygon)

## Impact

- **Affected specs**: `wallet-connection` (new capability)
- **Affected code**:
  - `frontend/src/pages/AddressInput.tsx` - Replace manual input with ConnectButton
  - `frontend/src/App.tsx` - Add WagmiProvider and RainbowKitProvider
  - `frontend/src/lib/wagmi.ts` - New configuration file
  - `frontend/src/index.css` - Import RainbowKit styles
  - `frontend/package.json` - Add dependencies
- **New dependencies**: `@rainbow-me/rainbowkit`, `wagmi`, `viem@2.x`
- **Environment variables**: `VITE_WALLETCONNECT_PROJECT_ID` (required for WalletConnect)
