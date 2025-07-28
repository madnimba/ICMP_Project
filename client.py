import socket
import time
import struct

SERVER_IP = "10.0.0.1"     
SERVER_PORT = 8080
BUFFER_SIZE = 64 
SEQ_WINDOW = 65535
defense_enabled = False

def parse_icmp_error(cmsg_data):
    """Parse ICMP error message from ancillary data"""
    # This is highly dependent on platform (Linux uses sock_extended_err)
    # Format: struct sock_extended_err (32 bytes) + optional offender sockaddr
    ee_errno, ee_origin, ee_type, ee_code, ee_pad, ee_info, ee_data = struct.unpack("=BBBxII", cmsg_data[:12])
    return ee_type, ee_code

def is_seq_valid(seq, expected_seq):
    """Check if ICMP-embedded seq is within a valid window"""
    return abs(seq - expected_seq) <= SEQ_WINDOW


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("10.0.0.2", 0))
   
    # Enable receiving of ICMP errors for this socket
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_RECVERR, 1)
    except:
        pass  
    
    # Set TCP_NODELAY to see immediate effects
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except:
        pass

    defense_enabled = input("Enable defense? (y/n): ")
    if defense_enabled == "y":
        defense_enabled = True
    else:
        defense_enabled = False
    
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
        expected_seq = 0

        print("[CLIENT] Starting download...")
        sock.setblocking(False)
        
        while True:
            try:
                # Use recv to get available data
                data = sock.recv(BUFFER_SIZE)
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
                        current_mss = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
                    except:
                        current_mss = "unknown"                   
                    
                    print(f"[CLIENT] Speed: {speed:.2f} KB/s | Avg: {avg_packet_size:.0f}B | MSS: {current_mss}")
                    
                    # Reset counters
                    total_bytes = 0
                    packet_count = 0
                    start_time = time.time()
                    
            except BlockingIOError:
                # No data available, check error queue
                try:
                    msg, ancdata, flags, addr = sock.recvmsg(1024, socket.CMSG_LEN(512), socket.MSG_ERRQUEUE)
                    for cmsg_level, cmsg_type, cmsg_data in ancdata:
                        if cmsg_level == socket.IPPROTO_IP:
                            icmp_type, icmp_code = parse_icmp_error(cmsg_data)
                            print(f"[CLIENT] ICMP Received: Type={icmp_type}, Code={icmp_code}")

                            if defense_enabled:
                                # Extract sequence number from ICMP payload
                                # Skip IP(20 bytes) + TCP header (20 bytes) to find seq
                                if len(msg) >= 24:
                                    embedded_seq = struct.unpack("!I", msg[16:20])[0]
                                    if not is_seq_valid(embedded_seq, expected_seq):
                                        print(f"[DEFENSE] Dropped ICMP (Seq {embedded_seq} out of window)")
                                        continue
                                print("[DEFENSE] Accepted ICMP")
                            else:
                                print("[DEFENSE] Disabled, ICMP applied")

                except BlockingIOError:
                    pass
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
