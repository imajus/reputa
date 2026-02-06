import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { FileUploadButton } from '@/components/ui/file-upload';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';
import { useReputa, QuestionnaireAnswer } from '@/contexts/ReputaContext';

interface Question {
  id: string;
  question: string;
  type: 'text' | 'file';
  placeholder: string;
}

const questions: Question[] = [
  {
    id: 'walletControl',
    question: 'Who is this wallet controlled by?',
    type: 'text',
    placeholder: 'e.g., individual, DAO, multisig, legal entity, smart contract protocol, custodian/exchange, other'
  },
  {
    id: 'loanUse',
    question: 'What is the intended use of loan proceeds?',
    type: 'text',
    placeholder: 'e.g., growth, working capital, investment, refinancing, treasury management, bridge financing, other'
  },
  {
    id: 'cashFlowGeneration',
    question: 'Will this loan generate incremental cash flow, and how?',
    type: 'text',
    placeholder: 'e.g., new revenue, balance-sheet reshuffling, liquidity mining/yield farming, arbitrage/market making, cost reduction, debt service coverage, other'
  },
  {
    id: 'offchainRevenue',
    question: 'Please provide details of any off-chain revenue or cash flow streams',
    type: 'text',
    placeholder: 'Describe any business operations, revenue sources, or cash flow streams outside of blockchain activity...'
  },
  {
    id: 'offchainLiabilities',
    question: 'List any material off-chain liabilities or guarantees not visible on-chain?',
    type: 'file',
    placeholder: 'Detail any existing debts, obligations, guarantees, or commitments not visible on-chain...'
  },
  {
    id: 'beneficiaryOwner',
    question: 'Who is the ultimate beneficiary owner of the borrowing wallet, and how is authority constrained?',
    type: 'text',
    placeholder: 'e.g., "John Doe, CEO with board approval required for debts >$100K"'
  }
];

const Questionnaire = () => {
  const navigate = useNavigate();
  const { updateQuestionnaire } = useReputa();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<QuestionnaireAnswer[]>(
    questions.map(q => ({ question: q.question, answer: '' }))
  );
  const question = questions[currentQuestion];
  const isLastQuestion = currentQuestion === questions.length - 1;
  const currentAnswer = answers[currentQuestion];
  const extractSuggestions = (placeholder: string): string[] => {
    const match = placeholder.match(/e\.g\.,\s*(.+)/);
    if (!match) return [];
    return match[1].split(',').map(s => s.trim());
  };
  const suggestions = extractSuggestions(question.placeholder);
  const handleTextChange = (value: string) => {
    setAnswers(prev => {
      const updated = [...prev];
      updated[currentQuestion] = { ...updated[currentQuestion], answer: value };
      return updated;
    });
  };
  const handleSuggestionClick = (suggestion: string) => {
    handleTextChange(suggestion);
  };
  const handleFileChange = (file: File) => {
    setAnswers(prev => {
      const updated = [...prev];
      updated[currentQuestion] = { ...updated[currentQuestion], file };
      return updated;
    });
  };
  const handleFileReset = () => {
    setAnswers(prev => {
      const updated = [...prev];
      updated[currentQuestion] = { ...updated[currentQuestion], file: undefined };
      return updated;
    });
  };
  const handleNext = () => {
    if (isLastQuestion) {
      updateQuestionnaire(answers);
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
            <div className="space-y-4">
              <Textarea
                value={currentAnswer.answer}
                onChange={(e) => handleTextChange(e.target.value)}
                placeholder={question.placeholder}
                className="min-h-[120px] resize-none placeholder:text-muted-foreground/30"
              />
              {suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-xs text-primary/70 hover:text-primary hover:underline"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
              {question.type === 'file' && (
                <FileUploadButton
                  onChange={handleFileChange}
                  file={currentAnswer.file}
                  onReset={handleFileReset}
                />
              )}
            </div>
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={handleNext}>
                  Skip
                </Button>
                <Button onClick={handleNext}>
                  {isLastQuestion ? 'Submit' : 'Next'}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        <p className="mt-4 text-center text-xs text-muted-foreground/60">
          Your answers will be processed privately and will not be uploaded to blockchain or any third-parties.
        </p>
      </div>
    </Layout>
  );
};

export default Questionnaire;
