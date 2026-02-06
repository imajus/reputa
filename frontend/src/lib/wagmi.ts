import { getDefaultConfig } from '@rainbow-me/rainbowkit';
import { mainnet, optimism, arbitrum, base, polygon } from 'wagmi/chains';

const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID;

if (!projectId) {
  console.warn('VITE_WALLETCONNECT_PROJECT_ID is not set. WalletConnect will not be available.');
}

export const config = getDefaultConfig({
  appName: 'Reputa',
  projectId: projectId || '',
  chains: [mainnet, optimism, arbitrum, base, polygon],
  ssr: false,
});
