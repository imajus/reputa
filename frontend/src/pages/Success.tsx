import { Link } from 'react-router-dom';
import { CheckCircle2, ExternalLink, Share2, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import Layout from '@/components/layout/Layout';
import { useReputa } from '@/contexts/ReputaContext';

const Success = () => {
  const { state } = useReputa();
  
  const truncateAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardContent className="space-y-8 py-12 text-center">
            {/* Success Icon */}
            <div className="flex justify-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                <CheckCircle2 className="h-12 w-12 text-primary" />
              </div>
            </div>
            
            <div>
              <h1 className="mb-2 text-3xl font-bold text-foreground">Score Recorded!</h1>
              <p className="text-muted-foreground">
                Your Reputa score is now on-chain and ready to use across Sui DeFi
              </p>
            </div>
            
            {/* Summary */}
            <div className="mx-auto max-w-sm space-y-3 rounded-lg border border-border/50 p-4 text-left">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Score:</span>
                <span className="font-semibold text-foreground">{state.score}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Address:</span>
                <span className="font-mono text-foreground">{truncateAddress(state.suiAddress || '0x1a2b3c4d5e6f7a8b')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tx Hash:</span>
                <span className="font-mono text-foreground">{truncateAddress(state.txHash || '0xabcdef1234567890')}</span>
              </div>
            </div>
            
            {/* CTA */}
            <div className="space-y-4">
              <p className="text-sm font-medium text-foreground">Next Steps</p>
              <Card className="border-primary/50 bg-primary/5">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="text-left">
                    <p className="font-medium text-foreground">Try Demo Protocol</p>
                    <p className="text-sm text-muted-foreground">See your score in action</p>
                  </div>
                  <Button asChild>
                    <Link to="/demo">
                      Try it
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </div>
            
            {/* Actions */}
            <div className="flex justify-center gap-4">
              <Button variant="outline" size="sm">
                <ExternalLink className="mr-2 h-4 w-4" />
                View on Explorer
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="mr-2 h-4 w-4" />
                Share Score
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Success;
