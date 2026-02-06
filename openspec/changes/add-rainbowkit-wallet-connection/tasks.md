## 1. Dependencies and Configuration

- [x] 1.1 Install RainbowKit, wagmi, and viem packages
- [x] 1.2 Create WalletConnect project and obtain Project ID
- [x] 1.3 Create `.env` file with `VITE_WALLETCONNECT_PROJECT_ID`
- [x] 1.4 Create `frontend/src/lib/wagmi.ts` configuration file

## 2. Provider Setup

- [x] 2.1 Update `frontend/src/App.tsx` to add WagmiProvider
- [x] 2.2 Add RainbowKitProvider with custom theme
- [x] 2.3 Import RainbowKit styles in `frontend/src/index.css`
- [x] 2.4 Verify provider hierarchy (QueryClient > Wagmi > RainbowKit > Tooltip > Reputa > Router)

## 3. AddressInput Component Redesign

- [x] 3.1 Remove manual Input component and validation logic
- [x] 3.2 Add wagmi hooks (useAccount, useEnsName)
- [x] 3.3 Implement ConnectButton with custom styling
- [x] 3.4 Add auto-navigation logic on wallet connection
- [x] 3.5 Update helper text and loading states

## 4. Styling and Theme

- [x] 4.1 Customize RainbowKit theme to match shadcn/ui
- [x] 4.2 Extract CSS custom properties for colors
- [x] 4.3 Ensure mobile responsiveness
- [x] 4.4 Match button styling with existing design system

## 5. Testing and Validation

- [x] 5.1 Test wallet connection with MetaMask
- [-] 5.2 Test with Coinbase Wallet
- [-] 5.3 Test with WalletConnect (mobile)
- [x] 5.4 Test ENS name resolution
- [x] 5.5 Test account switching
- [x] 5.6 Test disconnection handling
- [x] 5.7 Verify state persistence in ReputaContext
- [x] 5.8 End-to-end flow verification (Landing → Connect → Questionnaire → Score → Sui Wallet → Success)
- [x] 5.9 Run TypeScript compilation check (`npx tsc --noEmit`)
- [x] 5.10 Run linter (`npm run lint`)

## 6. Additional Enhancements (Completed)

- [x] 6.1 Create WalletBar component for persistent wallet widget
- [x] 6.2 Integrate WalletBar into Layout component
- [x] 6.3 Configure lightTheme for RainbowKit widget
- [x] 6.4 Update Analyzing page to check wallet connection before API requests
- [x] 6.5 Add error handling with Retry button (no redirect on error)
