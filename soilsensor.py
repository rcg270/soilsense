import serial
import requests
import time
import json
import base64

# Serial port settings (update COM port as needed)
arduino = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1)

# Replace with your GitHub Pages repository (static JSON file or endpoint)
DATA_URL = "https://api.github.com/repos/rcg270/soilsense/contents/data.json"
TOKEN = "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"


def read_from_arduino():
    if arduino.in_waiting > 0:
        line = arduino.readline().decode('utf-8').strip()
        if "Soil Moisture Value:" in line:
            return int(line.split(":")[1].strip())  # Extract the numerical value
    return None


def update_github(data):
    # Step 1: Get the current file SHA
    headers = {"Authorization": f"token {TOKEN}"}
    response = requests.get(DATA_URL, headers=headers)
    response.raise_for_status()
    file_info = response.json()

    # Step 2: Update the file with new data
    new_content = {"soil_moisture": data}
    encoded_content = base64.b64encode(json.dumps(new_content).encode()).decode()
    update_data = {
        "message": "Update soil moisture data",
        "content": encoded_content,
        "sha": file_info["sha"],  # Required to update the file
    }
    update_response = requests.put(DATA_URL, headers=headers, json=update_data)
    print("Updating GitHub with data:")
    print(json.dumps(update_data, indent=4))
    print(f"Response content: {update_response.text}")
    return update_response


if __name__ == "__main__":
    while True:
        moisture_value = read_from_arduino()
        if moisture_value is not None:
            print(f"Moisture: {moisture_value}")
            response = update_github(moisture_value)
            print(f"Update response: {response.status_code}")
        time.sleep(10)  # Delay between updates
