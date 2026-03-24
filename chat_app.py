import socket
import threading
from crypto_core import chm_encrypt, chm_decrypt, mandelbrot_key, secure_wipe

HOST = '127.0.0.1'
PORT = 5000

# ---------- Secure Seed Handling ----------
def get_shared_seed():
    # Avoid storing as plain string
    seed_input = input("Enter shared seed (OOB verified): ").encode()
    return bytearray(seed_input)

# Generate key securely
SEED = get_shared_seed()
KEY = bytearray(mandelbrot_key(SEED))

secure_wipe(SEED)  # 🔥 destroy seed immediately

# ---------- Receive Messages ----------
def receive_messages(sock):
    global KEY
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break

            try:
                decrypted = chm_decrypt(data, KEY)
                print(f"\n[Received]: {decrypted}")
            except:
                print("\n[Warning]: Message could not be decrypted")

        except:
            break

# ---------- Send Messages ----------
def send_messages(sock):
    global KEY
    while True:
        msg = input()

        if msg.lower() == "exit":
            secure_wipe(KEY)  # 🔥 wipe key before exit
            sock.close()
            break

        encrypted = chm_encrypt(msg, KEY)
        sock.sendall(encrypted)

# ---------- Server ----------
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print("[*] Waiting for connection...")
    conn, addr = server.accept()
    print(f"[+] Connected to {addr}")

    threading.Thread(target=receive_messages, args=(conn,), daemon=True).start()
    send_messages(conn)

# ---------- Client ----------
def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 6000))  # proxy / MITM demo
    print("[+] Connected to server")

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()
    send_messages(client)

# ---------- Main ----------
if __name__ == "__main__":
    mode = input("Start as server (s) or client (c): ").lower()

    if mode == 's':
        start_server()
    elif mode == 'c':
        start_client()