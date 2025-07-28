import socket
import time

SERVER_IP = "10.0.0.1"     
SERVER_PORT = 8080  

def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind((SERVER_IP, SERVER_PORT))
        server_sock.listen(1)
        print(f"[SERVER] Listening on {SERVER_IP}:{SERVER_PORT}")
        print("[SERVER] Waiting for client connection...")

        conn, addr = server_sock.accept()
        print(f"[SERVER] Client connected from {addr[0]}:{addr[1]}")
        print(f"[SERVER] Connection established, sending data...")

        try:
            packets_sent = 0

            while True:
                mss = conn.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
                print(f"[SERVER] Current TCP MSS: {mss} bytes")
                # Send exactly one MSS-sized message
                data = b'X' * mss
                conn.sendall(data)
                time.sleep(0.05)  # Very short delay to allow continuous data flow

        except BrokenPipeError:
            print("[SERVER] *** Client disconnected ***")
        except ConnectionResetError:
            print("[SERVER] *** Connection reset by client ***")
        except Exception as e:
            print(f"[SERVER] Connection error: {e}")
        finally:
            conn.close()
            print("[SERVER] Client connection closed")
            
    except OSError as e:
        print(f"[SERVER] Server error: {e}")
        if "Cannot assign requested address" in str(e):
            print("[SERVER] Tip: You may need to add IP alias: sudo ip addr add 10.0.0.1/32 dev lo")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_server()
