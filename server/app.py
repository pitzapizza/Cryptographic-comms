from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from crypto_core import chm_encrypt, chm_decrypt, mandelbrot_key, secure_wipe

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# { custom_sid: { 'role': str, 'key': bytearray, 'socket_id': str } }
clients = {}

# reverse lookup: socket_id -> custom_sid
socket_to_custom = {}

@socketio.on('connect')
def handle_connect():
    print(f"[CONNECT] socket={request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    custom = socket_to_custom.pop(request.sid, None)
    if custom:
        clients.pop(custom, None)
    print(f"[DISCONNECT] socket={request.sid}")

@socketio.on('register')
def handle_register(data):
    custom_sid = data['sid']
    role       = data['role']
    socket_id  = request.sid          # real Socket.IO connection ID

    clients[custom_sid] = {
        'role':      role,
        'key':       None,
        'socket_id': socket_id        # store the real socket id
    }
    socket_to_custom[socket_id] = custom_sid
    print(f"[REGISTER] {custom_sid} as {role} (socket={socket_id})")

@socketio.on('init_key')
def init_key(data):
    custom_sid = data['sid']
    seed       = bytearray(data['seed'].encode())
    key        = bytearray(mandelbrot_key(seed))
    secure_wipe(seed)

    if custom_sid not in clients:
        clients[custom_sid] = {
            'role':      'unknown',
            'key':       None,
            'socket_id': request.sid
        }
    clients[custom_sid]['key'] = key

    emit('key_ready', {'key_hex': bytes(key).hex()})
    print(f"[KEY SET] {custom_sid}")

@socketio.on('send_message')
def handle_message(data):
    sender_custom = data['sid']
    sender_role   = data['role']
    msg           = data['message']

    sender = clients.get(sender_custom)
    if not sender or not sender.get('key'):
        emit('error', {'msg': 'No key for sender'})
        return

    encrypted  = chm_encrypt(msg, sender['key'])
    cipher_hex = encrypted.hex()

    # Broadcast raw cipher to ALL tabs (wire view)
    socketio.emit('receive_encrypted', {
        'from_role': sender_role,
        'cipher':    cipher_hex
    })

    # Find recipient by role
    recipient_role = 'server' if sender_role == 'client' else 'client'

    for custom_sid, info in clients.items():
        if info.get('role') == recipient_role and info.get('key'):
            try:
                plain = chm_decrypt(encrypted, info['key'])
            except Exception as e:
                plain = f"[DECRYPTION FAILED: {e}]"

            real_socket_id = info['socket_id']   # use the REAL socket id
            socketio.emit('receive_message', {
                'from_role': sender_role,
                'message':   plain
            }, to=real_socket_id)                 # deliver only to recipient's tab
            print(f"[DELIVERED] '{plain}' → {custom_sid} (socket={real_socket_id})")
            break

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)