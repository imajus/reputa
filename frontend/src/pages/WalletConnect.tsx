import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Loader2, AlertCircle } from "lucide-react";
import {
  ConnectButton,
  useCurrentAccount,
  useSignAndExecuteTransaction,
} from "@mysten/dapp-kit";
import { Transaction } from "@mysten/sui/transactions";
import { bcs } from "@mysten/sui/bcs";
import { useAccount } from "wagmi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import Layout from "@/components/layout/Layout";
import ProgressIndicator from "@/components/layout/ProgressIndicator";
import { useReputa } from "@/contexts/ReputaContext";
import { hexToUint8Array } from "@/lib/oracleService";

const PACKAGE_ID = import.meta.env.VITE_ORACLE_PACKAGE_ID;
const REGISTRY_OBJECT_ID = import.meta.env.VITE_REGISTRY_OBJECT_ID;
const ENCLAVE_OBJECT_ID = import.meta.env.VITE_ENCLAVE_OBJECT_ID;

const WalletConnect = () => {
  const navigate = useNavigate();
  const { state, setSuiAddress, setTxHash } = useReputa();
  const { address } = useAccount();
  const currentAccount = useCurrentAccount();
  const {
    mutate: signAndExecute,
    isPending,
    error,
  } = useSignAndExecuteTransaction();
  const [txError, setTxError] = useState<string | null>(null);

  useEffect(() => {
    if (!state.score || !state.oracleSignature) {
      navigate("/analyze");
    }
  }, [state.score, state.oracleSignature, navigate]);

  useEffect(() => {
    if (currentAccount?.address) {
      setSuiAddress(currentAccount.address);
    }
  }, [currentAccount, setSuiAddress]);

  const handleSign = async () => {
    if (!currentAccount || !address) return;
    setTxError(null);
    try {
      const walletAddressBytes = new TextEncoder().encode(address);
      const signatureBytes = hexToUint8Array(state.oracleSignature);
      const tx = new Transaction();
      tx.moveCall({
        target: `${PACKAGE_ID}::score_oracle::update_wallet_score`,
        arguments: [
          tx.object(REGISTRY_OBJECT_ID),
          tx.object(ENCLAVE_OBJECT_ID),
          tx.pure.u64(state.score),
          tx.pure(
            bcs.vector(bcs.u8()).serialize(Array.from(walletAddressBytes)),
          ),
          tx.pure.u64(state.oracleTimestamp),
          tx.pure(bcs.vector(bcs.u8()).serialize(Array.from(signatureBytes))),
        ],
      });
      signAndExecute(
        { transaction: tx },
        {
          onSuccess: (result) => {
            console.log("Transaction successful:", result);
            setTxHash(result.digest);
            setTimeout(() => navigate("/success"), 1000);
          },
          onError: (err) => {
            console.error("Transaction error:", err);
            setTxError(err.message || "Transaction failed");
          },
        },
      );
    } catch (err: any) {
      console.error("Failed to build transaction:", err);
      setTxError(err.message || "Failed to build transaction");
    }
  };

  const truncateAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  const truncateSignature = (sig: string) => {
    return `${sig.slice(0, 6)}...${sig.slice(-4)}`;
  };

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={3} />

        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Record Your Score on Sui</CardTitle>
            <p className="text-muted-foreground">
              {currentAccount
                ? "Review and sign the transaction to record your score"
                : "Connect your Sui wallet to record your score on-chain"}
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {!currentAccount ? (
              <>
                <div className="flex justify-center">
                  <ConnectButton />
                </div>

                <p className="text-center text-sm text-muted-foreground">
                  Once connected, you'll sign a transaction to store your score
                  with cryptographic proof.
                </p>

                <div className="rounded-lg bg-muted/50 p-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    Gas estimate:{" "}
                    <span className="font-medium text-foreground">
                      ~0.01 SUI
                    </span>
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-3 rounded-lg border border-primary/50 bg-primary/5 p-4">
                  <Check className="h-5 w-5 text-primary" />
                  <span className="font-medium text-foreground">
                    Connected: {truncateAddress(currentAccount.address)}
                  </span>
                </div>

                {(txError || error) && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {txError || error?.message || "Transaction failed"}
                    </AlertDescription>
                  </Alert>
                )}

                <div className="space-y-4 rounded-lg border border-border/50 p-4">
                  <h3 className="font-semibold text-foreground">
                    Transaction Preview
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        Storing score:
                      </span>
                      <span className="font-medium text-foreground">
                        {state.score}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        TEE signature:
                      </span>
                      <span className="font-mono text-foreground">
                        {truncateSignature(state.oracleSignature)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gas:</span>
                      <span className="font-medium text-foreground">
                        ~0.01 SUI
                      </span>
                    </div>
                  </div>
                </div>

                <Button
                  className="w-full"
                  size="lg"
                  onClick={handleSign}
                  disabled={isPending}
                >
                  {isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Signing...
                    </>
                  ) : (
                    "Sign Transaction"
                  )}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default WalletConnect;
