# Technical Design: RainbowKit Wallet Connection

## Context

The Reputa frontend currently requires manual input of EVM addresses or ENS names at the entry point of the user flow (`frontend/src/pages/AddressInput.tsx`). This approach has several limitations:
- Error-prone manual copy-paste
- Mock ENS resolution (not production-ready)
- No wallet verification
- Poor mobile UX
- Doesn't follow Web3 industry standards

The frontend is built with React 18, TypeScript, Vite, and uses shadcn/ui components with Tailwind CSS. State management uses React Context API via `ReputaContext`, which stores the EVM address and resolved address along with the rest of the user journey state.

## Goals / Non-Goals

**Goals:**
- Replace manual input with industry-standard wallet connection
- Enable real ENS resolution via wagmi
- Maintain existing state management architecture (no breaking changes to ReputaContext)
- Support major EVM chains (Ethereum, Optimism, Arbitrum, Base, Polygon)
- Preserve auto-navigation flow (connect → proceed to questionnaire)
- Match existing UI design system (shadcn/ui + Tailwind)

**Non-Goals:**
- Multi-wallet connection (only one wallet at a time)
- Chain-specific features (we only need the wallet address, not chain-specific interactions)
- Custom wallet connector implementation (use RainbowKit's built-in connectors)
- Backend wallet verification (frontend-only change)

## Decisions

### Library Selection: RainbowKit over Web3Modal

**Decision:** Use RainbowKit (@rainbow-me/rainbowkit + wagmi + viem)

**Alternatives considered:**
1. **Web3Modal** - General-purpose wallet connection library
   - Pros: Framework-agnostic, supports multiple frameworks
   - Cons: Heavier bundle, less React-focused, more complex API
2. **wagmi only** - Use wagmi hooks without UI library
   - Pros: Smaller bundle, full control
   - Cons: Must build wallet selection UI, modal management, mobile support from scratch
3. **Custom implementation with ethers.js**
   - Pros: Complete control
   - Cons: Significant development time, reinventing the wheel, mobile support complexity

**Rationale:** RainbowKit provides:
- React-first design with excellent TypeScript support
- Battle-tested wallet connection UX
- Built-in support for major wallets (MetaMask, Coinbase, WalletConnect)
- Easy theme customization
- Automatic ENS resolution via wagmi
- Mobile-friendly with WalletConnect QR codes
- Active maintenance and community

### Provider Architecture

**Decision:** Nest WagmiProvider inside existing QueryClientProvider

**Provider hierarchy:**
```
QueryClientProvider (existing @tanstack/react-query)
  └─ WagmiProvider (new - wagmi)
      └─ QueryClientProvider (RainbowKit's instance)
          └─ RainbowKitProvider (new - RainbowKit)
              └─ TooltipProvider (existing - Radix UI)
                  └─ ReputaProvider (existing - ReputaContext)
                      └─ BrowserRouter (existing - react-router-dom)
```

**Rationale:**
- wagmi internally uses @tanstack/react-query
- RainbowKit requires both WagmiProvider and its own QueryClientProvider
- Existing QueryClientProvider at root level is compatible
- TooltipProvider and ReputaProvider remain innermost to ensure access to all providers

### UX Pattern: Connect-as-Continue

**Decision:** Auto-navigate to questionnaire when wallet connects (no separate "Continue" button)

**Alternatives considered:**
1. **Connect-then-Continue** - Show ConnectButton, then separate Continue button
   - Pros: Explicit user confirmation step
   - Cons: Extra click, more complex UI, unnecessary friction
2. **Always-visible Connect** - Keep manual input as alternative
   - Pros: Flexibility for users without wallets
   - Cons: Duplicate functionality, security risk with manual input

**Rationale:**
- Cleaner, more streamlined UX (one action instead of two)
- Follows modern Web3 app patterns (e.g., Uniswap, OpenSea)
- Reduces cognitive load
- Better mobile experience
- Matches existing auto-navigation pattern (current implementation navigates on "Continue" click)

**Implementation:**
```typescript
const { address, isConnected } = useAccount();
const { data: ensName } = useEnsName({ address });

useEffect(() => {
  if (isConnected && address) {
    setEvmAddress(ensName || address);
    setResolvedAddress(address);
    navigate('/questionnaire');
  }
}, [isConnected, address, ensName]);
```

### Chain Configuration

**Decision:** Support Ethereum mainnet + major L2s (Optimism, Arbitrum, Base, Polygon)

**Rationale:**
- Helper text in current AddressInput mentions "Ethereum and L2s"
- Oracle analyzes transaction history across multiple chains
- L2s (Optimism, Arbitrum, Base) are major DeFi ecosystems
- Polygon provides additional coverage
- No need to restrict chains since we only need the wallet address (not chain-specific interactions)
- User can connect from any supported chain

**Configuration:**
```typescript
import { mainnet, optimism, arbitrum, base, polygon } from 'wagmi/chains';

export const config = getDefaultConfig({
  appName: 'Reputa',
  projectId: import.meta.env.VITE_WALLETCONNECT_PROJECT_ID,
  chains: [mainnet, optimism, arbitrum, base, polygon],
});
```

### Theme Customization

**Decision:** Custom theme using shadcn/ui CSS variables

**Rationale:**
- Ensure visual consistency with existing design system
- shadcn/ui uses CSS custom properties (CSS variables) for theming
- RainbowKit supports theme customization
- Extract colors from `frontend/src/index.css`

**Implementation:**
```typescript
import { darkTheme } from '@rainbow-me/rainbowkit';

const customTheme = darkTheme({
  accentColor: 'hsl(var(--primary))',
  accentColorForeground: 'hsl(var(--primary-foreground))',
  borderRadius: 'medium', // matches 0.5rem
  fontStack: 'system',
});
```

### State Management Integration

**Decision:** Reuse existing ReputaContext with no changes to interface

**Rationale:**
- `evmAddress` stores ENS name (e.g., "vitalik.eth") or address if no ENS
- `resolvedAddress` stores the actual 0x address
- This mapping already exists in current implementation
- No downstream components need changes
- Backward compatible

## Risks / Trade-offs

### Bundle Size Increase

**Risk:** Adding RainbowKit, wagmi, and viem increases bundle size by ~150KB

**Mitigation:**
- Acceptable trade-off for production-ready wallet integration
- Vite's tree-shaking minimizes unused code
- Can implement code-splitting if needed (lazy load RainbowKit)

**Trade-off decision:** Accept bundle size increase for security and UX benefits

### WalletConnect Project ID Requirement

**Risk:** Requires external dependency (WalletConnect Cloud)

**Mitigation:**
- Free tier supports up to 1M requests/month
- Project ID is public (safe to commit)
- Fallback to injected wallets (MetaMask) if WalletConnect fails

**Trade-off decision:** Acceptable dependency for mobile wallet support

### ENS Resolution Cost

**Risk:** ENS lookups require RPC calls (rate limits, latency)

**Mitigation:**
- wagmi caches ENS lookups automatically
- Show loading state while resolving
- Fallback to address display if ENS fails
- Use `staleTime` configuration in wagmi to minimize redundant calls

**Trade-off decision:** Better UX worth occasional latency

### Account Switching Mid-Flow

**Risk:** User switches wallet after answering questionnaire but before recording score

**Mitigation:**
- Score is already calculated based on original address
- Allow switching but don't recalculate (user intent unclear)
- Could add warning toast if desired in future
- Current implementation: accept new address without warning

**Trade-off decision:** Allow flexibility, add warnings in future if user feedback indicates confusion

## Migration Plan

**Frontend-only change** - No database or backend changes required

**Steps:**
1. Install dependencies
2. Create WalletConnect project
3. Configure providers in App.tsx
4. Update AddressInput.tsx
5. Test thoroughly
6. Deploy to staging
7. Smoke test on staging
8. Deploy to production

**Rollback:** Revert commit and redeploy previous version (no data migration needed)

**Backward compatibility:** Not applicable (new user flow, no existing users)

## Open Questions

**Q: Should we support wallet disconnection mid-flow?**
A: Yes - RainbowKit provides disconnect UI automatically. If user disconnects, they remain on current page with their score already calculated. Only AddressInput page requires active connection.

**Q: Should we show connected wallet address in header across all pages?**
A: Optional enhancement - can add ConnectButton in compact mode to Header component for persistent visibility. Not required for MVP. Recommend adding this as separate follow-up change.

**Q: What happens if user rejects wallet connection?**
A: Stay on AddressInput page. RainbowKit modal closes. User can try again. Add helper text: "Please connect your wallet to continue."

**Q: Should we validate that connected wallet has transaction history?**
A: No - oracle backend handles this. Frontend only captures address. Validation would add latency and complexity.
