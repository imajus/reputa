import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, AlertCircle } from 'lucide-react';
import { useAccount, useEnsName } from 'wagmi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';
import { useReputa } from '@/contexts/ReputaContext';
import { cn } from '@/lib/utils';
import { submitQuestionnaireForScoring } from '@/lib/api';

interface Step {
  id: string;
  label: string;
  duration: number;
}

const steps: Step[] = [
  { id: 'fetch', label: 'Fetching transaction history', duration: 2000 },
  { id: 'analyze', label: 'Analyzing DeFi positions', duration: 2500 },
  { id: 'scoring', label: 'Running AI scoring model', duration: 3000 },
  { id: 'proof', label: 'Generating proof', duration: 2000 },
];

const Analyzing = () => {
  const navigate = useNavigate();
  const { state, setScore, setOracleData } = useReputa();
  const { address, isConnected } = useAccount();
  const { data: ensName } = useEnsName({ address });
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleRetry = () => {
    setError(null);
    setCurrentStep(0);
    setCompletedSteps([]);
  };

  useEffect(() => {
    const fetchScore = async () => {
      if (!isConnected || !address) {
        return;
      }
      try {
        const response = await submitQuestionnaireForScoring(
          ensName || address,
          state.questionnaire
        );
        console.log('Oracle response:', response);
        const scoreBreakdown = response.metadata?.scoreBreakdown || {
          activity: 50,
          maturity: 50,
          diversity: 50,
          riskBehavior: 50,
          surveyMatch: 50
        };
        if (response.metadata?.reasoning) {
          console.log('Score reasoning:', response.metadata.reasoning);
        }
        if (response.metadata?.risk_factors) {
          console.log('Risk factors:', response.metadata.risk_factors);
        }
        if (response.metadata?.strengths) {
          console.log('Strengths:', response.metadata.strengths);
        }
        setOracleData(response.signature, response.timestamp_ms);
        setScore(response.score, scoreBreakdown);
        setTimeout(() => navigate('/score'), 500);
      } catch (err) {
        console.error('Failed to get score:', err);
        setError('Failed to analyze your data. Please try again.');
      }
    };
    if (currentStep >= steps.length) {
      fetchScore();
      return;
    }
    const timer = setTimeout(() => {
      setCompletedSteps(prev => [...prev, steps[currentStep].id]);
      setCurrentStep(prev => prev + 1);
    }, steps[currentStep].duration);
    return () => clearTimeout(timer);
  }, [currentStep, navigate, setScore, setOracleData, state.questionnaire, isConnected, address, ensName]);

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={3} />

        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">
              {error ? 'Analysis Failed' : 'Analyzing Your Data...'}
            </CardTitle>
            <p className="text-muted-foreground">
              {error ? '' : 'This may take 30-60 seconds'}
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {error ? (
              <div className="space-y-6">
                <div className="flex items-center justify-center gap-3 rounded-lg bg-destructive/10 p-6 text-destructive">
                  <AlertCircle className="h-6 w-6" />
                  <p className="text-sm font-medium">{error}</p>
                </div>
                <div className="flex justify-center">
                  <Button onClick={handleRetry} size="lg">
                    Retry
                  </Button>
                </div>
              </div>
            ) : (
              <>
                {/* Loading Animation with Chain Icons */}
                <div className="flex items-center justify-between gap-8 py-12 px-4">
                  {/* Ethereum Side */}
                  <div className="flex flex-col items-center gap-3 animate-float">
                    <img
                      src="/ethereum.png"
                      alt="Ethereum"
                      className="h-16 w-16 object-contain"
                    />
                    <div className="text-sm font-medium text-muted-foreground">
                      {ensName || (address ? address.slice(0, 6) + '...' + address.slice(-4) : '')}
                    </div>
                  </div>

                  {/* Data Transfer Animation */}
                  <div className="flex-1 relative h-2">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-primary/5 rounded-full" />
                    <div className="absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-primary to-transparent rounded-full animate-slide-right" />
                  </div>

                  {/* Sui Side */}
                  <div className="flex flex-col items-center gap-3 animate-float" style={{ animationDelay: '0.5s' }}>
                    <img
                      src="/sui.png"
                      alt="Sui"
                      className="h-16 w-16 object-contain"
                    />
                    <div className="text-sm font-medium text-muted-foreground">
                      Sui Network
                    </div>
                  </div>
                </div>

                {/* Steps */}
                <div className="space-y-3">
                  {steps.map((step, index) => {
                    const isCompleted = completedSteps.includes(step.id);
                    const isCurrent = index === currentStep;
                    const isPending = index > currentStep;

                    return (
                      <div
                        key={step.id}
                        className={cn(
                          'flex items-center gap-3 rounded-lg p-3 transition-all',
                          isCompleted && 'text-foreground',
                          isCurrent && 'bg-primary/5 text-foreground',
                          isPending && 'text-muted-foreground'
                        )}
                      >
                        {isCompleted ? (
                          <Check className="h-5 w-5 text-primary" />
                        ) : isCurrent ? (
                          <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        ) : (
                          <div className="h-5 w-5 rounded-full border-2 border-muted" />
                        )}
                        <span className={cn(isCurrent && 'font-medium')}>
                          {step.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Analyzing;
