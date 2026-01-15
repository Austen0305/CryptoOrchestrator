use k256::ecdsa::{signature::Signer, Signature, SigningKey};
use k256::elliptic_curve::rand_core::OsRng;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::time::Instant;

/// MPC-Compatible Signature Result
///
/// In a real MPC implementation, the signature would be computed
/// across multiple parties without any party knowing the full key.
/// This implementation provides the interface expected by the MPC service.
#[derive(Clone)]
struct SignatureResult {
    /// ECDSA signature in raw bytes (64 bytes: r || s)
    signature: Vec<u8>,
    /// r component (32 bytes)
    r: Vec<u8>,
    /// s component (32 bytes)
    s: Vec<u8>,
    /// Recovery ID (0 or 1, +27 for Ethereum)
    v: u8,
    /// Signing latency in milliseconds
    latency_ms: f64,
}

/// Production signing interface
///
/// This uses the k256 crate for real ECDSA operations.
/// In production with MPC, replace the key generation with
/// threshold key share aggregation.
struct ProductionSigner {
    /// The signing key (in production, this would be MPC key shares)
    key: SigningKey,
}

impl ProductionSigner {
    /// Create a new signer
    ///
    /// In production MPC, this would initialize connection to key shares
    /// distributed across multiple parties.
    fn new() -> Self {
        // Generate ephemeral key for signing
        // In production: retrieve or compute from MPC shares
        let key = SigningKey::random(&mut OsRng);
        ProductionSigner { key }
    }

    /// Create signer from existing key bytes
    fn from_bytes(key_bytes: &[u8]) -> Result<Self, String> {
        let key = SigningKey::from_bytes(key_bytes.into())
            .map_err(|e| format!("Invalid key bytes: {}", e))?;
        Ok(ProductionSigner { key })
    }

    /// Sign a message digest
    ///
    /// Args:
    ///     digest: 32-byte message hash to sign
    ///
    /// Returns:
    ///     SignatureResult with signature components
    fn sign(&self, digest: &[u8]) -> Result<SignatureResult, String> {
        let start = Instant::now();

        if digest.len() != 32 {
            return Err(format!("Digest must be 32 bytes, got {}", digest.len()));
        }

        // Create the signature
        let signature: Signature = self.key.sign(digest);
        let sig_bytes = signature.to_bytes();

        // Extract r and s components
        let r = sig_bytes[..32].to_vec();
        let s = sig_bytes[32..].to_vec();

        let latency_ms = start.elapsed().as_secs_f64() * 1000.0;

        Ok(SignatureResult {
            signature: sig_bytes.to_vec(),
            r,
            s,
            v: 27, // Default recovery ID for Ethereum
            latency_ms,
        })
    }

    /// Get the public key (for address derivation)
    fn public_key(&self) -> Vec<u8> {
        use k256::ecdsa::VerifyingKey;
        let verifying_key: VerifyingKey = self.key.verifying_key().clone();
        verifying_key.to_encoded_point(false).as_bytes().to_vec()
    }
}

/// Signs a transaction digest using ECDSA
///
/// Args:
///     digest: Hex-encoded 32-byte message hash
///     key_hex: Optional hex-encoded private key (for testing)
///
/// Returns:
///     Dictionary with signature components (r, s, v, signature, latency_ms)
#[pyfunction]
fn sign_digest(digest: &str, key_hex: Option<&str>) -> PyResult<pyo3::Py<pyo3::types::PyDict>> {
    // Parse digest from hex
    let digest_bytes = hex::decode(digest.trim_start_matches("0x"))
        .map_err(|e| PyValueError::new_err(format!("Invalid hex digest: {}", e)))?;

    // Create signer
    let signer = if let Some(key) = key_hex {
        let key_bytes = hex::decode(key.trim_start_matches("0x"))
            .map_err(|e| PyValueError::new_err(format!("Invalid hex key: {}", e)))?;
        ProductionSigner::from_bytes(&key_bytes).map_err(|e| PyValueError::new_err(e))?
    } else {
        ProductionSigner::new()
    };

    // Sign
    let result = signer
        .sign(&digest_bytes)
        .map_err(|e| PyValueError::new_err(e))?;

    // Build Python dict
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("signature", format!("0x{}", hex::encode(&result.signature)))?;
        dict.set_item("r", format!("0x{}", hex::encode(&result.r)))?;
        dict.set_item("s", format!("0x{}", hex::encode(&result.s)))?;
        dict.set_item("v", result.v)?;
        dict.set_item("latency_ms", result.latency_ms)?;
        Ok(dict.into())
    })
}

/// Legacy function for backward compatibility
/// Signs a transaction payload (computes keccak256 hash first)
#[pyfunction]
fn sign_transaction(payload: &str) -> PyResult<String> {
    use sha3::{Digest, Keccak256};

    // Hash the payload
    let digest = Keccak256::digest(payload.as_bytes());

    // Create ephemeral signer
    let signer = ProductionSigner::new();

    // Sign
    let result = signer.sign(&digest).map_err(|e| PyValueError::new_err(e))?;

    Ok(format!("0x{}", hex::encode(&result.signature)))
}

/// Get public key from private key bytes
#[pyfunction]
fn get_public_key(key_hex: &str) -> PyResult<String> {
    let key_bytes = hex::decode(key_hex.trim_start_matches("0x"))
        .map_err(|e| PyValueError::new_err(format!("Invalid hex key: {}", e)))?;

    let signer = ProductionSigner::from_bytes(&key_bytes).map_err(|e| PyValueError::new_err(e))?;

    Ok(format!("0x{}", hex::encode(signer.public_key())))
}

/// Python module with production signing functions
#[pymodule]
fn crypto_signer(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sign_transaction, m)?)?;
    m.add_function(wrap_pyfunction!(sign_digest, m)?)?;
    m.add_function(wrap_pyfunction!(get_public_key, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_signing() {
        let signer = ProductionSigner::new();
        let digest = [0u8; 32];
        let result = signer.sign(&digest).unwrap();

        assert_eq!(result.signature.len(), 64);
        assert_eq!(result.r.len(), 32);
        assert_eq!(result.s.len(), 32);
        assert!(result.latency_ms < 100.0); // Should be fast
    }

    #[test]
    fn test_invalid_digest_length() {
        let signer = ProductionSigner::new();
        let digest = [0u8; 16]; // Wrong length
        let result = signer.sign(&digest);

        assert!(result.is_err());
    }
}
