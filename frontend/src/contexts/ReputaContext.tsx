import React, { createContext, useContext, useState, ReactNode } from 'react';

interface QuestionnaireAnswers {
  experience: string;
  activities: string[];
  riskTolerance: string;
  timeHorizon: string;
  protocols: string[];
  largestPosition: string;
  liquidated: string;
}

interface ScoreBreakdown {
  activity: number;
  maturity: number;
  diversity: number;
  riskBehavior: number;
  surveyMatch: number;
}

interface ReputaState {
  evmAddress: string;
  resolvedAddress: string;
  questionnaire: QuestionnaireAnswers;
  score: number;
  scoreBreakdown: ScoreBreakdown;
  suiAddress: string;
  txHash: string;
}

interface ReputaContextType {
  state: ReputaState;
  setEvmAddress: (address: string) => void;
  setResolvedAddress: (address: string) => void;
  updateQuestionnaire: (answers: Partial<QuestionnaireAnswers>) => void;
  setScore: (score: number, breakdown: ScoreBreakdown) => void;
  setSuiAddress: (address: string) => void;
  setTxHash: (hash: string) => void;
  reset: () => void;
}

const initialState: ReputaState = {
  evmAddress: '',
  resolvedAddress: '',
  questionnaire: {
    experience: '',
    activities: [],
    riskTolerance: '',
    timeHorizon: '',
    protocols: [],
    largestPosition: '',
    liquidated: '',
  },
  score: 0,
  scoreBreakdown: {
    activity: 0,
    maturity: 0,
    diversity: 0,
    riskBehavior: 0,
    surveyMatch: 0,
  },
  suiAddress: '',
  txHash: '',
};

const ReputaContext = createContext<ReputaContextType | undefined>(undefined);

export const ReputaProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ReputaState>(initialState);

  const setEvmAddress = (address: string) => {
    setState(prev => ({ ...prev, evmAddress: address }));
  };

  const setResolvedAddress = (address: string) => {
    setState(prev => ({ ...prev, resolvedAddress: address }));
  };

  const updateQuestionnaire = (answers: Partial<QuestionnaireAnswers>) => {
    setState(prev => ({
      ...prev,
      questionnaire: { ...prev.questionnaire, ...answers },
    }));
  };

  const setScore = (score: number, breakdown: ScoreBreakdown) => {
    setState(prev => ({ ...prev, score, scoreBreakdown: breakdown }));
  };

  const setSuiAddress = (address: string) => {
    setState(prev => ({ ...prev, suiAddress: address }));
  };

  const setTxHash = (hash: string) => {
    setState(prev => ({ ...prev, txHash: hash }));
  };

  const reset = () => {
    setState(initialState);
  };

  return (
    <ReputaContext.Provider
      value={{
        state,
        setEvmAddress,
        setResolvedAddress,
        updateQuestionnaire,
        setScore,
        setSuiAddress,
        setTxHash,
        reset,
      }}
    >
      {children}
    </ReputaContext.Provider>
  );
};

export const useReputa = () => {
  const context = useContext(ReputaContext);
  if (!context) {
    throw new Error('useReputa must be used within a ReputaProvider');
  }
  return context;
};
