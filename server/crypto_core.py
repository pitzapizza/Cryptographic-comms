from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import hashlib

BLOCK_SIZE = 16

# ---------- Secure Wipe ----------
def secure_wipe(data):
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = 0

# ---------- Padding ----------
def pad(data):
    pad_len = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + bytes([pad_len] * pad_len)

def unpad(data):
    return data[:-data[-1]]

# ---------- XOR ----------
def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

# ---------- SHA256 ----------
def sha256(data):
    h = SHA256.new()
    h.update(bytes(data))  # avoid accidental mutation issues
    return h.digest()

# =========================================================
# 🔥 SECURE Mandelbrot Key Generator
# =========================================================
def mandelbrot_key(seed: bytearray, iterations=500):
    import math

    seed_hash = hashlib.sha256(bytes(seed)).digest()

    real = int.from_bytes(seed_hash[:8], 'big') / 10**10
    imag = int.from_bytes(seed_hash[8:16], 'big') / 10**10

    c = complex(real, imag)
    z = 0 + 0j

    values = bytearray()

    for _ in range(iterations):
        z = z*z + c

        # 🔥 ESCAPE CONDITION (prevents infinity)
        if abs(z) > 2:
            break

        # 🔥 SAFE VALUE EXTRACTION
        val = int((abs(z) % 1) * 1e6)  # keep within range
        values.extend(val.to_bytes(4, 'big'))

    # fallback if too few iterations
    if len(values) < 32:
        values.extend(hashlib.sha256(bytes(values)).digest())

    final_key = hashlib.sha256(values).digest()

    secure_wipe(values)

    return final_key

# =========================================================
# 🔐 CHM Encryption (hardened)
# =========================================================
def chm_encrypt(message, key):
    cipher = AES.new(bytes(key), AES.MODE_ECB)

    message_bytes = pad(message.encode())
    blocks = [message_bytes[i:i+BLOCK_SIZE] for i in range(0, len(message_bytes), BLOCK_SIZE)]

    ciphertext = bytearray()
    prev_hash = sha256(key)

    for block in blocks:
        xored = xor_bytes(block, prev_hash[:BLOCK_SIZE])
        encrypted = cipher.encrypt(xored)

        ciphertext.extend(encrypted)
        prev_hash = sha256(encrypted)

    return bytes(ciphertext)

# =========================================================
# 🔓 CHM Decryption (hardened)
# =========================================================
def chm_decrypt(ciphertext, key):
    cipher = AES.new(bytes(key), AES.MODE_ECB)

    blocks = [ciphertext[i:i+BLOCK_SIZE] for i in range(0, len(ciphertext), BLOCK_SIZE)]

    plaintext = bytearray()
    prev_hash = sha256(key)

    for block in blocks:
        decrypted = cipher.decrypt(block)
        original = xor_bytes(decrypted, prev_hash[:BLOCK_SIZE])

        plaintext.extend(original)
        prev_hash = sha256(block)

    result = unpad(bytes(plaintext)).decode(errors='ignore')

    secure_wipe(plaintext)  # 🔥 wipe sensitive buffer

    return result