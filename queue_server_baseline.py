import http.client
import urllib.request
import urllib.error
import json
import numpy as np
import socket
import queue
import threading
from time import time, sleep


# Configuration
HOST = '128.105.102.4'  
PORTS = [65433, 65434, 65435]  # List of ports to listen on
TRITON_URL = 'http://128.105.102.4:8000/v2/models/roberta/infer'

data_queue = queue.Queue()
condition = threading.Condition()
lock = threading.Lock()

def safe_request(req, max_retries=3, timeout=10):
    retries = 0
    while retries < max_retries:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, http.client.RemoteDisconnected, ConnectionResetError) as e:
            print(f"Request failed: {e}. Retrying ({retries+1}/{max_retries})...")
            sleep(2 ** retries)  # Exponential back-off
            retries += 1
    raise Exception(f"All retries failed after {max_retries} attempts.")

def handle_client(connection, client_address):
    try:
        print(f"[NEW CONNECTION] {client_address} connected.")
        total_data = ""
        connection.settimeout(2)
        while True:
            try:
                data = connection.recv(1024).decode('utf-8')
                if not data:
                    break
                total_data += data
            except socket.timeout:
                break
        json_data = json.loads(total_data)
        with condition:
            data_queue.put((json_data, connection, time()))
            condition.notify()  # Signal that new data is available
    finally:
        print("Client sent the message. Now onto our queue!")

def model_inference_worker():
    while True:
        with condition:
            while data_queue.empty():
                condition.wait()  # Wait for data to be available
            request_data, client_connection, start_time = data_queue.get()

        target_latency = float(request_data['latency']) # unused in baseline (not SLO aware)
        inputs = {key: value for key, value in request_data.items() if key != 'latency'}
        json_body = json.dumps(inputs).encode('utf-8')

        req = urllib.request.Request(TRITON_URL, data=json_body, headers={'Content-Type': 'application/json'})

        try:
            response_body = safe_request(req)
            output_data = json.loads(response_body.decode('utf-8'))
            client_connection.sendall(json.dumps(output_data).encode('utf-8'))
            current_latency = time() - start_time
            print(f"Time taken: {current_latency}")
            res_file = open("results_baseline.txt", "a")
            res_file.write(str(current_latency)+"\n")
            res_file.close()
        except urllib.error.URLError as e:
            print(f"Failed to send request: {e.reason}")
        finally:
            client_connection.close()

def server_thread(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, port))
        server_socket.listen()
        print(f"Server listening on {HOST}:{port}")

        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def main():
    threading.Thread(target=model_inference_worker).start()
    threads = [threading.Thread(target=server_thread, args=(port,)) for port in PORTS]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    

if __name__ == "__main__":
    main()
