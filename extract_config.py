#!/usr/bin/env python3
"""Decrypt Granola's encrypted supabase storage and emit config.json.

Layout (newer Granola builds, macOS):
  storage.dek         = b"v10" + Electron-safeStorage(AES-128-CBC) wrapped DEK
                        key = PBKDF2-HMAC-SHA1(keychain_secret, b"saltysalt", 1003, 16)
                        IV  = 16 spaces
                        plaintext = 44-char base64 of the real 32-byte AES-256 DEK
  supabase.json.enc   = AES-256-GCM( DEK ) = [12B nonce][ciphertext][16B tag]
The keychain secret: service "Granola Safe Storage", account "Granola Key".
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA1

APP = Path.home() / "Library" / "Application Support" / "Granola"


def keychain_secret() -> bytes:
    out = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Granola Safe Storage"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"Keychain read failed: {out.stderr.strip()}")
    return out.stdout.strip().encode("utf-8")


def unwrap_dek(secret: bytes) -> bytes:
    blob = (APP / "storage.dek").read_bytes()
    if not blob.startswith(b"v10"):
        sys.exit(f"storage.dek prefix {blob[:4]!r} != v10")
    key = PBKDF2HMAC(algorithm=SHA1(), length=16, salt=b"saltysalt", iterations=1003).derive(secret)
    dec = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).decryptor()
    padded = dec.update(blob[3:]) + dec.finalize()
    unpadded = padded[:-padded[-1]]
    # Newer Granola builds store the 32-byte DEK as a 44-char base64 string,
    # not as raw key bytes. Decode it back to the real AES-256 key.
    return base64.b64decode(unpadded)


def try_gcm(dek: bytes, blob: bytes):
    """Try AES-256-GCM with a few common nonce-length conventions."""
    for nlen in (12, 16):
        try:
            nonce, ct = blob[:nlen], blob[nlen:]
            return AESGCM(dek).decrypt(nonce, ct, None)
        except Exception:
            continue
    return None


def main():
    secret = keychain_secret()
    dek = unwrap_dek(secret)
    print(f"[ok] unwrapped DEK ({len(dek)} bytes)", file=sys.stderr)

    blob = (APP / "supabase.json.enc").read_bytes()
    plaintext = try_gcm(dek, blob)
    if plaintext is None:
        sys.exit("AES-GCM decrypt failed with 12/16-byte nonce; scheme differs.")

    data = json.loads(plaintext)
    workos_raw = data.get("workos_tokens")
    if not workos_raw:
        sys.exit(f"workos_tokens missing; top-level keys: {list(data.keys())}")
    workos = json.loads(workos_raw) if isinstance(workos_raw, str) else workos_raw

    refresh_token = workos.get("refresh_token")
    access_token = workos.get("access_token")
    if not refresh_token or not access_token:
        sys.exit("refresh_token / access_token missing")

    payload = access_token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    iss = json.loads(base64.urlsafe_b64decode(payload)).get("iss", "")
    client_id = "client_" + iss.split("client_")[-1] if "client_" in iss else None
    if not client_id:
        sys.exit("client_id not found in access_token issuer")

    Path("config.json").write_text(json.dumps(
        {"refresh_token": refresh_token, "client_id": client_id}, indent=2))
    print(f"config.json created (client_id={client_id}, refresh_token len={len(refresh_token)})")


if __name__ == "__main__":
    main()
