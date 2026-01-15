import sys
import time

try:
    import crypto_signer

    print("✅ [Rust Bridge] Module imported successfully.")
except ImportError as e:
    print(f"❌ [Rust Bridge] Failed to import module: {e}")
    sys.exit(1)


def test_signing():
    payload = "tx_payload_data_0x123456789"
    start = time.time()
    try:
        # Call the Rust function
        signature = crypto_signer.sign_transaction(payload)
        elapsed = (time.time() - start) * 1000

        print(f"✅ [Rust Bridge] Signed Payload: {payload}")
        print(f"   -> Signature: {signature}")
        print(f"   -> Latency: {elapsed:.2f}ms")

        expected_prefix = "hsm_sig_slot_1_digest_"
        if signature.startswith(expected_prefix):
            print("✅ [Rust Bridge] Validation Passed: Signature format correct.")
        else:
            print(
                f"❌ [Rust Bridge] Validation Failed: Unexpected format. Got {signature}"
            )
            sys.exit(1)

    except Exception as e:
        print(f"❌ [Rust Bridge] Execution Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_signing()
