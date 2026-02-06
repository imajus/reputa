# Wallet Connection Specification

## ADDED Requirements

### Requirement: EVM Wallet Connection

The system SHALL provide wallet connection functionality using RainbowKit to capture the user's EVM wallet address at the entry point of the reputation analysis flow.

#### Scenario: User connects MetaMask wallet

- **WHEN** user navigates to the address input page (`/analyze`)
- **AND** clicks the Connect Wallet button
- **AND** selects MetaMask from the wallet options
- **AND** approves the connection in MetaMask
- **THEN** the connected wallet address is captured
- **AND** the user is automatically navigated to the questionnaire page (`/questionnaire`)
- **AND** the wallet address is stored in ReputaContext state

#### Scenario: User connects wallet with ENS name

- **WHEN** user connects a wallet that has an ENS name (e.g., vitalik.eth)
- **THEN** the ENS name is resolved to the 0x address automatically
- **AND** both the ENS name and resolved address are stored in ReputaContext
- **AND** the ENS name is displayed in the UI where applicable

#### Scenario: User connects via WalletConnect (mobile)

- **WHEN** user clicks Connect Wallet on mobile device
- **AND** selects WalletConnect option
- **THEN** a QR code is displayed in the RainbowKit modal
- **AND** user scans QR code with their mobile wallet app
- **AND** approves connection in mobile wallet
- **AND** wallet address is captured and user proceeds to questionnaire

#### Scenario: User rejects wallet connection

- **WHEN** user clicks Connect Wallet
- **AND** the wallet modal opens
- **AND** user closes the modal or rejects the connection
- **THEN** the user remains on the address input page
- **AND** the Connect Wallet button remains available
- **AND** no error message is shown (user intentionally declined)

### Requirement: Multi-Chain Support

The wallet connection SHALL support major EVM chains to accommodate users across different networks.

#### Scenario: User connects from Ethereum mainnet

- **WHEN** user's wallet is connected to Ethereum mainnet
- **AND** user approves the wallet connection
- **THEN** the wallet address is captured
- **AND** user proceeds to questionnaire
- **AND** no network switch is required

#### Scenario: User connects from Optimism

- **WHEN** user's wallet is connected to Optimism L2
- **AND** user approves the wallet connection
- **THEN** the wallet address is captured
- **AND** user proceeds to questionnaire
- **AND** the same address is valid across all EVM chains

#### Scenario: User connects from unsupported chain

- **WHEN** user's wallet is connected to a chain not in the configured list (mainnet, Optimism, Arbitrum, Base, Polygon)
- **THEN** RainbowKit automatically displays the supported chains
- **AND** user can proceed with connection (address is still valid)
- **AND** no network switch is enforced (we only need the address, not chain-specific interactions)

### Requirement: Wallet Connection State Management

The wallet connection state SHALL be integrated with the existing ReputaContext for seamless state management across the application flow.

#### Scenario: Connected address is stored in global state

- **WHEN** user successfully connects their wallet
- **THEN** the wallet address (0x format) is stored in `resolvedAddress` field in ReputaContext
- **AND** the ENS name (if available) or address is stored in `evmAddress` field
- **AND** the state persists throughout the user journey
- **AND** downstream components access the address via `useReputa()` hook

#### Scenario: User switches wallet account

- **WHEN** user has already connected a wallet
- **AND** switches to a different account in their wallet
- **THEN** the ReputaContext is updated with the new address
- **AND** if the user is still on the address input page, they are navigated to questionnaire with new address
- **AND** if the user is beyond the address input page, the address updates in state but navigation does not change

### Requirement: Provider Configuration

The application SHALL configure wagmi and RainbowKit providers with proper chain support and theming.

#### Scenario: WagmiProvider is configured with supported chains

- **WHEN** the application initializes
- **THEN** WagmiProvider is configured with chains: Ethereum mainnet, Optimism, Arbitrum, Base, Polygon
- **AND** WalletConnect project ID is loaded from environment variable `VITE_WALLETCONNECT_PROJECT_ID`
- **AND** connectors include injected (MetaMask), WalletConnect, and Coinbase Wallet

#### Scenario: RainbowKit theme matches shadcn/ui design system

- **WHEN** the RainbowKit modal is displayed
- **THEN** the modal uses custom theme colors matching CSS custom properties
- **AND** accent color uses `--primary` variable
- **AND** border radius is set to 'medium' (0.5rem)
- **AND** the visual style is consistent with the rest of the application

#### Scenario: Provider hierarchy is correctly nested

- **WHEN** the application renders
- **THEN** WagmiProvider is nested inside the root QueryClientProvider
- **AND** RainbowKitProvider is nested inside WagmiProvider
- **AND** ReputaProvider and BrowserRouter are nested inside RainbowKitProvider
- **AND** all components have access to wallet connection state

### Requirement: Connect Button UI

The Connect Wallet button SHALL be styled to match the existing shadcn/ui design system and provide clear user guidance.

#### Scenario: Connect button is displayed on address input page

- **WHEN** user navigates to `/analyze` page
- **THEN** a Connect Wallet button is prominently displayed
- **AND** the button uses shadcn/ui Button component styling
- **AND** helper text explains "We'll analyze your on-chain history from Ethereum and L2s"
- **AND** an info card with Lightbulb icon provides additional context

#### Scenario: Connecting state is shown during wallet approval

- **WHEN** user clicks Connect Wallet
- **AND** the wallet connection is in progress
- **THEN** a loading indicator or "Connecting..." text is shown
- **AND** the button is disabled during connection
- **AND** user cannot trigger multiple connection attempts

#### Scenario: Connected wallet address is displayed

- **WHEN** wallet connection succeeds
- **THEN** the address is briefly visible (during auto-navigation transition)
- **AND** ENS name is shown instead of address if available
- **AND** a checkmark icon indicates successful connection

### Requirement: Wallet Disconnection Handling

The system SHALL gracefully handle wallet disconnection events.

#### Scenario: User disconnects wallet on address input page

- **WHEN** user is on the address input page (`/analyze`)
- **AND** user disconnects their wallet via RainbowKit button or wallet extension
- **THEN** the ReputaContext state is cleared (`evmAddress` and `resolvedAddress` set to empty)
- **AND** the Connect Wallet button is shown again
- **AND** user can reconnect with same or different wallet

#### Scenario: User disconnects wallet after questionnaire

- **WHEN** user has completed the address input and questionnaire
- **AND** user disconnects their wallet
- **THEN** the ReputaContext state retains the original address
- **AND** the score calculation and display continue unaffected
- **AND** the flow is not interrupted (score already calculated for the original address)

### Requirement: Error Handling

The wallet connection SHALL handle errors gracefully and provide meaningful feedback to users.

#### Scenario: WalletConnect project ID is missing

- **WHEN** the application starts
- **AND** `VITE_WALLETCONNECT_PROJECT_ID` environment variable is not set
- **THEN** WalletConnect connector is not available
- **AND** injected wallets (MetaMask, Coinbase) still work
- **AND** console warning is logged for developers

#### Scenario: ENS resolution fails

- **WHEN** user connects a wallet with an ENS name
- **AND** the ENS resolution RPC call fails or times out
- **THEN** the wallet address (0x format) is used as fallback
- **AND** the address is stored in both `evmAddress` and `resolvedAddress`
- **AND** the user flow continues without interruption
- **AND** no error message is shown to the user

#### Scenario: No wallet extension installed

- **WHEN** user clicks Connect Wallet
- **AND** no browser wallet extension is installed
- **THEN** RainbowKit modal shows wallet download options
- **AND** links to install MetaMask, Coinbase Wallet, etc. are provided
- **AND** WalletConnect QR code option is available for mobile wallets
