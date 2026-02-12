import { useCurrentAccount, useCurrentClient } from '@mysten/dapp-kit-react';
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
  const client = useCurrentClient();

  return useQuery({
    queryKey: ['wallet-score', account?.address, evmAddress],
    queryFn: async (): Promise<ParsedWalletScore | null> => {
      if (!account?.address) {
        return null;
      }

      const ownedObjects = await client.core.listOwnedObjects({
        owner: account.address,
        type: `${PACKAGE_ID}::score_oracle::WalletScore`,
        include: {
          json: true,
        },
      });

      if (!ownedObjects.objects || ownedObjects.objects.length === 0) {
        return null;
      }

      const scoreObjects = ownedObjects.objects
        .map((obj) => {
          if (!obj.json) {
            return null;
          }

          const fields = obj.json as any;
          return {
            score: parseInt(fields.score),
            walletAddress: fields.wallet_address,
            timestampMs: parseInt(fields.timestamp_ms),
            version: parseInt(fields.version),
            objectId: obj.objectId,
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
