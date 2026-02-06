import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface QuestionnaireAnswer {
  question: string;
  answer: string;
  file?: File;
}

interface ScoreBreakdown {
  activity: number;
  maturity: number;
  diversity: number;
  riskBehavior: number;
  surveyMatch: number;
}

interface ReputaState {
  questionnaire: QuestionnaireAnswer[];
  score: number;
  scoreBreakdown: ScoreBreakdown;
  oracleSignature: string;
  oracleTimestamp: number;
  suiAddress: string;
  txHash: string;
}

interface ReputaContextType {
  state: ReputaState;
  updateQuestionnaire: (answers: QuestionnaireAnswer[]) => void;
  setScore: (score: number, breakdown: ScoreBreakdown) => void;
  setOracleData: (signature: string, timestamp: number) => void;
  setSuiAddress: (address: string) => void;
  setTxHash: (hash: string) => void;
  reset: () => void;
}

const initialState: ReputaState = {
  questionnaire: [],
  score: 0,
  scoreBreakdown: {
    activity: 0,
    maturity: 0,
    diversity: 0,
    riskBehavior: 0,
    surveyMatch: 0,
  },
  oracleSignature: '',
  oracleTimestamp: 0,
  suiAddress: '',
  txHash: '',
};

const ReputaContext = createContext<ReputaContextType | undefined>(undefined);

export const ReputaProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ReputaState>(initialState);

  const updateQuestionnaire = (answers: QuestionnaireAnswer[]) => {
    setState(prev => ({ ...prev, questionnaire: answers }));
  };

  const setScore = (score: number, breakdown: ScoreBreakdown) => {
    setState(prev => ({ ...prev, score, scoreBreakdown: breakdown }));
  };

  const setOracleData = (signature: string, timestamp: number) => {
    setState(prev => ({ ...prev, oracleSignature: signature, oracleTimestamp: timestamp }));
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
        updateQuestionnaire,
        setScore,
        setOracleData,
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
