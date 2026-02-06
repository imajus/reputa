import { createNetworkConfig } from '@mysten/dapp-kit';

const { networkConfig, useNetworkVariable, useNetworkVariables } = createNetworkConfig({
  testnet: {
    url: 'https://fullnode.testnet.sui.io',
  },
  mainnet: {
    url: 'https://fullnode.mainnet.sui.io',
  },
});

export { networkConfig, useNetworkVariable, useNetworkVariables };
