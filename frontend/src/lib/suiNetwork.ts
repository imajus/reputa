import { createNetworkConfig } from '@mysten/dapp-kit';

const { networkConfig, useNetworkVariable, useNetworkVariables } = createNetworkConfig({
  testnet: {
    url: 'https://fullnode.testnet.sui.io',
    network: 'testnet'
  }
});

export { networkConfig, useNetworkVariable, useNetworkVariables };
