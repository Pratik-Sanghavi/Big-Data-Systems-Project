import socket
import json
import numpy as np
import threading

def send_data_to_server(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Connecting to {host}:{port}")
        sock.connect((host, port))

        data['latency'] = 2
        json_data = json.dumps(data).encode('utf-8')
        sock.sendall(json_data)

        response = sock.recv(10000)
        print(f"Received from {port}: {response.decode('utf-8')}")

def load_data():
    with open('payload.json', 'r') as f:
        data = json.load(f)
    data["inputs"][0]["shape"] = [8, 3, 224, 224]
    data["inputs"][0]["data"] = 8*[data["inputs"][0]["data"]]
    return data

def main():
    HOST = '128.105.102.4'
    PORT = 65433
    data = load_data()

    # Creating threads for sending data to different ports
    threads = []
    for j in range(50):
        print(f"Iteration {j}")
        for i in range(3):
            thread = threading.Thread(target=send_data_to_server, args=(HOST, PORT + i, data))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

if __name__ == "__main__":
    main()
