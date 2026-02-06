import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lightbulb } from 'lucide-react';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount } from 'wagmi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';

const AddressInput = () => {
  const navigate = useNavigate();
  const { address, isConnected } = useAccount();

  useEffect(() => {
    if (isConnected && address) {
      navigate('/questionnaire');
    }
  }, [isConnected, address, navigate]);

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={1} />

        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Connect Your Wallet</CardTitle>
            <p className="text-muted-foreground">
              We'll analyze your on-chain history from Ethereum and L2s
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex justify-center">
              <ConnectButton />
            </div>

            <div className="flex items-start gap-3 rounded-lg bg-primary/5 p-4">
              <Lightbulb className="h-5 w-5 shrink-0 text-primary" />
              <p className="text-sm text-muted-foreground">
                We'll analyze your transaction history across Ethereum, Arbitrum, Optimism, and other major L2s to build your reputation score.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default AddressInput;
