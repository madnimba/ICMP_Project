# ICMP Blind Attack Demonstration

A realistic demonstration of ICMP-based blind attacks against TCP connections, showing how attackers can disrupt network communications by sending crafted ICMP packets.

## Project Overview

This project demonstrates two types of real ICMP blind attacks:

1. **Connection Reset Attack** - Forces TCP connection termination using ICMP Destination Unreachable packets
2. **Throughput Reduction Attack** - Reduces connection speed using ICMP Fragmentation Needed packets

## Components

- `server.py` - TCP server that continuously sends data
- `client.py` - TCP client that downloads data and measures throughput  
- `attacker.py` - Performs real ICMP blind attacks with crafted packets

## Requirements

- Python 3.x
- Linux system (for raw socket support)
- Root privileges (for attacker component)
- Network configuration for IP aliases

## Network Setup

Before running, add an IP alias for the demonstration:

```bash
sudo ip addr add 10.0.0.1/32 dev lo
```

This creates a local IP address that allows for more realistic network simulation.

## How to Run

### Step 1: Set up Network
```bash
sudo ip addr add 10.0.0.1/32 dev lo
```

### Step 2: Start the Server
```bash
python3 server.py
```

### Step 3: Start the Client
In a new terminal:
```bash
python3 client.py
```

### Step 4: Launch Attack
In a third terminal with root privileges:
```bash
sudo python3 attacker.py
```

Choose from the attack menu:
- `1` - Connection Reset Attack
- `2` - Throughput Reduction Attack  
- `3` - Both attacks

Then select scanning strategy:
- `1` - Random sampling (1000 random ports) - realistic and fast
- `2` - Sequential scan (multiple passes) - systematic coverage
- `3` - Full brute force (all ports) - guaranteed but slow

## Expected Results

### Normal Operation
- Client shows download speed around 97-98 KB/s
- Server shows packets being sent regularly

### After Real ICMP Attacks
- **Throughput Reduction**: Client TCP stack automatically reduces MSS, causing slower throughput and smaller packet sizes
- **Connection Reset**: Client receives "CONNECTION RESET BY ICMP ATTACK" and connection terminates
- **Server**: Detects broken pipe or connection reset

## Attack Mechanism

### Connection Reset Attack (ICMP Type 3, Code 1)
- Sends ICMP Destination Unreachable packets to client
- Spoofs source IP as the server (10.0.0.1)  
- Includes embedded TCP header with guessed sequence numbers
- Client's TCP stack receives ICMP and terminates connection

### Throughput Reduction Attack (ICMP Type 3, Code 4)
- Sends ICMP Fragmentation Needed packets to client
- Spoofs source IP as intermediate router (192.168.1.1)
- Advertises smaller MTU (512 bytes) via Next-Hop MTU field
- Client's TCP stack automatically reduces MSS for path MTU discovery

## Key Improvements Over Simulation

✅ **Real Network Attacks**: No flag file simulation - actual ICMP packets sent and processed

✅ **Automatic Detection**: Attacker can auto-detect active connection ports using netstat

✅ **Realistic Behavior**: Client responds naturally to ICMP packets via kernel TCP stack

✅ **Proper Spoofing**: Source IP spoofing simulates real-world attack scenarios


## Technical Details

- **Port Detection**: Uses netstat to find actual client connection port
- **Packet Crafting**: Raw sockets create authentic ICMP packets with embedded TCP headers
- **Sequence Number Guessing**: Multiple attempts with random 32-bit sequence numbers
- **Attack Timing**: Optimized delays to avoid flooding while maintaining effectiveness

## Defending Against These Attacks

1. **Ingress Filtering (BCP 38)** - Block packets with spoofed source addresses at network edge
2. **ICMP Rate Limiting** - Limit ICMP message processing rate in TCP stack
3. **TCP Authentication** - Use TCP MD5 signatures (RFC 2385) or IPSec
4. **Firewall Rules** - Filter suspicious ICMP traffic patterns
5. **TCP Sequence Randomization** - Makes sequence number guessing harder
