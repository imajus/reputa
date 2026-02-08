import { useCurrentAccount, useSuiClient } from '@mysten/dapp-kit';
import { useQuery } from '@tanstack/react-query';

const PACKAGE_ID = import.meta.env.VITE_ORACLE_PACKAGE_ID;

interface ParsedWalletScore {
  score: number;
  walletAddress: string;
  timestampMs: number;
  version: number;
  objectId: string;
}

export function useSuiScore(evmAddress?: string) {
  const account = useCurrentAccount();
  const client = useSuiClient();

  return useQuery({
    queryKey: ['wallet-score', account?.address, evmAddress],
    queryFn: async (): Promise<ParsedWalletScore | null> => {
      if (!account?.address) {
        return null;
      }

      const ownedObjects = await client.getOwnedObjects({
        owner: account.address,
        filter: {
          StructType: `${PACKAGE_ID}::score_oracle::WalletScore`,
        },
        options: {
          showContent: true,
        },
      });

      if (!ownedObjects.data || ownedObjects.data.length === 0) {
        return null;
      }

      const scoreObjects = ownedObjects.data
        .map((obj) => {
          if (!obj.data?.content || obj.data.content.dataType !== 'moveObject') {
            return null;
          }

          const fields = obj.data.content.fields as any;
          return {
            score: parseInt(fields.score),
            walletAddress: fields.wallet_address,
            timestampMs: parseInt(fields.timestamp_ms),
            version: parseInt(fields.version),
            objectId: obj.data.objectId,
          };
        })
        .filter((obj): obj is ParsedWalletScore => obj !== null);

      if (evmAddress) {
        const matchingScore = scoreObjects.find(
          obj => obj.walletAddress.toLowerCase() === evmAddress.toLowerCase()
        );
        return matchingScore || null;
      }

      if (scoreObjects.length === 0) {
        return null;
      }

      scoreObjects.sort((a, b) => b.timestampMs - a.timestampMs);
      return scoreObjects[0];
    },
    enabled: !!account?.address,
    staleTime: 30000,
  });
}
