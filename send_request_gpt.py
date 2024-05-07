import socket
import json
import numpy as np
import threading

def send_data_to_server(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Connecting to {host}:{port}")
        sock.connect((host, port))

        data['latency'] = 1
        json_data = json.dumps(data).encode('utf-8')
        sock.sendall(json_data)

        response = sock.recv(10000)
        print(f"Received from {port}: {response.decode('utf-8')}")

def load_data():
    input_ids = np.random.randint(0, 30000, size=(1, 128))
    attention_mask = np.ones((1, 128), dtype=np.int32)

    data = {
        "inputs": [
            {
                "name": "input_ids",
                "datatype": "INT32",
                "shape": input_ids.shape,
                "data": input_ids.tolist()
            },
            {
                "name": "attention_mask",
                "datatype": "FP32",
                "shape": attention_mask.shape,
                "data": attention_mask.tolist()
            }
        ],
        "outputs": [
            {
                "name": "1531",
                "datatype": "FP32",
                "shape": [768]
            }
        ]
    }
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