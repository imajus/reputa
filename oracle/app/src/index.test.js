import { describe, test, expect } from 'vitest';
import { validateAIResponseData, calculateTotalScore } from './validation.js';

describe('Schema Validation', () => {
  test('validates a correct AI response', () => {
    const validResponse = {
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Account shows strong engagement with consistent repayment behavior.',
      risk_factors: ['High token concentration'],
      strengths: ['Consistent repayment history']
    };
    const result = validateAIResponseData(validResponse);
    expect(result.valid).toBe(true);
  });

  test('rejects response missing required field', () => {
    const invalidResponse = {
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Valid reasoning text here.'
    };
    const result = validateAIResponseData(invalidResponse);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Schema validation failed');
  });

  test('rejects breakdown dimension outside 0-100 range', () => {
    const invalidResponse = {
      scoreBreakdown: {
        activity: 150,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Valid reasoning text.',
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(invalidResponse);
    expect(result.valid).toBe(false);
  });

  test('rejects reasoning too short', () => {
    const invalidResponse = {
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Too short',
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(invalidResponse);
    expect(result.valid).toBe(false);
  });

  test('rejects reasoning too long', () => {
    const longReasoning = 'x'.repeat(501);
    const invalidResponse = {
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: longReasoning,
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(invalidResponse);
    expect(result.valid).toBe(false);
  });
});

describe('Score Calculation', () => {
  test('calculates correct total score from breakdown', () => {
    const breakdown = {
      activity: 85,
      maturity: 78,
      diversity: 62,
      riskBehavior: 88,
      surveyMatch: 72
    };
    const score = calculateTotalScore(breakdown);
    expect(score).toBe(778);
  });

  test('calculates minimum score', () => {
    const breakdown = {
      activity: 0,
      maturity: 0,
      diversity: 0,
      riskBehavior: 0,
      surveyMatch: 0
    };
    const score = calculateTotalScore(breakdown);
    expect(score).toBe(0);
  });

  test('calculates maximum score', () => {
    const breakdown = {
      activity: 100,
      maturity: 100,
      diversity: 100,
      riskBehavior: 100,
      surveyMatch: 100
    };
    const score = calculateTotalScore(breakdown);
    expect(score).toBe(1000);
  });

  test('applies correct weights to each dimension', () => {
    const breakdown = {
      activity: 100,
      maturity: 0,
      diversity: 0,
      riskBehavior: 0,
      surveyMatch: 0
    };
    expect(calculateTotalScore(breakdown)).toBe(200);
    expect(calculateTotalScore({ ...breakdown, activity: 0, maturity: 100 })).toBe(200);
    expect(calculateTotalScore({ ...breakdown, activity: 0, diversity: 100 })).toBe(200);
    expect(calculateTotalScore({ ...breakdown, activity: 0, riskBehavior: 100 })).toBe(250);
    expect(calculateTotalScore({ ...breakdown, activity: 0, surveyMatch: 100 })).toBe(150);
  });

  test('rounds score to nearest integer', () => {
    const breakdown = {
      activity: 33,
      maturity: 33,
      diversity: 33,
      riskBehavior: 33,
      surveyMatch: 33
    };
    const score = calculateTotalScore(breakdown);
    expect(Number.isInteger(score)).toBe(true);
    expect(score).toBe(330);
  });
});

describe('Edge Cases', () => {
  test('validates minimum breakdown', () => {
    const response = {
      scoreBreakdown: {
        activity: 0,
        maturity: 0,
        diversity: 0,
        riskBehavior: 0,
        surveyMatch: 0
      },
      reasoning: 'Completely inactive wallet with no transaction history.',
      risk_factors: ['No activity'],
      strengths: []
    };
    const result = validateAIResponseData(response);
    expect(result.valid).toBe(true);
  });

  test('validates maximum breakdown', () => {
    const response = {
      scoreBreakdown: {
        activity: 100,
        maturity: 100,
        diversity: 100,
        riskBehavior: 100,
        surveyMatch: 100
      },
      reasoning: 'Perfect DeFi track record with exceptional engagement and financial health.',
      risk_factors: [],
      strengths: ['Perfect repayment history', 'High diversification']
    };
    const result = validateAIResponseData(response);
    expect(result.valid).toBe(true);
  });

  test('validates empty arrays for risk_factors and strengths', () => {
    const response = {
      scoreBreakdown: {
        activity: 50,
        maturity: 50,
        diversity: 50,
        riskBehavior: 50,
        surveyMatch: 50
      },
      reasoning: 'Average wallet with no standout features or issues.',
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(response);
    expect(result.valid).toBe(true);
  });
});
