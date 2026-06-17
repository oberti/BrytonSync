from __future__ import annotations

import base64
import hashlib
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

AES_KEY = "G9uX0Fjd"


def _java_xor(data: str, key: str) -> str:
    if not key:
        return data
    return "".join(chr(ord(ch) ^ ord(key[i % len(key)])) for i, ch in enumerate(data))


def _b64_iso_8859_1(text: str) -> str:
    return base64.b64encode(text.encode("latin-1", errors="strict")).decode("ascii")


def decrypt_bryton_aes(encrypted_data64: str, key_input: str = AES_KEY) -> str:
    # Java AESUtil: key = SHA-256(key_input), payload = Base64(IV + ciphertext), AES/CBC/PKCS5Padding
    key = hashlib.sha256(key_input.encode("utf-8")).digest()
    payload = base64.b64decode(encrypted_data64)
    iv, ciphertext = payload[:16], payload[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size).decode("utf-8")


def make_login_payload(email: str, password: str, login_pwd_key: str) -> dict[str, str]:
    enc_pwd = _java_xor(password, login_pwd_key)
    password_b64 = _b64_iso_8859_1(enc_pwd)

    expires = int(time.time()) + 86400
    key_raw = f"{expires} {login_pwd_key}"
    enc_key = _java_xor(key_raw, login_pwd_key)
    key_b64 = base64.b64encode(enc_key.encode("utf-8", errors="surrogatepass")).decode("ascii")

    return {"email": email, "password": password_b64, "key": key_b64}
