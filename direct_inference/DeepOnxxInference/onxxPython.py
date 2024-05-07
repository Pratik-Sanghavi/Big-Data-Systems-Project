import json
from urllib import request
from urllib.error import HTTPError

url = 'http://128.105.102.4:8000/v2/models/densenet_onnx/infer'
headers = {'Content-Type': 'application/json'}

for i in range(100):
    try:
        with open('payload.json') as payload_file:
            payload_data = payload_file.read()

        req = request.Request(url, headers=headers, data=payload_data.encode('utf-8'))
        response = request.urlopen(req)
        
        print(response.getcode())
    except HTTPError as e:
        print(f"HTTP Error: {e.code}, {e.reason}")
    except Exception as e:
        print(f"Error: {e}")