import json
from PIL import Image
import numpy as np

def preprocess_image(image_path, target_size=(224, 224)):
    # Load the image
    image = Image.open(image_path)
    
    # Resize and convert the image to the target size
    image = image.resize(target_size).convert('RGB')
    
    # Convert the image to a numpy array
    image_array = np.array(image)
    
    # Normalize the pixel values to the range [0, 1]
    image_array = image_array.astype(np.float32) / 255.0
    
    # Reshape the image data for batch processing
    image_array = np.transpose(image_array, (2, 0, 1))
    image_array = np.expand_dims(image_array, axis=0)
    
    # Flatten the image array to send as a flat list
    flat_image_array = image_array.flatten().tolist()
    
    return flat_image_array

def create_payload(image_path):
    # Process the image and get the serialized array
    serialized_image = preprocess_image(image_path)
    
    # Create the payload dictionary
    payload = {
        "inputs": [
            {
                "name": "data_0",
                "datatype": "FP32",
                "shape": [3, 224, 224],
                "data": serialized_image
            }
        ]
    }
    
    # Save the payload to a JSON file
    payload_file = 'payload.json'
    with open(payload_file, 'w') as f:
        json.dump(payload, f)
    
    return payload_file

def print_curl_command(server_url, model_name, payload_file):
    curl_command = (
        f"curl -i -X POST {server_url}/v2/models/{model_name}/infer "
        f"-H \"Content-Type: application/json\" "
        f"-d @{payload_file}"
    )
    print("Run the following command in your terminal:")
    print(curl_command)

# Replace with your image path and server details
image_path = 'path_to_your_image.jpg'
server_url = '128.105.102.4:8000'
model_name = 'densenet_onnx'

# Create payload
payload_file = create_payload(image_path)

# Print the curl command
print_curl_command(server_url, model_name, payload_file)
