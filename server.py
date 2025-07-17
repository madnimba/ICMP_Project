import socket
import time

SERVER_IP = "127.0.0.1"  # Change to 10.0.0.1 if needed
SERVER_PORT = 8080

def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen(1)
    print(f"[SERVER] Listening on {SERVER_IP}:{SERVER_PORT}")

    conn, addr = server_sock.accept()
    print(f"[SERVER] Client connected from {addr}")

    try:
        message = b"X" * 1024  # 1 KB data chunk
        while True:
            conn.sendall(message)
            time.sleep(0.01)  # Send continuously
    except BrokenPipeError:
        print("[SERVER] Connection reset by client.")
    finally:
        conn.close()
        server_sock.close()

if __name__ == "__main__":
    start_server()
