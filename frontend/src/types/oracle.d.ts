export interface OracleScoreResponse {
  score: number;
  wallet_address: string;
  signature: string;
  public_key: string;
  timestamp_ms: number;
  metadata?: {
    scoreBreakdown?: {
      activity: number;
      maturity: number;
      diversity: number;
      riskBehavior: number;
      surveyMatch: number;
    };
    reasoning?: string;
    risk_factors?: string[];
    strengths?: string[];
    features?: any;
  };
}
