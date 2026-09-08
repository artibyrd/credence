/**
 * Credence Workstation WebCrypto Ed25519 Verification
 * Zero-npm native ES module.
 */

// WEBCRYPTO ED25519 VERIFICATION UTILITY
// -----------------------------------------------------------------------------

export async function verifyEd25519Signature(canonicalJsonString, signatureHex, pubkeyHex) {
  try {
    if (!window.crypto || !window.crypto.subtle) {
      return { valid: false, error: 'WebCrypto unavailable' };
    }
    const cleanPubHex = pubkeyHex.replace(/^0x/, '').trim();
    const cleanSigHex = signatureHex.replace(/^0x/, '').trim();
    
    const pubKeyBytes = new Uint8Array(cleanPubHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const sigBytes = new Uint8Array(cleanSigHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const msgBytes = new TextEncoder().encode(canonicalJsonString);

    const cryptoKey = await window.crypto.subtle.importKey(
      'raw',
      pubKeyBytes,
      { name: 'Ed25519' },
      false,
      ['verify']
    );

    const isValid = await window.crypto.subtle.verify(
      { name: 'Ed25519' },
      cryptoKey,
      sigBytes,
      msgBytes
    );

    return { valid: isValid, error: null };
  } catch (e) {
    return { valid: false, error: e.message };
  }
}
