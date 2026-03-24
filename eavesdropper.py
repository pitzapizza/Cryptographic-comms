import socket
import threading

# Proxy settings
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 6000   # Client connects here

TARGET_HOST = '127.0.0.1'
TARGET_PORT = 5000   # Real server

# ---------- Pretty Print ----------
def print_intercepted(data, direction):
    print(f"\n[MITM] {direction} intercepted:")
    print(data)  # raw encrypted bytes

    try:
        print("[MITM] Attempt to decode:", data.decode())
    except:
        print("[MITM] Cannot decode (encrypted data)")

# ---------- Forwarding ----------
def forward(source, destination, direction):
    while True:
        try:
            data = source.recv(4096)
            if not data:
                break

            # 👀 Intercept here
            print_intercepted(data, direction)

            # Forward normally
            destination.sendall(data)

        except:
            break

# ---------- Start Proxy ----------
def start_proxy():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((LISTEN_HOST, LISTEN_PORT))
    proxy.listen(1)

    print(f"[MITM] Listening on {LISTEN_HOST}:{LISTEN_PORT}")

    client_socket, client_addr = proxy.accept()
    print(f"[MITM] Client connected: {client_addr}")

    # Connect to real server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((TARGET_HOST, TARGET_PORT))
    print("[MITM] Connected to real server")

    # Start bidirectional forwarding
    threading.Thread(target=forward, args=(client_socket, server_socket, "Client → Server"), daemon=True).start()
    threading.Thread(target=forward, args=(server_socket, client_socket, "Server → Client"), daemon=True).start()

    while True:
        pass  # keep alive

# ---------- Run ----------
if __name__ == "__main__":
    start_proxy()