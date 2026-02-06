import { useNavigate } from 'react-router-dom';
import { ArrowRight, Award, TrendingUp, Shield, Layers, Target } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';
import { useReputa } from '@/contexts/ReputaContext';
import { cn } from '@/lib/utils';

const ScoreReview = () => {
  const navigate = useNavigate();
  const { state } = useReputa();
  const { score, scoreBreakdown } = state;

  const getTier = (score: number) => {
    if (score >= 800) return { name: 'Premium', color: 'text-primary', bg: 'bg-primary/10' };
    if (score >= 600) return { name: 'Standard', color: 'text-chart-3', bg: 'bg-chart-3/10' };
    return { name: 'Basic', color: 'text-muted-foreground', bg: 'bg-muted/50' };
  };

  const tier = getTier(score);
  const scorePercent = (score / 1000) * 100;

  const breakdownItems = [
    { label: 'Transaction Activity', value: scoreBreakdown.activity, icon: TrendingUp },
    { label: 'Account Maturity', value: scoreBreakdown.maturity, icon: Award },
    { label: 'Protocol & Token Diversity', value: scoreBreakdown.diversity, icon: Layers },
    { label: 'Financial Health', value: scoreBreakdown.riskBehavior, icon: Shield },
    { label: 'Intent Alignment', value: scoreBreakdown.surveyMatch, icon: Target },
  ];

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={3} />
        
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Your Reputa Score</CardTitle>
          </CardHeader>
          <CardContent className="space-y-8">
            {/* Score Display */}
            <div className="flex flex-col items-center py-6">
              <div className="relative mb-4">
                {/* Semi-circle gauge */}
                <svg className="h-40 w-80" viewBox="0 0 200 100">
                  {/* Background arc */}
                  <path
                    d="M 10 100 A 90 90 0 0 1 190 100"
                    fill="none"
                    stroke="hsl(var(--muted))"
                    strokeWidth="12"
                    strokeLinecap="round"
                  />
                  {/* Score arc */}
                  <path
                    d="M 10 100 A 90 90 0 0 1 190 100"
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="12"
                    strokeLinecap="round"
                    strokeDasharray={`${scorePercent * 2.83} 283`}
                    className="transition-all duration-1000"
                  />
                </svg>
                {/* Score number */}
                <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
                  <span className="text-5xl font-bold text-foreground">{score}</span>
                  <span className="text-muted-foreground">/ 1000</span>
                </div>
              </div>
              
              {/* Tier badge */}
              <div className={cn('rounded-full px-4 py-1.5 text-sm font-medium', tier.bg, tier.color)}>
                {tier.name} Tier
              </div>
            </div>
            
            {/* Score Breakdown */}
            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Score Breakdown</h3>
              <div className="space-y-3">
                {breakdownItems.map((item) => (
                  <div key={item.label} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <item.icon className="h-4 w-4 text-muted-foreground" />
                        <span className="text-foreground">{item.label}</span>
                      </div>
                      <span className="font-medium text-foreground">{item.value}/100</span>
                    </div>
                    <Progress value={item.value} className="h-2" />
                  </div>
                ))}
              </div>
            </div>
            
            {/* What This Means */}
            <div className="rounded-lg bg-primary/5 p-4">
              <p className="text-sm text-muted-foreground">
                <strong className="text-foreground">What This Means:</strong> You qualify for {tier.name} tier benefits on Sui protocols, including enhanced APY rates and priority access to new features.
              </p>
            </div>
            
            <Button className="w-full" size="lg" onClick={() => navigate('/record')}>
              Record Score on Sui
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default ScoreReview;
