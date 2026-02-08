import Ajv from 'ajv';

/**
 * AI Response JSON Schema
 * Defines expected structure, types, and ranges for AI-generated breakdown
 */
export const reponseSchema = Object.freeze({
  type: 'object',
  properties: {
    scoreBreakdown: {
      type: 'object',
      properties: {
        activity: { type: 'integer', minimum: 0, maximum: 100 },
        maturity: { type: 'integer', minimum: 0, maximum: 100 },
        diversity: { type: 'integer', minimum: 0, maximum: 100 },
        riskBehavior: { type: 'integer', minimum: 0, maximum: 100 },
        surveyMatch: { type: 'integer', minimum: 0, maximum: 100 }
      },
      required: ['activity', 'maturity', 'diversity', 'riskBehavior', 'surveyMatch']
    },
    reasoning: { type: 'string', minLength: 10, maxLength: 500 },
    risk_factors: { type: 'array', items: { type: 'string' } },
    strengths: { type: 'array', items: { type: 'string' } }
  },
  required: ['scoreBreakdown', 'reasoning', 'risk_factors', 'strengths']
});

const ajv = new Ajv();
const validateAIResponse = ajv.compile(reponseSchema);

/**
 * Validate AI response against schema
 *
 * @param {Object} analysis - AI response object to validate
 * @returns {Object} Validation result: { valid: boolean, error?: string, details?: Object }
 */
export function validateAIResponseData(analysis) {
  const isValid = validateAIResponse(analysis);
  if (!isValid) {
    console.error('Schema validation failed:', validateAIResponse.errors);
    return { valid: false, error: 'Schema validation failed', details: validateAIResponse.errors };
  }
  return { valid: true };
}

/**
 * Calculate total score from breakdown using weighted formula
 *
 * @param {Object} breakdown - Score breakdown object
 * @returns {number} Total score (0-1000)
 */
export function calculateTotalScore(breakdown) {
  return Math.round(
    (breakdown.activity * 2.0) +
    (breakdown.maturity * 2.0) +
    (breakdown.diversity * 2.0) +
    (breakdown.riskBehavior * 2.5) +
    (breakdown.surveyMatch * 1.5)
  );
}
