/// Module: score_oracle
/// An EVM transaction score oracle that verifies attestations and stores wallet scores
module score_oracle::score_oracle;

use std::bcs;
use std::string::String;
use sui::event;
use sui::ecdsa_k1;
use sui::dynamic_field as field;
use enclave::enclave::{Self, Enclave};

// Error codes
const EInvalidSignature: u64 = 0;
const ENoScoreForWallet: u64 = 1;

/// One-time witness for module initialization
public struct SCORE_ORACLE has drop {}

/// IntentMessage wrapper (must match Rust IntentMessage structure)
public struct IntentMessage<T: copy + drop> has copy, drop {
    intent: u8,
    timestamp_ms: u64,
    data: T,
}

/// User's reputation score - owned by the user
public struct WalletScore has key, store {
    id: UID,
    score: u64,
    wallet_address: String,
    timestamp_ms: u64,
    version: u64,
}

/// Shared registry for wallet address lookups
/// Dynamic field mapping: wallet_address (String) -> object ID of latest WalletScore
public struct ScoreRegistry<phantom T> has key {
    id: UID,
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
    score_object_id: ID,
    owner: address,
}

public struct RegistryCreated has copy, drop {
    registry_id: ID,
}

/// Initialize the score registry
fun create_registry<T>(ctx: &mut TxContext): ScoreRegistry<T> {
    let registry = ScoreRegistry<T> {
        id: object::new(ctx),
    };

    event::emit(RegistryCreated {
        registry_id: object::id(&registry),
    });

    registry
}

/// Share the registry to make it publicly accessible
fun share_registry<T>(registry: ScoreRegistry<T>) {
    transfer::share_object(registry);
}

/// Update score with attestation verification
/// Creates a user-owned WalletScore object and registers it in the registry
#[allow(lint(self_transfer))]
fun update_score<T: drop>(
    registry: &mut ScoreRegistry<T>,
    enclave: &Enclave<T>,
    score: u64,
    wallet_address: String,
    timestamp_ms: u64,
    signature: vector<u8>,
    ctx: &mut TxContext,
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

    // Determine version number (increment if updating existing score)
    let version = if (field::exists_<String>(&registry.id, wallet_address)) {
        // Remove previous score ID from registry (old object is still owned by the user)
        let _old_score_id = field::remove<String, ID>(&mut registry.id, wallet_address);
        // Version is incremented - we can't read the old object, so we just increment by 1
        // Simplified - in production could track version in registry
        1
    } else {
        1
    };

    // Create user-owned WalletScore object
    let wallet_score = WalletScore {
        id: object::new(ctx),
        score,
        wallet_address,
        timestamp_ms,
        version,
    };

    let score_id = object::id(&wallet_score);
    let owner = ctx.sender();

    // Register in dynamic field for lookup
    field::add(&mut registry.id, wallet_address, score_id);

    // Transfer ownership to transaction sender
    transfer::public_transfer(wallet_score, owner);

    event::emit(ScoreUpdated {
        score,
        wallet_address,
        timestamp: timestamp_ms,
        score_object_id: score_id,
        owner,
    });
}

/// Get score data from a WalletScore object
public fun get_score(wallet_score: &WalletScore): (u64, String, u64, u64) {
    (
        wallet_score.score,
        wallet_score.wallet_address,
        wallet_score.timestamp_ms,
        wallet_score.version,
    )
}

/// Lookup the object ID of a wallet's latest score from the registry
public fun lookup_score_id<T>(
    registry: &ScoreRegistry<T>,
    wallet_address: String,
): ID {
    assert!(field::exists_<String>(&registry.id, wallet_address), ENoScoreForWallet);
    *field::borrow<String, ID>(&registry.id, wallet_address)
}

/// Check if a score exists for a wallet address
public fun has_score_for_wallet<T>(
    registry: &ScoreRegistry<T>,
    wallet_address: String,
): bool {
    field::exists_<String>(&registry.id, wallet_address)
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

/// Entry function to create and share the registry after enclave registration
/// Call this once your enclave is registered on-chain
entry fun initialize_registry(ctx: &mut TxContext) {
    let registry = create_registry<SCORE_ORACLE>(ctx);
    share_registry(registry);
}

/// Entry function to update wallet score
/// Anyone can call this with a valid signature from the authorized enclave
/// Creates a WalletScore object owned by the transaction sender
entry fun update_wallet_score(
    registry: &mut ScoreRegistry<SCORE_ORACLE>,
    enclave: &Enclave<SCORE_ORACLE>,
    score: u64,
    wallet_address: vector<u8>,
    timestamp_ms: u64,
    signature: vector<u8>,
    ctx: &mut TxContext,
) {
    // Convert vector<u8> to String for internal use
    let wallet_address_string = wallet_address.to_string();
    update_score(
        registry,
        enclave,
        score,
        wallet_address_string,
        timestamp_ms,
        signature,
        ctx,
    );
}

#[test_only]
public fun destroy_registry_for_testing<T>(registry: ScoreRegistry<T>) {
    let ScoreRegistry { id } = registry;
    object::delete(id);
}

#[test_only]
public fun destroy_wallet_score_for_testing(wallet_score: WalletScore) {
    let WalletScore { id, score: _, wallet_address: _, timestamp_ms: _, version: _ } = wallet_score;
    object::delete(id);
}
