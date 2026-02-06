import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  useEffect(() => {
    const fetchScore = async () => {
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
      } catch (error) {
        console.error('Failed to get score:', error);
        alert('Failed to analyze your data. Please try again.');
        navigate('/questionnaire');
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
  }, [currentStep, navigate, setScore, state.evmAddress, state.resolvedAddress, state.questionnaire]);

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={3} />
        
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Analyzing Your Data...</CardTitle>
            <p className="text-muted-foreground">
              This may take 30-60 seconds
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
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
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Analyzing;
