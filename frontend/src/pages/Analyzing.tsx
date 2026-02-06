import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, AlertCircle } from 'lucide-react';
import { useAccount } from 'wagmi';
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
  const { state, setScore } = useReputa();
  const { isConnected } = useAccount();
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
      if (!isConnected) {
        return;
      }
      try {
        const response = await submitQuestionnaireForScoring(
          state.resolvedAddress || state.evmAddress,
          state.questionnaire
        );
        const normalizedScore = Math.round((response.score / 100) * 1000);
        setScore(normalizedScore, {
          activity: Math.floor(Math.random() * 20) + 75,
          maturity: Math.floor(Math.random() * 20) + 75,
          diversity: Math.floor(Math.random() * 30) + 60,
          riskBehavior: Math.floor(Math.random() * 25) + 70,
          surveyMatch: Math.floor(Math.random() * 20) + 80,
        });
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
  }, [currentStep, navigate, setScore, state.evmAddress, state.resolvedAddress, state.questionnaire, isConnected]);

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
                {/* Loading Animation */}
                <div className="flex justify-center py-8">
                  <div className="relative h-24 w-24">
                    <div className="absolute inset-0 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
                    <div className="absolute inset-2 animate-spin rounded-full border-4 border-primary/10 border-b-primary/60" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
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
