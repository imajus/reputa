import { QuestionnaireAnswer } from '@/contexts/ReputaContext';

interface ScoreResponse {
  score: number;
  wallet_address: string;
  timestamp_ms: number;
  signature: string;
}

export const submitQuestionnaireForScoring = async (
  address: string,
  questionnaire: QuestionnaireAnswer[]
): Promise<ScoreResponse> => {
  const apiUrl = import.meta.env.VITE_ORACLE_API_URL || 'http://localhost:3000';
  const requestBody = {
    address,
    questionnaire: questionnaire.map(({ question, answer }) => ({
      question,
      answer
    }))
  };
  const response = await fetch(`${apiUrl}/score`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });
  if (!response.ok) {
    throw new Error(`Failed to get score: ${response.statusText}`);
  }
  return response.json();
};
