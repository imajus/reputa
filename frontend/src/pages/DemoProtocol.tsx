import { Sparkles, Info, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Layout from '@/components/layout/Layout';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useSuiScore } from '@/hooks/useSuiScore';
import { useAccount } from 'wagmi';

const tiers = [
  { name: 'Premium', minScore: 800, bonus: 2.0, apy: 7.0 },
  { name: 'Standard', minScore: 600, bonus: 1.0, apy: 6.0 },
  { name: 'Basic', minScore: 0, bonus: 0, apy: 5.0 },
];

const DemoProtocol = () => {
  const navigate = useNavigate();
  const { address: evmAddress } = useAccount();

  const { data: onChainScore, isLoading } = useSuiScore(evmAddress);

  const hasScore = onChainScore !== null && onChainScore !== undefined;
  const score = onChainScore?.score ?? null;
  const currentTier = hasScore ? (tiers.find(t => score >= t.minScore) || tiers[2]) : null;
  const baseApy = 5.0;
  const bonusApy = currentTier?.bonus ?? 0;
  const totalApy = baseApy + bonusApy;

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Reputa Demo Yield Protocol</CardTitle>
            <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm">
              <span className="text-muted-foreground">Your Tier:</span>
              <span className="font-semibold text-primary">
                {hasScore && currentTier ? currentTier.name : 'N/A'}
              </span>
              <span className="text-muted-foreground">
                (Score: {hasScore ? score : 'N/A'})
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {isLoading && (
              <Alert>
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>
                  Loading your on-chain reputation score...
                </AlertDescription>
              </Alert>
            )}

            {!isLoading && !hasScore && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="flex items-center justify-between">
                  <span>
                    Complete the reputation scoring flow to see your personalized tier and APY bonus.
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate('/analyze')}
                    className="ml-2"
                  >
                    Get Score <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {/* APY Display */}
            <Card className="border-primary/50 bg-card">
              <CardContent className="p-6 text-center">
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-2 text-muted-foreground">
                    <span>Base APY:</span>
                    <span className="font-medium text-foreground">{baseApy.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-primary">
                    <Sparkles className="h-4 w-4" />
                    <span>Your Bonus:</span>
                    <span className="font-medium">
                      {hasScore ? `+${bonusApy.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <Separator className="my-2" />
                  <div className="text-2xl font-bold text-foreground">
                    Total APY: {hasScore ? `${totalApy.toFixed(1)}%` : 'N/A'}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tier Comparison */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-foreground">APY Tier Reference</h3>
              <p className="text-sm text-muted-foreground">
                Higher reputation scores unlock better APY rates across integrated DeFi protocols.
              </p>
              <div className="space-y-2">
                {tiers.map((tier) => (
                  <div
                    key={tier.name}
                    className={cn(
                      'flex items-center justify-between rounded-lg border p-3 transition-all',
                      tier.name === currentTier?.name
                        ? 'border-primary bg-primary/5'
                        : 'border-border/50'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        'font-medium',
                        tier.name === currentTier?.name ? 'text-primary' : 'text-foreground'
                      )}>
                        {tier.name}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        ({tier.minScore}+)
                      </span>
                    </div>
                    <span className={cn(
                      'font-semibold',
                      tier.name === currentTier?.name ? 'text-primary' : 'text-foreground'
                    )}>
                      {tier.apy.toFixed(1)}% APY
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default DemoProtocol;
