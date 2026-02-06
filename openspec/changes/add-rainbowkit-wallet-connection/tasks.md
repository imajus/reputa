## 1. Dependencies and Configuration

- [ ] 1.1 Install RainbowKit, wagmi, and viem packages
- [ ] 1.2 Create WalletConnect project and obtain Project ID
- [ ] 1.3 Create `.env` file with `VITE_WALLETCONNECT_PROJECT_ID`
- [ ] 1.4 Create `frontend/src/lib/wagmi.ts` configuration file

## 2. Provider Setup

- [ ] 2.1 Update `frontend/src/App.tsx` to add WagmiProvider
- [ ] 2.2 Add RainbowKitProvider with custom theme
- [ ] 2.3 Import RainbowKit styles in `frontend/src/index.css`
- [ ] 2.4 Verify provider hierarchy (QueryClient > Wagmi > RainbowKit > Tooltip > Reputa > Router)

## 3. AddressInput Component Redesign

- [ ] 3.1 Remove manual Input component and validation logic
- [ ] 3.2 Add wagmi hooks (useAccount, useEnsName)
- [ ] 3.3 Implement ConnectButton with custom styling
- [ ] 3.4 Add auto-navigation logic on wallet connection
- [ ] 3.5 Update helper text and loading states

## 4. Styling and Theme

- [ ] 4.1 Customize RainbowKit theme to match shadcn/ui
- [ ] 4.2 Extract CSS custom properties for colors
- [ ] 4.3 Ensure mobile responsiveness
- [ ] 4.4 Match button styling with existing design system

## 5. Testing and Validation

- [ ] 5.1 Test wallet connection with MetaMask
- [ ] 5.2 Test with Coinbase Wallet
- [ ] 5.3 Test with WalletConnect (mobile)
- [ ] 5.4 Test ENS name resolution
- [ ] 5.5 Test account switching
- [ ] 5.6 Test disconnection handling
- [ ] 5.7 Verify state persistence in ReputaContext
- [ ] 5.8 End-to-end flow verification (Landing → Connect → Questionnaire → Score → Sui Wallet → Success)
- [ ] 5.9 Run TypeScript compilation check (`npx tsc --noEmit`)
- [ ] 5.10 Run linter (`npm run lint`)
