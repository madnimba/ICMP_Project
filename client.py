import socket
import time
import threading

SERVER_IP = "127.0.0.1"   # Change to 10.0.0.1 if needed
SERVER_PORT = 8080
CLIENT_IP = "127.0.0.1"   # For attacker reference
BUFFER_SIZE = 1460        # Initial MSS (simulating normal)
reduced_mss = False       # Flag for throughput attack simulation

def listen_for_attack():
    """
    Simulate detection: If attacker sends a file 'reduce_mss.flag',
    reduce MSS in client.
    """
    global BUFFER_SIZE, reduced_mss
    while True:
        try:
            with open("reduce_mss.flag", "r") as f:
                BUFFER_SIZE = 472
                reduced_mss = True
                print("[CLIENT] MSS reduced due to ICMP attack simulation!")
                break
        except FileNotFoundError:
            time.sleep(0.5)

def start_client():
    global BUFFER_SIZE
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    print("[CLIENT] Connected to server. Starting download...")

    attack_thread = threading.Thread(target=listen_for_attack, daemon=True)
    attack_thread.start()

    total_bytes = 0
    start_time = time.time()
    try:
        while True:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            total_bytes += len(data)
            elapsed = time.time() - start_time
            if elapsed >= 2:
                speed = (total_bytes / elapsed) / 1024
                print(f"[CLIENT] Download speed: {speed:.2f} KB/s {'(SLOW)' if reduced_mss else '(NORMAL)'}")
                total_bytes = 0
                start_time = time.time()
    except ConnectionResetError:
        print("[CLIENT] Connection reset! ICMP Reset Attack successful.")
    finally:
        sock.close()

if __name__ == "__main__":
    start_client()
