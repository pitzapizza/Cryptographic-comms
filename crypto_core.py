from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import hashlib

BLOCK_SIZE = 16

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
    h.update(data)
    return h.digest()

# =========================================================
# 🔥 Mandelbrot-based Key Generator
# =========================================================
def mandelbrot_key(seed: str, iterations=1000):
    """
    Generates a deterministic 256-bit key using Mandelbrot iteration.
    Both users must use SAME seed.
    """
    # Convert seed → complex number
    seed_hash = hashlib.sha256(seed.encode()).hexdigest()
    
    real = int(seed_hash[:16], 16) / 10**18
    imag = int(seed_hash[16:32], 16) / 10**18
    
    c = complex(real, imag)
    z = 0 + 0j

    values = []

    for _ in range(iterations):
        z = z*z + c
        values.append(abs(z))

    # Convert values → bytes → hash → 32-byte AES key
    byte_data = ''.join([str(v) for v in values]).encode()
    final_key = hashlib.sha256(byte_data).digest()

    return final_key

# =========================================================
# 🔐 CHM Encryption
# =========================================================
def chm_encrypt(message, key):
    cipher = AES.new(key, AES.MODE_ECB)

    message = pad(message.encode())
    blocks = [message[i:i+BLOCK_SIZE] for i in range(0, len(message), BLOCK_SIZE)]

    ciphertext = b''
    prev_hash = sha256(key)

    for block in blocks:
        xored = xor_bytes(block, prev_hash[:BLOCK_SIZE])
        encrypted = cipher.encrypt(xored)

        ciphertext += encrypted
        prev_hash = sha256(encrypted)

    return ciphertext

# =========================================================
# 🔓 CHM Decryption
# =========================================================
def chm_decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)

    blocks = [ciphertext[i:i+BLOCK_SIZE] for i in range(0, len(ciphertext), BLOCK_SIZE)]

    plaintext = b''
    prev_hash = sha256(key)

    for block in blocks:
        decrypted = cipher.decrypt(block)
        original = xor_bytes(decrypted, prev_hash[:BLOCK_SIZE])

        plaintext += original
        prev_hash = sha256(block)

    return unpad(plaintext).decode(errors='ignore')