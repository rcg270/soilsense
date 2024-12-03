import serial
import requests
import time

# Serial port settings (update COM port as needed)
arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1)  # Replace 'COM3' with your Arduino port

# Replace with your GitHub Pages repository (static JSON file or endpoint)
DATA_URL = "https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/contents/data.json"
TOKEN = "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"


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
    encoded_content = requests.utils.quote(json.dumps(new_content)).encode()
    update_data = {
        "message": "Update soil moisture data",
        "content": encoded_content,
        "sha": file_info["sha"],  # Required to update the file
    }
    update_response = requests.put(DATA_URL, headers=headers, json=update_data)
    return update_response


if __name__ == "__main__":
    while True:
        moisture_value = read_from_arduino()
        if moisture_value is not None:
            print(f"Moisture: {moisture_value}")
            response = update_github(moisture_value)
            print(f"Update response: {response.status_code}")
        time.sleep(10)  # Delay between updates
