import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';
import { useReputa } from '@/contexts/ReputaContext';

interface Question {
  id: string;
  question: string;
  type: 'radio' | 'checkbox';
  options: { value: string; label: string }[];
}

const questions: Question[] = [
  {
    id: 'experience',
    question: 'How long have you been active in DeFi?',
    type: 'radio',
    options: [
      { value: 'less_6mo', label: 'Less than 6 months' },
      { value: '6mo_1yr', label: '6 months - 1 year' },
      { value: '1_3yr', label: '1-3 years' },
      { value: '3yr_plus', label: '3+ years' },
    ],
  },
  {
    id: 'activities',
    question: 'What are your primary DeFi activities?',
    type: 'checkbox',
    options: [
      { value: 'lending', label: 'Lending' },
      { value: 'liquidity', label: 'Liquidity Provision' },
      { value: 'trading', label: 'Trading' },
      { value: 'yield_farming', label: 'Yield Farming' },
      { value: 'other', label: 'Other' },
    ],
  },
  {
    id: 'riskTolerance',
    question: 'What is your risk tolerance?',
    type: 'radio',
    options: [
      { value: 'conservative', label: 'Conservative' },
      { value: 'moderate', label: 'Moderate' },
      { value: 'aggressive', label: 'Aggressive' },
    ],
  },
  {
    id: 'timeHorizon',
    question: 'What is your typical investment time horizon?',
    type: 'radio',
    options: [
      { value: 'less_1mo', label: 'Less than 1 month' },
      { value: '1_6mo', label: '1-6 months' },
      { value: '6mo_1yr', label: '6 months - 1 year' },
      { value: '1yr_plus', label: '1+ years' },
    ],
  },
  {
    id: 'protocols',
    question: 'Which protocols have you used?',
    type: 'checkbox',
    options: [
      { value: 'aave', label: 'Aave' },
      { value: 'compound', label: 'Compound' },
      { value: 'uniswap', label: 'Uniswap' },
      { value: 'curve', label: 'Curve' },
      { value: 'none', label: 'None of these' },
    ],
  },
  {
    id: 'largestPosition',
    question: 'What was the largest position you\'ve managed?',
    type: 'radio',
    options: [
      { value: 'less_1k', label: 'Less than $1,000' },
      { value: '1k_10k', label: '$1,000 - $10,000' },
      { value: '10k_100k', label: '$10,000 - $100,000' },
      { value: '100k_plus', label: '$100,000+' },
    ],
  },
  {
    id: 'liquidated',
    question: 'Have you ever been liquidated?',
    type: 'radio',
    options: [
      { value: 'never', label: 'Never' },
      { value: 'once', label: 'Once' },
      { value: 'multiple', label: 'Multiple times' },
    ],
  },
];

const Questionnaire = () => {
  const navigate = useNavigate();
  const { updateQuestionnaire } = useReputa();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});

  const question = questions[currentQuestion];
  const isLastQuestion = currentQuestion === questions.length - 1;
  const currentAnswer = answers[question.id];
  
  const isAnswered = question.type === 'radio' 
    ? !!currentAnswer 
    : Array.isArray(currentAnswer) && currentAnswer.length > 0;

  const handleRadioChange = (value: string) => {
    setAnswers(prev => ({ ...prev, [question.id]: value }));
  };

  const handleCheckboxChange = (value: string, checked: boolean) => {
    const current = (answers[question.id] as string[]) || [];
    const updated = checked 
      ? [...current, value]
      : current.filter(v => v !== value);
    setAnswers(prev => ({ ...prev, [question.id]: updated }));
  };

  const handleNext = () => {
    if (isLastQuestion) {
      // Convert answers to questionnaire format
      updateQuestionnaire({
        experience: answers.experience as string,
        activities: answers.activities as string[],
        riskTolerance: answers.riskTolerance as string,
        timeHorizon: answers.timeHorizon as string,
        protocols: answers.protocols as string[],
        largestPosition: answers.largestPosition as string,
        liquidated: answers.liquidated as string,
      });
      navigate('/analyzing');
    } else {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentQuestion === 0) {
      navigate('/analyze');
    } else {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={2} />
        
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <p className="text-sm text-muted-foreground">
              Question {currentQuestion + 1} of {questions.length}
            </p>
            <CardTitle className="text-2xl">{question.question}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {question.type === 'radio' ? (
              <RadioGroup
                value={(currentAnswer as string) || ''}
                onValueChange={handleRadioChange}
                className="space-y-3"
              >
                {question.options.map(option => (
                  <div
                    key={option.value}
                    className="flex items-center space-x-3 rounded-lg border border-border/50 p-4 transition-colors hover:border-primary/50 has-[:checked]:border-primary has-[:checked]:bg-primary/5"
                  >
                    <RadioGroupItem value={option.value} id={option.value} />
                    <Label htmlFor={option.value} className="flex-1 cursor-pointer">
                      {option.label}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            ) : (
              <div className="space-y-3">
                {question.options.map(option => {
                  const checked = ((currentAnswer as string[]) || []).includes(option.value);
                  return (
                    <div
                      key={option.value}
                      className={`flex items-center space-x-3 rounded-lg border border-border/50 p-4 transition-colors hover:border-primary/50 ${checked ? 'border-primary bg-primary/5' : ''}`}
                    >
                      <Checkbox
                        id={option.value}
                        checked={checked}
                        onCheckedChange={(checked) => handleCheckboxChange(option.value, !!checked)}
                      />
                      <Label htmlFor={option.value} className="flex-1 cursor-pointer">
                        {option.label}
                      </Label>
                    </div>
                  );
                })}
              </div>
            )}
            
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNext} disabled={!isAnswered}>
                {isLastQuestion ? 'Submit' : 'Next'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Questionnaire;
