import socket
import threading
from crypto_core import chm_encrypt, chm_decrypt, mandelbrot_key

HOST = '127.0.0.1'
PORT = 5000

# Shared seed (OOB verification required in real system)
SHARED_SEED = "secure-seed-123"

# Generate same key on both sides
KEY = mandelbrot_key(SHARED_SEED)

# ---------- Receive Messages ----------
def receive_messages(sock):
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
    while True:
        msg = input()
        if msg.lower() == "exit":
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
    #client.connect((HOST, PORT))
    client.connect(('127.0.0.1', 6000))  # connect to proxy instead of server
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