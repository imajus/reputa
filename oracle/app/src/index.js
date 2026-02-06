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
 * Extract transaction features from EVM data for AI scoring
 */
function extractTransactionFeatures(evmData) {
  const events = evmData?.EVM?.Events || [];
  if (events.length === 0) {
    return {
      totalTransactions: 0,
      accountAgeDays: 0,
      recentActivity: { day: 0, week: 0, month: 0 },
      uniqueContracts: 0,
      protocolsUsed: [],
      valueStats: { total: 0, average: 0 }
    };
  }
  const now = Date.now();
  const ONE_DAY = 24 * 60 * 60 * 1000;
  const ONE_WEEK = 7 * ONE_DAY;
  const ONE_MONTH = 30 * ONE_DAY;
  const timestamps = events.map(e => parseInt(e.Block?.Timestamp || 0) * 1000).filter(t => t > 0);
  const accountAgeDays = timestamps.length > 0 ? (now - Math.min(...timestamps)) / ONE_DAY : 0;
  const recentDay = timestamps.filter(t => now - t < ONE_DAY).length;
  const recentWeek = timestamps.filter(t => now - t < ONE_WEEK).length;
  const recentMonth = timestamps.filter(t => now - t < ONE_MONTH).length;
  const uniqueContracts = new Set(events.map(e => e.Log?.Address).filter(Boolean)).size;
  const protocols = new Set();
  events.forEach(e => {
    const addr = e.Log?.Address?.toLowerCase();
    if (addr?.startsWith('0xa0b8')) protocols.add('Uniswap');
    if (addr?.startsWith('0x7a25')) protocols.add('Aave');
    if (addr?.startsWith('0x1f98')) protocols.add('Uniswap V3');
  });
  const values = events.map(e => parseFloat(e.Transaction?.Value || 0)).filter(v => v > 0);
  const totalValue = values.reduce((sum, v) => sum + v, 0);
  const avgValue = values.length > 0 ? totalValue / values.length : 0;
  return {
    totalTransactions: events.length,
    accountAgeDays: Math.round(accountAgeDays),
    recentActivity: { day: recentDay, week: recentWeek, month: recentMonth },
    uniqueContracts,
    protocolsUsed: Array.from(protocols),
    valueStats: { total: totalValue, average: avgValue }
  };
}

/**
 * Generate AI-powered reputation score using Ollama
 */
async function generateAIScore(address, evmData) {
  const features = extractTransactionFeatures(evmData);
  try {
    const prompt = `You are a DeFi reputation analyzer. Analyze this Ethereum wallet activity and provide a reputation score.

Wallet: ${address}

Activity Summary:
- Total Transactions: ${features.totalTransactions}
- Account Age: ${features.accountAgeDays} days
- Recent Activity: ${features.recentActivity.day} (24h), ${features.recentActivity.week} (7d), ${features.recentActivity.month} (30d)
- Unique Contracts Interacted: ${features.uniqueContracts}
- DeFi Protocols Used: ${features.protocolsUsed.join(', ') || 'None detected'}
- Transaction Value: Total=${features.valueStats.total.toFixed(4)} ETH, Avg=${features.valueStats.average.toFixed(4)} ETH

Scoring Criteria:
1. Transaction Volume (0-250 points): More transactions indicate higher engagement
2. Account Maturity (0-200 points): Older accounts with consistent activity score higher
3. Protocol Diversity (0-200 points): Interaction with multiple DeFi protocols shows sophistication
4. Recent Activity (0-200 points): Recent engagement indicates active participation
5. Value Transacted (0-150 points): Higher value transactions (within normal ranges) show trust

Output Format (JSON):
{
  "score": <integer 0-1000>,
  "reasoning": "<2-3 sentence explanation>",
  "risk_factors": ["<factor1>", "<factor2>"],
  "strengths": ["<strength1>", "<strength2>"]
}

Analyze and respond with JSON only.`;
    const response = await ollamaClient.generate({
      model: 'llama3.2:1b',
      prompt,
      format: 'json',
      options: {
        temperature: 0.3,
        num_predict: 500
      }
    });
    const analysis = JSON.parse(response.response);
    const score = Math.max(0, Math.min(1000, parseInt(analysis.score || 0)));
    return {
      score,
      reasoning: analysis.reasoning || 'AI analysis complete',
      riskFactors: analysis.risk_factors || [],
      strengths: analysis.strengths || [],
      features
    };
  } catch (error) {
    console.error('AI scoring failed, falling back to simple count:', error.message);
    const fallbackScore = Math.min(1000, features.totalTransactions * 10);
    return {
      score: fallbackScore,
      reasoning: 'Fallback: Simple transaction count',
      riskFactors: ['AI scoring unavailable'],
      strengths: [],
      features
    };
  }
}

/**
 * Fetch EVM data from n8n webhook API
 */
async function fetchEVMData(address) {
  const url = `https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address=${address}`;
  try {
    const response = await httpClient.get(url, {
      headers: { 'User-Agent': 'EVM-Score-Oracle/1.0' },
      timeout: 10000
    });
    if (!response.data?.EVM?.Events) {
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
    console.log(`Fetching EVM data for address: ${address}`);
    const evmData = await fetchEVMData(address);
    const aiResult = await generateAIScore(address, evmData);
    const timestampMs = Date.now();
    console.log(`AI Score for ${address}: ${aiResult.score}`);
    console.log(`Reasoning: ${aiResult.reasoning}`);
    const signature = signScoreData(signingKey, aiResult.score, address, timestampMs);
    res.json({
      score: aiResult.score,
      wallet_address: address,
      timestamp_ms: timestampMs,
      signature,
      metadata: {
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
    const { address, questionnaire } = req.body;
    if (!address || !address.match(/^0x[a-fA-F0-9]{40}$/)) {
      return res.status(400).json({
        error: 'Invalid address format. Expected 0x followed by 40 hex characters'
      });
    }
    console.log(`POST /score - address: ${address}`);
    console.log('Questionnaire data:', JSON.stringify(questionnaire, null, 2));
    const evmData = await fetchEVMData(address);
    const aiResult = await generateAIScore(address, evmData);
    const timestampMs = Date.now();
    console.log(`AI Score for ${address}: ${aiResult.score}`);
    console.log(`Reasoning: ${aiResult.reasoning}`);
    const signature = signScoreData(signingKey, aiResult.score, address, timestampMs);
    res.json({
      score: aiResult.score,
      wallet_address: address,
      timestamp_ms: timestampMs,
      signature,
      metadata: {
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
  const port = 3000;
  const host = '0.0.0.0';
  app.listen(port, host, () => {
    console.log(`Starting server on ${host}:${port}`);
  });
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
