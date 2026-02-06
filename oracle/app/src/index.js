import express from 'express';
import cors from 'cors';
import axios from 'axios';
import { sign, getPublicKey, hashes } from '@noble/secp256k1';
import { sha256 } from '@noble/hashes/sha2.js';
import { hmac } from '@noble/hashes/hmac.js';
import { createHash } from 'crypto';
import fs from 'fs';
import { bcs } from '@mysten/bcs';

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

/**
 * Fetch transaction count from n8n webhook API
 */
async function fetchTransactionCount(address) {
  const url = `https://n8n.majus.org/webhook/c1b4be31-8022-4d48-94a6-7d27a7565440?address=${address}`;
  try {
    const response = await httpClient.get(url, {
      headers: { 'User-Agent': 'EVM-Score-Oracle/1.0' },
      timeout: 10000
    });
    if (!response.data?.EVM?.Events) {
      throw new Error('Invalid API response structure');
    }
    return response.data.EVM.Events.length;
  } catch (error) {
    console.error('Failed to fetch transaction count:', error.message);
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
  origin: ['http://[::]:8080', 'http://localhost:8080', 'http://192.168.0.12:8080']
}));
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
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
    console.log(`Fetching transaction count for address: ${address}`);
    const txCount = await fetchTransactionCount(address);
    const timestampMs = Date.now();
    console.log(`Transaction count for ${address}: ${txCount}`);
    const signature = signScoreData(signingKey, txCount, address, timestampMs);
    res.json({
      score: txCount,
      wallet_address: address,
      timestamp_ms: timestampMs,
      signature,
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
    const txCount = await fetchTransactionCount(address);
    const timestampMs = Date.now();
    console.log(`Transaction count for ${address}: ${txCount}`);
    const signature = signScoreData(signingKey, txCount, address, timestampMs);
    res.json({
      score: txCount,
      wallet_address: address,
      timestamp_ms: timestampMs,
      signature,
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
