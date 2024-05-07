
for (( i=1; i<=10; i++ ))
    do
        # Run the curl command
        curl -i -X POST 128.105.102.4:8000/v2/models/densenet_onnx/infer \
        -H "Content-Type: application/json" \
        -d @payload.json
    done

# payload.json is created using createPayload.py