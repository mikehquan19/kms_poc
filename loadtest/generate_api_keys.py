import requests
import time
import json
import os

num_keys = 120
base_url = "http://127.0.0.1:8000/api"
api_keys = []

for i in range(num_keys):
    if i < 100:
        # Generate the first 100 public keys that cannot call internal endpoint
        project = f"Public key {i + 1}"
        description = f"This is a project using public key {i + 1}"
        internal = "false"
    else:
        # Generate the last 20 internal keys that can call internal endpoint
        project = f"Internal key {i + 1}"
        description = f"This is a project using internal key {i + 1}"
        internal = "true"

    response = requests.post(
        f"{base_url}/keys",
        json={
            "project": project,
            "description": description,
            "internal": internal,
        },
    )

    if response.status_code == 200:
        api_keys.append(response.json())
    else:
        print(f"Failed with status code {response.status_code} at attempt {i + 1}")
        break

    time.sleep(5)

if len(api_keys) == 120:
    # Write the data to the file generated_keys.json
    try:
        dir = os.path.dirname(os.path.abspath(__file__))

        path = os.path.join(dir, "generated_keys.json")

        with open(path, "w", encoding="utf-8") as json_file:
            json.dump(api_keys, json_file, indent=2)

        print("Write data to generated_keys.json successfully!")
    except Exception as e:
        print("Failed to write data to generated_keys.json")
else:
    print("Failed to generate 120 keys. Please clear the database")
