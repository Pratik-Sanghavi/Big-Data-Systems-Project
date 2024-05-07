import json

# Assuming 'processed_image' is your preprocessed and serialized image data
# data_0 = processed_image

# Path to your serialized image array text file
serialized_array_path = 'serializedImage.txt'

# Read the content of the file
with open(serialized_array_path, 'r') as file:
    # Assuming the file contains a Python list in string form
    serialized_array_str = file.read()

# Convert the string back to a Python list
# This uses `eval` which should ONLY be used if you're absolutely sure about the content of the file
# being safe and not containing any harmful code
processed_image = eval(serialized_array_str)

# Payload to send for inference
payload = {
    "inputs": [
        {
            "name": "data_0",
            "datatype": "FP32",
            "shape": [3, 224, 224],
            "data": processed_image
        }
    ]
}

# Save the payload to a file
with open('payload.json', 'w') as f:
    json.dump(payload, f)