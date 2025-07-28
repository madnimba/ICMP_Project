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
            total_bytes = 0
            start_time = time.time()
            packet_count = 0 
            expected_seq = 0

            while True:
                mss = conn.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
                #print(f"[SERVER] Current TCP MSS: {mss} bytes")
                data = conn.recv(mss if mss > 0 else 32768)
                if not data:
                    break
                    
                packet_size = len(data)
                total_bytes += packet_size
                packet_count += 1
                expected_seq += packet_size
                
                elapsed = time.time() - start_time
                if elapsed >= 2:
                    speed = (total_bytes / elapsed) / 1024
                    avg_packet_size = total_bytes / packet_count if packet_count > 0 else 0                                      
                    try:
                        current_mss = conn.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
                    except:
                        current_mss = "unknown"

                    print(f"[SERVER] Speed: {speed:.2f} KB/s | Avg: {avg_packet_size:.0f}B | MSS: {current_mss}")

                    # Reset counters
                    total_bytes = 0
                    packet_count = 0
                    start_time = time.time()

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
