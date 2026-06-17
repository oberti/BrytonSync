from __future__ import annotations

import base64
import time
from typing import Iterable

AES_KEY = "G9uX0Fjd"


def xor_encrypt_decrypt(data: str, key: str) -> str:
    if not key:
        return data
    return "".join(chr(ord(ch) ^ ord(key[i % len(key)])) for i, ch in enumerate(data))


def b64_iso_8859_1(text: str) -> str:
    return base64.b64encode(text.encode("iso-8859-1", errors="strict")).decode("ascii")


def b64_utf8(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def make_login_payload(email: str, password: str, login_pwd_key: str) -> dict[str, str]:
    """Build the same login payload as Bryton Active.

    Decompiled logic:
      password = Base64( XOR(raw_password, loginPwdKey) ) using ISO-8859-1 bytes
      key      = Base64( XOR(f"{unix+86400} {loginPwdKey}", loginPwdKey) )
    """
    pwd_xor = xor_encrypt_decrypt(password, login_pwd_key)
    expires_and_key = f"{int(time.time()) + 86400} {login_pwd_key}"
    key_xor = xor_encrypt_decrypt(expires_and_key, login_pwd_key)
    return {
        "email": email,
        "password": b64_iso_8859_1(pwd_xor),
        "key": b64_utf8(key_xor),
    }


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        return data
    pad = data[-1]
    if pad < 1 or pad > 16:
        return data
    if data[-pad:] != bytes([pad]) * pad:
        return data
    return data[:-pad]


def decrypt_bryton_aes(cipher_text_b64: str, aes_key: str = AES_KEY) -> str:
    """Decrypt Bryton announcement values exactly like AESUtil.java.

    Java logic:
      key = SHA-256(keyInput UTF-8)
      raw = Base64.decode(encryptedData64, NO_WRAP)
      iv = raw[0:16]
      ciphertext = raw[16:]
      AES/CBC/PKCS5Padding
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Hash import SHA256
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Installa pycryptodome: pip install pycryptodome") from exc

    raw = base64.b64decode(cipher_text_b64)
    if len(raw) <= 16:
        raise ValueError("Payload AES Bryton non valido: meno di 17 byte dopo Base64")

    key_bytes = SHA256.new(aes_key.encode("utf-8")).digest()
    iv = raw[:16]
    encrypted = raw[16:]

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
    plain = _pkcs7_unpad(cipher.decrypt(encrypted))
    return plain.decode("utf-8")
