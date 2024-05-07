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

EMA_ALPHA = 0.1  # Smoothing factor for EMA
current_ema_deviation = 0
current_frequency_index = 6  # Start with a middle frequency as default
FREQUENCIES = [
    114750000, 216750000, 318750000, 420750000, 522750000, 624750000,
    726750000, 854250000, 930750000, 1032750000, 1122000000, 1236750000, 1300500000
]

MIN_FREQ_FILE="/sys/devices/17000000.gp10b/devfreq/17000000.gp10b/min_freq"
MAX_FREQ_FILE="/sys/devices/17000000.gp10b/devfreq/17000000.gp10b/max_freq"

def update_frequency(actual_latency, target_latency):
    global current_ema_deviation
    deviation = actual_latency - target_latency
    with lock:
        current_ema_deviation = EMA_ALPHA * deviation + (1 - EMA_ALPHA) * current_ema_deviation

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

def frequency_management_worker():
    global current_frequency_index
    min_freq_str = str(FREQUENCIES[current_frequency_index])
    max_freq_str = min_freq_str
    direction = 0
    while True:
        sleep(10)  # Sleep outside the lock
        with lock:
            target_frequency_index = current_frequency_index
            if current_ema_deviation > 0 and current_frequency_index < len(FREQUENCIES) - 1:
                target_frequency_index += 1  # Increase frequency
                direction=1
            elif current_ema_deviation < 0 and current_frequency_index > 0:
                target_frequency_index -= 1  # Decrease frequency
                direction=-1

            if target_frequency_index != current_frequency_index:
                current_frequency_index = target_frequency_index
                # Prepare the strings to write outside of the locked section
                min_freq_str = str(FREQUENCIES[current_frequency_index])
                max_freq_str = min_freq_str

        # Perform file writing outside of the lock
        try:
            if direction==1:
                with open(MAX_FREQ_FILE, 'w') as f:
                    print(f"Writing: {max_freq_str} to max frequency")
                    f.write(max_freq_str)
                with open(MIN_FREQ_FILE, 'w') as f:
                    print(f"Writing: {min_freq_str} to min frequency")
                    f.write(min_freq_str)
            if direction==-1:
                with open(MIN_FREQ_FILE, 'w') as f:
                    print(f"Writing: {min_freq_str} to min frequency")
                    f.write(min_freq_str)
                with open(MAX_FREQ_FILE, 'w') as f:
                    print(f"Writing: {max_freq_str} to max frequency")
                    f.write(max_freq_str)
            
            print(f"Updated GPU frequency to {FREQUENCIES[current_frequency_index]} Hz")
            direction=-1
        except IOError as e:
            print(f"Error writing to frequency files: {e}")



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

        target_latency = float(request_data['latency'])
        inputs = {key: value for key, value in request_data.items() if key != 'latency'}
        json_body = json.dumps(inputs).encode('utf-8')
        print(json_body)

        req = urllib.request.Request(TRITON_URL, data=json_body, headers={'Content-Type': 'application/json'})

        try:
            response_body = safe_request(req)
            output_data = json.loads(response_body.decode('utf-8'))
            client_connection.sendall(json.dumps(output_data).encode('utf-8'))
            current_latency = time() - start_time
            print(f"Time taken: {current_latency}")
            res_file = open("results_adapter.txt", "a")
            with lock:
                curr_freq = str(FREQUENCIES[current_frequency_index])
            res_file.write(curr_freq+","+str(current_latency)+"\n")
            res_file.close()
            update_frequency(current_latency, target_latency)
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
    threading.Thread(target=frequency_management_worker).start()
    threads = [threading.Thread(target=server_thread, args=(port,)) for port in PORTS]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    

if __name__ == "__main__":
    main()
