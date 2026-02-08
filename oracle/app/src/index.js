import express from 'express';
import cors from 'cors';
import axios from 'axios';
import { sign, getPublicKey, hashes } from '@noble/secp256k1';
import { sha256 } from '@noble/hashes/sha2.js';
import { hmac } from '@noble/hashes/hmac.js';
import { createHash } from 'crypto';
import fs from 'fs';
import { bcs } from '@mysten/bcs';
import { Ollama } from 'ollama';
import { validateAIResponseData } from './validation.js';

// Configure @noble/secp256k1 to use @noble/hashes for SHA-256
hashes.sha256 = sha256;
hashes.hmacSha256 = (key, msg) => hmac(sha256, key, msg);

// Define the structures to match Move contract
const ScoreUpdatePayload = bcs.struct('ScoreUpdatePayload', {
  score: bcs.u64(),
  wallet_address: bcs.string(),
});

// Define IntentMessage wrapper - using a generic function approach
function IntentMessage(DataType) {
  return bcs.struct('IntentMessage', {
    intent: bcs.u8(),
    timestamp_ms: bcs.u64(),
    data: DataType,
  });
}

// Create the specific IntentMessage for ScoreUpdatePayload
const IntentMessageScoreUpdate = IntentMessage(ScoreUpdatePayload);

// Intent scope constant (0 for personal intent)
const INTENT_SCOPE = 0;

// Application state
let signingKey = null;
const httpClient = axios.create();
const ollamaClient = new Ollama({ host: process.env.OLLAMA_HOST || 'http://127.0.0.1:11434' });

/**
 * Helper function to sum a specific field across lending protocol objects
 */
function sumField(protocols, field) {
  if (!protocols || typeof protocols !== 'object') return 0;
  return Object.values(protocols).reduce((sum, protocol) => {
    return sum + (parseInt(protocol[field]) || 0);
  }, 0);
}

/**
 * Format questionnaire responses for AI readability
 */
function formatQuestionnaireForAI(questionnaire) {
  if (!questionnaire || !Array.isArray(questionnaire) || questionnaire.length === 0) {
    return "No questionnaire data provided.";
  }
  return questionnaire.map((item, index) => {
    const answer = item.answer?.trim() || '';
    const answerText = answer === '' ? '(not answered)' : answer;
    return `Q${index + 1}: ${item.question}\nA${index + 1}: ${answerText}`;
  }).join('\n\n');
}

/**
 * Generate fallback scoreBreakdown from total score
 */
function generateFallbackBreakdown(totalScore) {
  return {
    activity: Math.round(Math.max(0, Math.min(100, totalScore * 0.20 / 10))),
    maturity: Math.round(Math.max(0, Math.min(100, totalScore * 0.20 / 10))),
    diversity: Math.round(Math.max(0, Math.min(100, totalScore * 0.20 / 10))),
    riskBehavior: Math.round(Math.max(0, Math.min(100, totalScore * 0.25 / 10))),
    surveyMatch: 50
  };
}

/**
 * Extract wallet features from new EVM data structure
 */
function extractWalletFeatures(evmData) {
  const walletMetadata = evmData?.wallet_metadata || {};
  const defiAnalysis = evmData?.defi_analysis || {};
  const lendingHistory = evmData?.lending_history || {};
  const tokens = evmData?.tokens || {};
  const nfts = evmData?.nfts || {};
  const protocolInteractions = defiAnalysis.protocol_interactions || {};
  const protocolNames = Object.keys(protocolInteractions).filter(key =>
    key !== 'total_protocols' && protocolInteractions[key] === true
  );
  const protocols = lendingHistory?.protocol_analysis?.protocols || {};
  const borrowCount = sumField(protocols, 'borrow_count');
  const repayCount = sumField(protocols, 'repay_count');
  const liquidateCount = sumField(protocols, 'liquidate_count');
  const supplyCount = sumField(protocols, 'supply_count');
  const withdrawCount = sumField(protocols, 'withdraw_count');
  const concentration = tokens?.concentration || {};
  const holdings = tokens?.holdings || [];
  const poapCount = Array.isArray(nfts?.poaps) ? nfts.poaps.length : 0;
  const nftCount = Array.isArray(nfts?.legit_nfts) ? nfts.legit_nfts.length : 0;
  return {
    walletAge: parseInt(walletMetadata.wallet_age_days) || 0,
    totalTransactions: parseInt(walletMetadata.total_transactions) || 0,
    avgTxsPerMonth: parseFloat(walletMetadata.average_txs_per_month) || 0,
    uniqueCounterparties: parseInt(walletMetadata.unique_counterparties) || 0,
    protocolsUsed: parseInt(protocolInteractions.total_protocols) || 0,
    protocolNames: protocolNames,
    borrowCount,
    repayCount,
    liquidateCount,
    supplyCount,
    withdrawCount,
    numTokens: parseInt(concentration.num_tokens) || holdings.length || 0,
    diversificationScore: parseInt(concentration.diversification_score) || 0,
    concentrationRisk: parseFloat(concentration.herfindahl_index) || 0,
    poapCount,
    nftCount,
    ethBalance: parseFloat(evmData?.eth_balance) || 0
  };
}

/**
 * Generate deterministic seed from wallet address
 */
function generateSeedFromAddress(address) {
  const normalized = address.toLowerCase().replace(/^0x/, '');
  const hash = createHash('sha256').update(normalized).digest();
  return hash.readUInt32BE(0);
}

/**
 * Generate AI score with validation and retry logic
 */
async function generateAIScore(evmData, questionnaire = [], walletAddress = '') {
  const features = extractWalletFeatures(evmData);
  const questionnaireText = formatQuestionnaireForAI(questionnaire);
  const seed = walletAddress ? generateSeedFromAddress(walletAddress) : undefined;
  if (seed !== undefined) {
    console.log(`Using deterministic seed: ${seed} for address: ${walletAddress}`);
  }
  const prompt = `You are a DeFi creditworthiness analyzer. Analyze this Ethereum wallet's on-chain activity and questionnaire responses to provide a detailed reputation score.

## On-Chain Activity

Wallet Metadata:
- Account Age: ${features.walletAge} days
- Total Transactions: ${features.totalTransactions}
- Average Transactions/Month: ${features.avgTxsPerMonth.toFixed(1)}
- Unique Counterparties: ${features.uniqueCounterparties}

DeFi Protocol Interactions:
- Total Protocols Used: ${features.protocolsUsed}
- Protocol Names: ${features.protocolNames.join(', ') || 'None detected'}

Lending History:
- Borrow Events: ${features.borrowCount}
- Repay Events: ${features.repayCount}
- Liquidation Events: ${features.liquidateCount}
- Supply Events: ${features.supplyCount}
- Withdraw Events: ${features.withdrawCount}

Token Portfolio:
- Number of Tokens: ${features.numTokens}
- Diversification Score: ${features.diversificationScore}/100
- Concentration Risk (Herfindahl Index): ${features.concentrationRisk.toFixed(3)}

NFTs & POAPs:
- POAPs: ${features.poapCount}
- NFTs: ${features.nftCount}

ETH Balance: ${features.ethBalance.toFixed(4)} ETH

## Borrower Profile

${questionnaireText}

## Scoring Instructions

Provide a detailed breakdown across 5 dimensions (each 0-100):

1. **Transaction Activity** (0-100): Transaction count, frequency, monthly average, recent engagement
2. **Account Maturity** (0-100): Account age, usage consistency over time
3. **Protocol & Token Diversity** (0-100): Number of protocols, token count, diversification score, unique counterparties
4. **Risk Behavior / Financial Health** (0-100): Liquidation history, borrow/repay ratio, concentration risk, liability disclosure from questionnaire
5. **Questionnaire Coherence** (0-100): Alignment between stated intent and on-chain behavior. If no questionnaire provided, default to 50 (neutral)

Calculate total score as weighted average:
Total Score (0-1000) = (Activity*2 + Maturity*2 + Diversity*2 + RiskBehavior*2.5 + Coherence*1.5)

Output Format (JSON only):
{
  "score": <integer 0-1000>,
  "scoreBreakdown": {
    "activity": <integer 0-100>,
    "maturity": <integer 0-100>,
    "diversity": <integer 0-100>,
    "riskBehavior": <integer 0-100>,
    "surveyMatch": <integer 0-100>
  },
  "reasoning": "<2-3 sentence explanation of overall score>",
  "risk_factors": ["<factor1>", "<factor2>"],
  "strengths": ["<strength1>", "<strength2>"]
}

Analyze and respond with JSON only.`;
  const temperatures = [0.2, 0.1, 0.05];
  const maxRetries = temperatures.length;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const temperature = temperatures[attempt];
    console.log(`AI scoring attempt ${attempt + 1}/${maxRetries} with temperature ${temperature}`);
    try {
      const response = await ollamaClient.generate({
        model: 'llama3.2:1b',
        prompt,
        format: 'json',
        options: {
          temperature,
          num_predict: 800,
          seed
        }
      });
      const analysis = JSON.parse(response.response);
      const validation = validateAIResponseData(analysis);
      if (!validation.valid) {
        console.error(`Attempt ${attempt + 1} validation failed:`, validation.error, validation.details);
        if (attempt === maxRetries - 1) {
          throw new Error(`All ${maxRetries} validation attempts failed`);
        }
        continue;
      }
      console.log(`AI scoring succeeded on attempt ${attempt + 1}`);
      return {
        score: analysis.score,
        scoreBreakdown: analysis.scoreBreakdown,
        reasoning: analysis.reasoning,
        riskFactors: analysis.risk_factors,
        strengths: analysis.strengths,
        features
      };
    } catch (error) {
      console.error(`AI scoring attempt ${attempt + 1} failed:`, error.message);
      if (attempt === maxRetries - 1) {
        console.error('All AI scoring attempts exhausted, falling back to simple count');
        const fallbackScore = Math.min(1000, features.totalTransactions * 10);
        const scoreBreakdown = generateFallbackBreakdown(fallbackScore);
        return {
          score: fallbackScore,
          scoreBreakdown,
          reasoning: 'Fallback scoring: AI unavailable',
          riskFactors: ['AI scoring unavailable'],
          strengths: [],
          features
        };
      }
    }
  }
}

/**
 * Fetch EVM data from aggregate API
 */
async function fetchEVMData(address) {
  const url = 'https://reputa-data.majus.app/aggregate';
  try {
    const response = await httpClient.post(url, {
      wallet_address: address
    }, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'EVM-Score-Oracle/1.0'
      },
      timeout: 120000
    });
    if (!response.data) {
      throw new Error('Invalid API response structure');
    }
    return response.data;
  } catch (error) {
    console.error('Failed to fetch EVM data:', error.message);
    throw error;
  }
}

/**
 * Sign score data following Nautilus pattern with secp256k1
 */
function signScoreData(privateKey, score, walletAddress, timestampMs) {
  const payload = {
    score: score,
    wallet_address: walletAddress
  };
  const intentMessage = {
    intent: INTENT_SCOPE,
    timestamp_ms: timestampMs,
    data: payload,
  };
  const messageBytes = IntentMessageScoreUpdate.serialize(intentMessage).toBytes();
  const hash = createHash('sha256').update(messageBytes).digest();
  const signature = sign(hash, privateKey, { prehash: false });
  return Buffer.from(signature).toString('hex');
}

/**
 * Load secp256k1 signing key from file
 */
function loadSigningKeyFromFile(path) {
  const keyBytes = fs.readFileSync(path);
  if (keyBytes.length !== 32) {
    throw new Error(`Expected 32-byte secp256k1 private key, got ${keyBytes.length} bytes`);
  }
  try {
    getPublicKey(keyBytes);
  } catch (error) {
    throw new Error('Invalid secp256k1 private key');
  }
  return keyBytes;
}

/**
 * Express route handlers
 */
const app = express();

app.use(cors({
  origin: ['http://[::]:8080', 'http://localhost:8080', 'http://192.168.0.12:8080', 'https://reputa.pages.dev'],
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
app.use(express.json());

// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: Date.now(),
    ollama: 'unknown'
  };
  try {
    await ollamaClient.list();
    health.ollama = 'connected';
  } catch (error) {
    health.ollama = 'unavailable';
    health.status = 'degraded';
  }
  res.json(health);
});

// Get public key endpoint
app.get('/public-key', (req, res) => {
  const publicKey = getPublicKey(signingKey, true);
  const pkHex = Buffer.from(publicKey).toString('hex');
  res.json({
    public_key: pkHex,
  });
});

// Get signed score endpoint
app.get('/score', async (req, res) => {
  try {
    const address = req.query.address;
    if (!address || !address.match(/^0x[a-fA-F0-9]{40}$/)) {
      return res.status(400).json({
        error: 'Invalid address format. Expected 0x followed by 40 hex characters'
      });
    }
    console.log(`GET /score - Fetching EVM data for address: ${address}`);
    const evmData = await fetchEVMData(address);
    const aiResult = await generateAIScore(evmData, [], address);
    const timestampMs = Date.now();
    console.log(`AI Score for ${address}: ${aiResult.score}`);
    console.log(`Reasoning: ${aiResult.reasoning}`);
    console.log(`Score Breakdown:`, aiResult.scoreBreakdown);
    const signature = signScoreData(signingKey, aiResult.score, address, timestampMs);
    res.json({
      score: aiResult.score,
      wallet_address: address,
      timestamp_ms: timestampMs,
      signature,
      metadata: {
        scoreBreakdown: aiResult.scoreBreakdown,
        reasoning: aiResult.reasoning,
        risk_factors: aiResult.riskFactors,
        strengths: aiResult.strengths,
        features: aiResult.features
      }
    });
  } catch (error) {
    console.error('Failed to process score request:', error);
    res.status(503).json({
      error: 'Failed to fetch or sign score',
      message: error.message,
    });
  }
});

app.post('/score', async (req, res) => {
  try {
    const { address, questionnaire = [] } = req.body;
    if (!address || !address.match(/^0x[a-fA-F0-9]{40}$/)) {
      return res.status(400).json({
        error: 'Invalid address format. Expected 0x followed by 40 hex characters'
      });
    }
    const hasQuestionnaire = questionnaire && Array.isArray(questionnaire) && questionnaire.length > 0;
    console.log(`POST /score - address: ${address}, questionnaire: ${hasQuestionnaire ? 'provided' : 'empty'}`);
    if (hasQuestionnaire) {
      console.log('Questionnaire data:', JSON.stringify(questionnaire, null, 2));
    }
    const evmData = await fetchEVMData(address);
    const aiResult = await generateAIScore(evmData, questionnaire, address);
    const timestampMs = Date.now();
    console.log(`AI Score for ${address}: ${aiResult.score}`);
    console.log(`Reasoning: ${aiResult.reasoning}`);
    console.log(`Score Breakdown:`, aiResult.scoreBreakdown);
    const signature = signScoreData(signingKey, aiResult.score, address, timestampMs);
    res.json({
      score: aiResult.score,
      wallet_address: address,
      timestamp_ms: timestampMs,
      signature,
      metadata: {
        scoreBreakdown: aiResult.scoreBreakdown,
        reasoning: aiResult.reasoning,
        risk_factors: aiResult.riskFactors,
        strengths: aiResult.strengths,
        features: aiResult.features
      }
    });
  } catch (error) {
    console.error('Failed to process score request:', error);
    res.status(503).json({
      error: 'Failed to fetch or sign score',
      message: error.message,
    });
  }
});

/**
 * Main function
 */
async function main() {
  const args = process.argv.slice(2);
  if (args.length !== 1) {
    console.error('Usage: node src/index.js <path-to-signing-key>');
    process.exit(1);
  }
  const keyPath = args[0];
  console.log(`Loading secp256k1 signing key from: ${keyPath}`);
  signingKey = loadSigningKeyFromFile(keyPath);
  console.log('Signing key loaded successfully');
  const publicKey = getPublicKey(signingKey, true);
  console.log(`Public key (hex): ${Buffer.from(publicKey).toString('hex')}`);
  const port = 8880;
  const host = '0.0.0.0';
  app.listen(port, host, () => {
    console.log(`Starting server on ${host}:${port}`);
  });
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
