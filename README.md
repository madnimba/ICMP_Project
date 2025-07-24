# ICMP Blind Attack Demonstration

A educational demonstration of ICMP-based blind attacks against TCP connections, showing how attackers can disrupt network communications without being on the communication path.

## Project Overview

This project simulates two types of ICMP blind attacks:

1. **Connection Reset Attack** - Forces TCP connection termination using ICMP Destination Unreachable packets
2. **Throughput Reduction Attack** - Reduces connection speed using ICMP Fragmentation Needed packets

## Components

- `server.py` - TCP server that continuously sends data
- `client.py` - TCP client that downloads data and measures throughput
- `attacker.py` - Performs ICMP blind attacks with spoofed packets

## Requirements

- Python 3.x
- Linux system (for raw socket support)
- Root privileges (for attacker component)

## How to Run

### Step 1: Start the Server
```bash
python3 server.py
```

### Step 2: Start the Client
In a new terminal:
```bash
python3 client.py
```

### Step 3: Launch Attack
In a third terminal with root privileges:
```bash
sudo python3 attacker.py
```

Choose from the attack menu:
- `1` - Connection Reset Attack
- `2` - Throughput Reduction Attack  
- `3` - Both attacks

## Expected Results

### Normal Operation
- Client shows download speed around 97-98 KB/s with "(NORMAL)" indicator

### After Throughput Reduction Attack
- Speed drops to ~56 KB/s with "(SLOW)" indicator
- Client shows "MSS reduced due to ICMP attack simulation!"

### After Connection Reset Attack
- Client shows "Connection reset! ICMP Reset Attack successful."
- Connection terminates

## Attack Mechanism

### Connection Reset Attack
- Sends ICMP Destination Unreachable (Type 3, Code 1) packets
- Spoofs source IP as the server
- Includes embedded TCP header with guessed sequence numbers
- Scans port range to find the active connection

### Throughput Reduction Attack
- Sends ICMP Fragmentation Needed (Type 3, Code 4) packets
- Spoofs source IP as a router
- Forces MSS reduction by advertising smaller MTU
- Simulates network path MTU discovery manipulation


## Technical Details

- **Port Range**: Scans ephemeral ports (32768, 60999) for demo speed
- **Packet Crafting**: Uses raw sockets to create custom ICMP packets
- **Attack Detection**: Client simulates MSS reduction when flag file is created
- **Timing**: 50ms delay between attack packets to avoid flooding
