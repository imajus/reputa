/// Module: score_oracle
/// An EVM transaction score oracle that verifies attestations and stores wallet scores
module score_oracle::score_oracle;

use std::bcs;
use std::string::String;
use sui::table::{Self, Table};
use sui::event;
use sui::ecdsa_k1;
use enclave::enclave::{Self, Enclave};

// Error codes
const EInvalidSignature: u64 = 0;
const ENoScoreAtTimestamp: u64 = 1;
const ENoScoreAvailable: u64 = 2;

/// One-time witness for module initialization
public struct SCORE_ORACLE has drop {}

/// IntentMessage wrapper (must match Rust IntentMessage structure)
public struct IntentMessage<T: copy + drop> has copy, drop {
    intent: u8,
    timestamp_ms: u64,
    data: T,
}

/// Score data record
public struct ScoreData has copy, drop, store {
    score: u64,
    wallet_address: String,
}

/// Stores all score data with timestamp mapping
public struct ScoreOracle<phantom T> has key {
    id: UID,
    /// Mapping from timestamp to score data
    scores: Table<u64, ScoreData>,
    /// Latest score and its metadata
    latest_score: u64,
    latest_wallet_address: String,
    latest_timestamp: u64,
}

/// Payload for score update messages signed by enclave
public struct ScoreUpdatePayload has copy, drop {
    score: u64,
    wallet_address: String,
}

// Events
public struct ScoreUpdated has copy, drop {
    score: u64,
    wallet_address: String,
    timestamp: u64,
}

public struct OracleCreated has copy, drop {
    oracle_id: ID,
}

/// Initialize the score oracle
fun create_oracle<T>(ctx: &mut TxContext): ScoreOracle<T> {
    let oracle = ScoreOracle<T> {
        id: object::new(ctx),
        scores: table::new(ctx),
        latest_score: 0,
        latest_wallet_address: b"".to_string(),
        latest_timestamp: 0,
    };

    event::emit(OracleCreated {
        oracle_id: object::id(&oracle),
    });

    oracle
}

/// Share the oracle to make it publicly accessible
fun share_oracle<T>(oracle: ScoreOracle<T>) {
    transfer::share_object(oracle);
}

/// Update score with attestation verification
/// Anyone can call this, but the signature must be valid from a registered enclave with correct PCRs
fun update_score<T: drop>(
    oracle: &mut ScoreOracle<T>,
    enclave: &Enclave<T>,
    score: u64,
    wallet_address: String,
    timestamp_ms: u64,
    signature: vector<u8>,
) {
    // Create the payload that should have been signed
    let payload = ScoreUpdatePayload {
        score,
        wallet_address,
    };

    // Verify secp256k1 signature
    // Sui's secp256k1_verify will hash the message using the specified hash function
    // We use SHA256 (hash flag = 1) to match what the enclave uses

    // Serialize the IntentMessage structure: { intent: u8, timestamp_ms: u64, data: payload }
    let intent_message = IntentMessage {
        intent: 0u8,
        timestamp_ms,
        data: payload,
    };
    let message_bytes = bcs::to_bytes(&intent_message);

    let enclave_pk = enclave.pk();

    // Verify secp256k1 signature with SHA256 hash (flag = 1)
    // The function will hash message_bytes with SHA256 before verifying
    let is_valid = ecdsa_k1::secp256k1_verify(
        &signature,
        enclave_pk,
        &message_bytes,
        1 // SHA256 hash function
    );

    assert!(is_valid, EInvalidSignature);

    // Store the score data at the timestamp
    let score_data = ScoreData {
        score,
        wallet_address,
    };
    table::add(&mut oracle.scores, timestamp_ms, score_data);

    // Update latest if this is newer
    if (timestamp_ms > oracle.latest_timestamp) {
        oracle.latest_score = score;
        oracle.latest_wallet_address = wallet_address;
        oracle.latest_timestamp = timestamp_ms;
    };

    event::emit(ScoreUpdated {
        score,
        wallet_address,
        timestamp: timestamp_ms,
    });
}

/// Get the latest wallet score
public fun get_latest_score<T>(oracle: &ScoreOracle<T>): (u64, String, u64) {
    assert!(oracle.latest_timestamp > 0, ENoScoreAvailable);
    (oracle.latest_score, oracle.latest_wallet_address, oracle.latest_timestamp)
}

/// Get the score at a specific timestamp
public fun get_score_at_timestamp<T>(oracle: &ScoreOracle<T>, timestamp: u64): ScoreData {
    assert!(table::contains(&oracle.scores, timestamp), ENoScoreAtTimestamp);
    *table::borrow(&oracle.scores, timestamp)
}

/// Check if a score exists at a specific timestamp
public fun has_score_at_timestamp<T>(oracle: &ScoreOracle<T>, timestamp: u64): bool {
    table::contains(&oracle.scores, timestamp)
}

/// Get the timestamp of the latest score
public fun get_latest_timestamp<T>(oracle: &ScoreOracle<T>): u64 {
    oracle.latest_timestamp
}

/// Module initializer - sets up enclave config
/// The oracle will be created after enclave registration
fun init(witness: SCORE_ORACLE, ctx: &mut TxContext) {
    // Create the enclave capability
    let cap = enclave::new_cap(witness, ctx);

    // Create the enclave configuration with PCR values
    cap.create_enclave_config(
        b"EVM Transaction Score Oracle".to_string(),
        // PCR0: Enclave image file hash - update after building your enclave
        x"3aa0e6e6ed7d8301655fced7e6ddcc443a3e57bf62f070caa6becf337069e859c0f03d68136440ff1cab8adefd20634c",
        // PCR1: Enclave kernel hash - update after building your enclave
        x"b0d319fa64f9c2c9d7e9187bc21001ddacfab4077e737957fa1b8b97cc993bed43a79019aebfd40ee5f6f213147909f8",
        // PCR2: Enclave application hash - update after building your enclave
        x"fdb2295dc5d9b67a653ed5f3ead5fc8166ec3cae1de1c7c6f31c3b43b2eb26ab5d063f414f3d2b93163426805dfe057e",
        // PCR16: Application image hash - update after building your application
        x"94a33ba1298c64a16a1f4c9cc716525c86497017e09dd976afcaf812b0e2a3e8ba04ff6954167ad69a6413a1e6e44621",
        ctx,
    );

    // Transfer the capability to the deployer for future PCR updates
    transfer::public_transfer(cap, ctx.sender());
}

/// Entry function to create and share the oracle after enclave registration
/// Call this once your enclave is registered on-chain
entry fun initialize_oracle(ctx: &mut TxContext) {
    let oracle = create_oracle<SCORE_ORACLE>(ctx);
    share_oracle(oracle);
}

/// Entry function to update wallet score
/// Anyone can call this with a valid signature from the authorized enclave
entry fun update_wallet_score(
    oracle: &mut ScoreOracle<SCORE_ORACLE>,
    enclave: &Enclave<SCORE_ORACLE>,
    score: u64,
    wallet_address: vector<u8>,
    timestamp_ms: u64,
    signature: vector<u8>,
) {
    // Convert vector<u8> to String for internal use
    let wallet_address_string = wallet_address.to_string();
    update_score(
        oracle,
        enclave,
        score,
        wallet_address_string,
        timestamp_ms,
        signature,
    );
}

#[test_only]
public fun destroy_oracle_for_testing<T>(oracle: ScoreOracle<T>) {
    let ScoreOracle { id, scores, latest_score: _, latest_wallet_address: _, latest_timestamp: _ } = oracle;
    table::drop(scores);
    object::delete(id);
}
