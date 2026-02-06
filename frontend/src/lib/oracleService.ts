import type { OracleScoreResponse } from '@/types/oracle';

const ORACLE_API_URL = import.meta.env.VITE_ORACLE_API_URL || 'http://localhost:3000';

export async function fetchScoreFromOracle(
  address: string,
  questionnaire?: Array<{ question: string; answer: string }>
): Promise<OracleScoreResponse> {
  const url = questionnaire
    ? `${ORACLE_API_URL}/score`
    : `${ORACLE_API_URL}/score?address=${address}`;
  const options: RequestInit = {
    headers: {
      'Accept': 'application/json',
      ...(questionnaire && { 'Content-Type': 'application/json' }),
    },
  };
  if (questionnaire) {
    options.method = 'POST';
    options.body = JSON.stringify({ address, questionnaire });
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Oracle API error: ${response.status} ${errorBody}`);
  }
  const data = await response.json();
  if (
    typeof data.score !== 'number' ||
    typeof data.signature !== 'string' ||
    typeof data.wallet_address !== 'string'
  ) {
    throw new Error('Invalid oracle response format');
  }
  return data;
}

export function hexToUint8Array(hex: string): Uint8Array {
  const cleaned = hex.startsWith('0x') ? hex.slice(2) : hex;
  const bytes = new Uint8Array(cleaned.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(cleaned.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}
