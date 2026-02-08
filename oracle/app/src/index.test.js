import { describe, test, expect } from 'vitest';
import { validateAIResponseData } from './validation.js';

describe('Schema Validation', () => {
  test('validates a correct AI response', () => {
    const validResponse = {
      score: 778,
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
      score: 750,
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

  test('rejects score outside valid range', () => {
    const invalidResponse = {
      score: 1200,
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Account shows strong engagement.',
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(invalidResponse);
    expect(result.valid).toBe(false);
  });

  test('rejects breakdown dimension outside 0-100 range', () => {
    const invalidResponse = {
      score: 750,
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
      score: 750,
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
      score: 750,
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

describe('Cross-Validation', () => {
  test('accepts score matching weighted formula', () => {
    const response = {
      score: 778,
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
    const result = validateAIResponseData(response);
    expect(result.valid).toBe(true);
  });

  test('rejects score not matching weighted formula', () => {
    const response = {
      score: 500,
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Account shows strong engagement with consistent repayment behavior.',
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(response);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Cross-validation failed');
  });

  test('accepts score within 2% tolerance', () => {
    const response = {
      score: 765,
      scoreBreakdown: {
        activity: 85,
        maturity: 78,
        diversity: 62,
        riskBehavior: 88,
        surveyMatch: 72
      },
      reasoning: 'Account shows strong engagement with consistent repayment behavior.',
      risk_factors: [],
      strengths: []
    };
    const result = validateAIResponseData(response);
    expect(result.valid).toBe(true);
  });
});

describe('Edge Cases', () => {
  test('validates minimum score', () => {
    const response = {
      score: 0,
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

  test('validates maximum score', () => {
    const response = {
      score: 1000,
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
      score: 500,
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
