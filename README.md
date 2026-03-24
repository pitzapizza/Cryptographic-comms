<div align="center">

```
 ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗      ██████╗ ██████╗ ███╗   ███╗███╗   ███╗███████╗
██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗    ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔════╝
██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║    ██║     ██║   ██║██╔████╔██║██╔████╔██║███████╗
██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║    ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║╚════██║
╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║███████║
 ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝      ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝
```

**End-to-end encrypted real-time chat using a custom Mandelbrot Set key generator + AES encryption**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![Flask](https://img.shields.io/badge/Flask-SocketIO-000000?style=flat-square&logo=flask&logoColor=white)](https://flask-socketio.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

</div>

---

## 🔐 What is this?

**Cryptographic Comms** is a real-time encrypted messaging demo that replaces standard key derivation with an unconventional approach — using the **Mandelbrot Set** as a chaotic, deterministic key generator.

Two browser tabs act as **SERVER** and **CLIENT**. They share a seed phrase, independently derive the same 256-bit AES key from it using Mandelbrot orbit values, and then communicate over WebSockets with every message encrypted using a custom **CHM (Chain Hash Mode)** on top of AES-ECB. The raw ciphertext travelling on the wire is visible in real time at the bottom of the UI.

> This is a cryptography research/demo project — not intended for production use.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌀 **Mandelbrot Key Gen** | Seed phrase → SHA-256 → complex number `c` → orbit iterations → 256-bit key |
| 🔒 **CHM Encryption** | Custom chain mode: each AES block is XOR'd with SHA-256 of the previous ciphertext block |
| ⚡ **Real-time WebSockets** | Flask-SocketIO backend, Socket.IO React client — sub-millisecond delivery |
| 👁 **Wire Intercept View** | Bottom panel shows the raw hex ciphertext as it travels socket-to-socket |
| 🖥 **Two-role UI** | Open two tabs, pick SERVER or CLIENT — fully independent sessions |
| 🧹 **Secure Wipe** | Sensitive buffers (seed, key material) are zeroed from memory after use |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER TAB 1                        │
│                     role: SERVER                            │
│   seed ──► mandelbrot_key() ──► 256-bit AES key             │
│            React UI  ◄──► Socket.IO client                  │
└──────────────────────┬──────────────────────────────────────┘
                       │  WebSocket (encrypted payload)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FLASK-SOCKETIO SERVER                     │
│                     app.py  :5000                           │
│                                                             │
│  register()  ──► store role + real socket.id                │
│  init_key()  ──► mandelbrot_key(seed) → store key           │
│  send_msg()  ──► chm_encrypt() → broadcast cipher           │
│               ──► chm_decrypt() → emit plaintext to recv    │
└──────────────────────┬──────────────────────────────────────┘
                       │  WebSocket (encrypted payload)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER TAB 2                        │
│                     role: CLIENT                            │
│   seed ──► mandelbrot_key() ──► same 256-bit AES key        │
│            React UI  ◄──► Socket.IO client                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌀 How the Mandelbrot Key Generator Works

Standard key derivation uses PBKDF2 or bcrypt. This project takes a different path.

```
seed string
    │
    ▼
SHA-256(seed)
    │
    ├─ bytes [0:8]  ──► real part of c  (divided by 10^10)
    └─ bytes [8:16] ──► imag part of c  (divided by 10^10)
    
    c = real + imag·i  (a point in the complex plane)
    
    z₀ = 0
    zₙ₊₁ = zₙ² + c   (iterate up to 500 times while |z| ≤ 2)
    
    each iteration:  val = floor((|z| mod 1) × 10⁶)
                     append val as 4 bytes to buffer
    
    final_key = SHA-256(buffer)   ──► 32 bytes = 256-bit AES key
```

The Mandelbrot orbit produces a chaotic, non-repeating byte sequence that is entirely determined by the seed — identical seeds always produce identical keys, but tiny seed changes produce completely different orbits and keys.

---

## 🔐 CHM Encryption (Chain Hash Mode)

AES-ECB alone is insecure for multi-block messages (identical blocks produce identical ciphertext). CHM fixes this with SHA-256 chaining:

```
plaintext  ──► PKCS7 pad ──► split into 16-byte blocks

block₀:   XOR(block₀,  SHA-256(key)[:16])  ──► AES-ECB ──► cipher₀
block₁:   XOR(block₁,  SHA-256(cipher₀)[:16]) ──► AES-ECB ──► cipher₁
block₂:   XOR(block₂,  SHA-256(cipher₁)[:16]) ──► AES-ECB ──► cipher₂
  ...

ciphertext = cipher₀ ‖ cipher₁ ‖ cipher₂ ‖ ...
```

Each block's encryption depends on all previous blocks. Changing one character anywhere alters every subsequent block.

---

## 📁 Project Structure

```
cryptographic-comms/
│
├── server/
│   ├── app.py              # Flask-SocketIO server, event handlers
│   └── crypto_core.py      # Mandelbrot key gen, CHM encrypt/decrypt, secure wipe
│
├── client/
│   └── src/
│       ├── App.js          # React UI — role picker, chat, wire intercept panel
│       ├── App.css         # Dark terminal aesthetic styles
│       └── index.css       # Base reset + font imports
│
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### 1 — Clone

```bash
git clone https://github.com/pitzapizza/Cryptographic-comms.git
cd Cryptographic-comms
```

### 2 — Backend

```bash
cd server
pip install flask flask-socketio flask-cors pycryptodome
python app.py
```

Server runs at `http://localhost:5000`

### 3 — Frontend

```bash
cd client
npm install
npm install socket.io-client
npm start
```

Frontend runs at `http://localhost:3000`

### 4 — Use it

1. Open **two browser tabs** at `http://localhost:3000`
2. Tab 1 → click **SERVER** &nbsp;|&nbsp; Tab 2 → click **CLIENT**
3. In **both tabs** — type the same seed phrase and click **INIT KEY**
4. Start chatting — messages are encrypted before leaving your tab
5. Watch the **raw ciphertext** appear in the bottom panel as each message travels the wire

---

## 🔬 Socket Events Reference

| Event | Direction | Payload | Description |
|---|---|---|---|
| `register` | client → server | `{ sid, role }` | Register tab as server or client |
| `init_key` | client → server | `{ sid, seed }` | Derive and store Mandelbrot key |
| `key_ready` | server → client | `{ key_hex }` | Key confirmed, returns hex for display |
| `send_message` | client → server | `{ sid, role, message }` | Send plaintext to be encrypted |
| `receive_encrypted` | server → all | `{ from_role, cipher }` | Raw ciphertext broadcast (wire view) |
| `receive_message` | server → recipient | `{ from_role, message }` | Decrypted plaintext to intended recipient only |

---

## 📜 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built with chaos theory and bad ideas &nbsp;·&nbsp; <a href="https://github.com/pitzapizza">pitzapizza</a></sub>
</div>