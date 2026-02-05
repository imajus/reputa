import { useState } from 'react';
import { Sparkles, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import Layout from '@/components/layout/Layout';
import { useReputa } from '@/contexts/ReputaContext';
import { cn } from '@/lib/utils';

const tiers = [
  { name: 'Premium', minScore: 800, bonus: 2.0, apy: 7.0 },
  { name: 'Standard', minScore: 600, bonus: 1.0, apy: 6.0 },
  { name: 'Basic', minScore: 0, bonus: 0, apy: 5.0 },
];

const DemoProtocol = () => {
  const { state } = useReputa();
  const [depositAmount, setDepositAmount] = useState('100');
  
  const score = state.score || 782;
  const currentTier = tiers.find(t => score >= t.minScore) || tiers[2];
  const baseApy = 5.0;
  const bonusApy = currentTier.bonus;
  const totalApy = baseApy + bonusApy;
  
  const yearlyEarnings = parseFloat(depositAmount || '0') * (totalApy / 100);

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Reputa Demo Yield Protocol</CardTitle>
            <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm">
              <span className="text-muted-foreground">Your Tier:</span>
              <span className="font-semibold text-primary">{currentTier.name}</span>
              <span className="text-muted-foreground">(Score: {score})</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
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
                    <span className="font-medium">+{bonusApy.toFixed(1)}%</span>
                  </div>
                  <Separator className="my-2" />
                  <div className="text-2xl font-bold text-foreground">
                    Total APY: {totalApy.toFixed(1)}%
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Deposit Form */}
            <div className="space-y-4">
              <label className="text-sm font-medium text-foreground">Deposit Amount</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    type="number"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    className="pr-16"
                    placeholder="0"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    SUI
                  </span>
                </div>
                <Button variant="outline" onClick={() => setDepositAmount('1000')}>
                  Max
                </Button>
              </div>
              
              <div className="flex items-center gap-2 rounded-lg bg-primary/5 p-3">
                <Info className="h-4 w-4 text-primary" />
                <span className="text-sm text-muted-foreground">
                  You'll earn: <span className="font-medium text-foreground">~{yearlyEarnings.toFixed(2)} SUI/year</span>
                </span>
              </div>
              
              <Button className="w-full" size="lg">
                Deposit Now
              </Button>
            </div>
            
            {/* Tier Comparison */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-foreground">Tier Comparison</h3>
              <div className="space-y-2">
                {tiers.map((tier) => (
                  <div
                    key={tier.name}
                    className={cn(
                      'flex items-center justify-between rounded-lg border p-3 transition-all',
                      tier.name === currentTier.name
                        ? 'border-primary bg-primary/5'
                        : 'border-border/50'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        'font-medium',
                        tier.name === currentTier.name ? 'text-primary' : 'text-foreground'
                      )}>
                        {tier.name}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        ({tier.minScore}+)
                      </span>
                    </div>
                    <span className={cn(
                      'font-semibold',
                      tier.name === currentTier.name ? 'text-primary' : 'text-foreground'
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
