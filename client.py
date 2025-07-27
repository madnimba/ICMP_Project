import socket
import time

SERVER_IP = "10.0.0.1"     
SERVER_PORT = 8080
BUFFER_SIZE = 1024          
CLIENT_PORT = 55555      

def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind to a specific client port for debugging
    #sock.bind(("10.0.0.2", CLIENT_PORT))
    sock.bind(("10.0.0.2", 0))
    # Do NOT bind — let the OS handle it
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    
    # Enable socket options to receive ICMP errors and better detect changes
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Enable receiving of ICMP errors for this socket
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_RECVERR, 1)
    except:
        pass  # Not all systems support this
    
    # Set TCP_NODELAY to see immediate effects
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except:
        pass
    
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        print(f"[CLIENT] Connected to {SERVER_IP}:{SERVER_PORT}")
        print(f"[CLIENT] Local port: {sock.getsockname()[1]}") 
        
        # Try to get initial TCP MSS
        try:
            mss = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
            print(f"[CLIENT] Initial TCP MSS: {mss} bytes")
        except:
            print("[CLIENT] Could not retrieve TCP MSS")
        
        total_bytes = 0
        start_time = time.time()
        packet_count = 0   

        print("[CLIENT] Starting download...")
        
        while True:
            try:
                # Use recv to get available data
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    break
                    
                packet_size = len(data)
                total_bytes += packet_size
                packet_count += 1
                
                elapsed = time.time() - start_time
                if elapsed >= 2:
                    speed = (total_bytes / elapsed) / 1024
                    avg_packet_size = total_bytes / packet_count if packet_count > 0 else 0
                    
                    
                    # Check current TCP MSS
                    try:
                        current_mss = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
                    except:
                        current_mss = "unknown"
                    
                    
                    print(f"[CLIENT] Speed: {speed:.2f} KB/s | Avg: {avg_packet_size:.0f}B | MSS: {current_mss}")
                    
                    # Reset counters
                    total_bytes = 0
                    packet_count = 0
                    start_time = time.time()
                    
            except socket.error as e:
                print(f"[CLIENT] Socket error: {e}")
                if "Connection reset" in str(e):
                    print("[CLIENT] *** CONNECTION RESET ***")
                elif "Message too long" in str(e):
                    print("[CLIENT] *** MTU/MSS REDUCTION DETECTED ***")
                break
                
    except ConnectionRefusedError:
        print(f"[CLIENT] Cannot connect to {SERVER_IP}:{SERVER_PORT}")
        print("[CLIENT] Make sure server is running and IP is reachable")
    except ConnectionResetError:
        print("[CLIENT] *** CONNECTION RESET ***")
    except OSError as e:
        print(f"[CLIENT] Network error: {e}")
        if "No route to host" in str(e):
            print("[CLIENT] *** HOST UNREACHABLE***")
    finally:
        sock.close()

if __name__ == "__main__":
    start_client()
