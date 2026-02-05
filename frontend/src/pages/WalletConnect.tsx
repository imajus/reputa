import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wallet, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';
import { useReputa } from '@/contexts/ReputaContext';

const WalletConnect = () => {
  const navigate = useNavigate();
  const { state, setSuiAddress, setTxHash } = useReputa();
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isSigning, setIsSigning] = useState(false);

  const handleConnect = async () => {
    setIsConnecting(true);
    
    // Simulate wallet connection
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setSuiAddress('0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b');
    setIsConnecting(false);
    setIsConnected(true);
  };

  const handleSign = async () => {
    setIsSigning(true);
    
    // Simulate transaction signing
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setTxHash('0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890');
    setIsSigning(false);
    
    navigate('/success');
  };

  const truncateAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={4} />
        
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Record Your Score on Sui</CardTitle>
            <p className="text-muted-foreground">
              {isConnected 
                ? 'Review and sign the transaction to record your score'
                : 'Connect your Sui wallet to record your score on-chain'}
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {!isConnected ? (
              <>
                <Button
                  variant="outline"
                  className="h-16 w-full justify-start gap-4 text-lg"
                  onClick={handleConnect}
                  disabled={isConnecting}
                >
                  {isConnecting ? (
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  ) : (
                    <Wallet className="h-6 w-6 text-primary" />
                  )}
                  <span>{isConnecting ? 'Connecting...' : 'Connect Wallet'}</span>
                </Button>
                
                <p className="text-center text-sm text-muted-foreground">
                  Once connected, you'll sign a transaction to store your score with cryptographic proof.
                </p>
                
                <div className="rounded-lg bg-muted/50 p-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    Gas estimate: <span className="font-medium text-foreground">~0.01 SUI</span>
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-3 rounded-lg border border-primary/50 bg-primary/5 p-4">
                  <Check className="h-5 w-5 text-primary" />
                  <span className="font-medium text-foreground">
                    Connected: {truncateAddress(state.suiAddress)}
                  </span>
                </div>
                
                <div className="space-y-4 rounded-lg border border-border/50 p-4">
                  <h3 className="font-semibold text-foreground">Transaction Preview</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Storing score:</span>
                      <span className="font-medium text-foreground">{state.score}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">TEE signature:</span>
                      <span className="font-mono text-foreground">0x1a2b...3c4d</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gas:</span>
                      <span className="font-medium text-foreground">0.01 SUI</span>
                    </div>
                  </div>
                </div>
                
                <Button 
                  className="w-full" 
                  size="lg"
                  onClick={handleSign}
                  disabled={isSigning}
                >
                  {isSigning ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Signing...
                    </>
                  ) : (
                    'Sign Transaction'
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
