import network
import socket
import time
import random
from machine import Pin, ADC, PWM
from utime import sleep, localtime
import json
import requests
import os
from base64 import b64
import ubinascii

from melodies import *  # import melodies.py
from notes import *     # import notes.py


# Create an LED object on pin 'LED'
led = Pin('LED', Pin.OUT)
led.value(1)
buzzer = PWM(Pin(3))  # Replace 3 with your chosen GPIO pin
volume = 600
track = 0
is_muted = False

TOKEN = "your-github-token"
# replace with your data url
DATA_URL = "https://api.github.com/repos/rcg270/soilsense/contents/data.json"

# Wi-Fi credentials, replace with your information
networks = [
    {'ssid': 'ssid1', 'password': 'pw1'},
    {'ssid': 'ssid2', 'password': 'pw2'}
]

plants = {  # Dictionary to store plant names and their required moisture levels
    "Monsterra": 30,
    "Flamingo": 25,
}

# Constants for soil moisture calibration
AIR_VALUE = 49000  # Replace with your sensor's air value
WATER_VALUE = 20000  # Replace with your sensor's water value

DATA_FILE = 'soil_data.json'
soil_data_list = [{'moisture_percent': 25, 'current_plant': 'Flamingo Plant', 'date': '2024-12-23 02:04:39'}]

# Soil moisture sensor pin (ADC0)
soil_moisture_sensor = ADC(Pin(26))  # GP26 corresponds to ADC0 on Pico

# Blink function to indicate startup
def blink(n):
    for i in range(0, n):
        led.value(1)
        time.sleep(1)
        led.value(0)
        time.sleep(1)

def playtone(frequency):
    buzzer.duty_u16(volume)
    buzzer.freq(frequency)

def be_quiet():
    buzzer.duty_u16(0)  # turns sound off

def duration(tempo, t):

    # calculate the duration of a whole note in milliseconds (60s/tempo)*4 beats
    wholenote = (60000 / tempo) * 4

    # calculate the duration of the current note
    # (we need an integer without decimals, hence the // instead of /)
    if t > 0:
      noteDuration = wholenote // t
    elif (t < 0):
      # dotted notes are represented with negative durations
      noteDuration = wholenote // abs(t)
      noteDuration *= 1.5 # increase their duration by a half

    return noteDuration

def playsong(mysong):
    start_time = time.time()
    try:

        print(mysong[0]) # print title of the song to the shell
        tempo = mysong[1] # get the tempo for this song from the melodies list

        # iterate over the notes of the melody.
        # The array is twice the number of notes (notes + durations)
        for thisNote in range(2, len(mysong), 2):
            if time.time() - start_time >= 4:  # Check if 4 seconds have passed
                print("Song playback stopped after 4 seconds")
                be_quiet()
                break

            noteduration = duration(tempo, int(mysong[thisNote+1]))

            if (mysong[thisNote] == "REST"):
                be_quiet()
            else:
                playtone(notes[mysong[thisNote]])

            sleep(noteduration*0.9/1000) # we only play the note for 90% of the duration...
            be_quiet()
            sleep(noteduration*0.1/1000) # ... and leave 10% as a pause between notes


    except: # make sure the buzzer stops making noise when something goes wrong or when the script is stopped
        print("something went wrong bruh")


def upload_to_github():
    # Convert the data to a base64 string
    print("encoding data", soil_data_list)
    json_data = json.dumps(soil_data_list)
    print("json_data:", json_data)
    # encoded_data = encoder.encode(json_data)  # Use the custom base64_encode function
    encoded_data = ubinascii.b2a_base64(json_data.encode()).decode('utf-8')
    print("encoded data:", encoded_data)

    print("finished encoding")

    # Get the current file SHA to update it
    print("getting current data file")
    headers = {
        "Authorization": f"token {TOKEN}",
        "User-Agent": "Soilsense"  # Replace with your app's name
    }
    
    response = requests.get(DATA_URL, headers=headers)

    # Check if the response is valid
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        print(f"Response Text: {response.text}")
        return

    try:
        file_info = response.json()
        print(file_info)
    except ValueError:
        print("Response is not valid JSON")
        print(f"Response Text: {response.text}")
        return

    # Prepare the data for update
    print("preparing data for update")
    update_data = {
        "message": "Update soil moisture data",
        "content": encoded_data,
        "sha": file_info["sha"],
    }

    # Send the update request
    print("sending update rq")
    update_response = requests.put(DATA_URL, headers=headers, json=update_data)
    if update_response.status_code == 200:
        print("Data uploaded successfully to GitHub")
    else:
        print(f"Error uploading data: {update_response.text}")


def store_soil_data(moisture_percent, current_plant):
    # Prepare data to be stored
    current_time = localtime()
    print("curr time", current_time)
    formatted_time = "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
        current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5])
    data = {
        "date": formatted_time,
        "moisture_percent": moisture_percent,
        "current_plant": current_plant
    }
    print("data:", data)

    # Write data to JSON file (doesnt work, instead use list)
    soil_data_list.append(data)

    print("Data stored successfully")


# Function to read soil moisture
def read_soil_moisture():
    print("reading soil moisture")
    raw_value = soil_moisture_sensor.read_u16()
    percent = int((AIR_VALUE - raw_value) / (AIR_VALUE - WATER_VALUE) * 100)
    percent = max(0, min(100, percent))  # Clamp between 0 and 100
    return raw_value, percent

# HTML template for the webpage
def load_html(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            print("HTML Loaded Successfully")  # Print a snippet
            return content
    except Exception as e:
        print("Error loading HTML file:", e)
        return "<h1>Error loading HTML file</h1>"


def build_webpage(state, raw_value, moisture_percent, current_plant, required_moisture=25):
    """Inject the plant data into HTML using JavaScript."""
    html_template = load_html('pico.html')  # Your HTML template

    # Set default for plants if None
    # Convert plants dictionary to JSON string for JavaScript
    plants_json = json.dumps(plants)

    # Replace placeholders in the HTML with Python variables
    html = html_template.format(
        state=state,
        raw_value=raw_value,
        moisture_percent=moisture_percent,
        current_plant=current_plant,
        required_moisture=required_moisture,
        plants_json=plants_json  # Pass the JSON-encoded plants data to the HTML
    )
    return html



blink(3)
# Connect to WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

available_networks = [n[0].decode('utf-8') for n in wlan.scan()]

for net in networks:
    if net['ssid'] in available_networks:
        print(f"Connecting to {net['ssid']}...")
        wlan.connect(net['ssid'], net['password'])
        for _ in range(10):  # Wait up to 10 seconds
            if wlan.isconnected():
                print(f"Connected to {net['ssid']}!")
                print("Network info:", wlan.ifconfig())
                break
            time.sleep(1)
        else:
            print(f"Failed to connect to {net['ssid']}")
        break
else:
    print("No known networks found.")

# Wait for Wi-Fi connection
connection_timeout = 10
while connection_timeout > 0:
    if wlan.status() >= 3:
        break
    connection_timeout -= 1
    print('Waiting for Wi-Fi connection...')
    time.sleep(1)

# Check if connection is successful
if wlan.status() != 3:
    raise RuntimeError('Failed to establish a network connection')
else:
    print('Connection successful!')
    led.value(1)
    network_info = wlan.ifconfig()
    print('IP address:', network_info[0])


# Set up socket and start listening
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen()

print('Listening on', addr)

# Initialize variables
state = "ON"
random_value = 0
raw_value = 0
moisture_percent = 0


# Default plant
current_plant = "Flamingo Plant"
required_moisture = 25

# Main loop to listen for connections
while True:
    try:
        conn, addr = s.accept()
        print('Got a connection from', addr)

        request = conn.recv(1024).decode('utf-8')
        print('Request content =', request)

        try:
            path = request.split()[1]
        except IndexError:
            path = "/"

        if "plant" in path:
            print(f"Received path: {path}")  # Debug: print the full request path

            if "current_plant" in path:
                plant = path.split('=')[-1].replace("?", "")  # Remove trailing '?' if present
                print(f"Setting current plant to: {plant}")  # Debug: print plant being set
                if plant in plants:
                    current_plant = plant
                    required_moisture = plants[plant]
                    print(f"Current plant set to {current_plant} with required moisture {required_moisture}")  # Debug: confirm update
                else:
                    print(f"Plant {plant} not found in plants dictionary")  # Debug: plant not found in the list

            elif "add_plant" in path:
                params = path.split('?')[-1].split('&')
                print(f"Received add_plant parameters: {params}")  # Debug: show the parameters received
                new_plant = params[0].split('=')[-1]
                moisture = int(params[1].split('=')[-1])
                print(f"Adding new plant: {new_plant} with moisture: {moisture}")  # Debug: print the plant and moisture being added
                plants[new_plant] = moisture
                print(f"Updated plants: {plants}")  # Debug: print updated plant list

            elif "remove_plant" in path:
                plant_to_remove = path.split('=')[-1].replace("?", "")
                print(f"Attempting to remove plant: {plant_to_remove}")  # Debug: print the plant being removed
                if plant_to_remove in plants:
                    del plants[plant_to_remove]
                    print(f"Plant {plant_to_remove} removed successfully")  # Debug: confirm removal
                else:
                    print(f"Plant {plant_to_remove} not found in plants dictionary")  # Debug: plant not found to remove



        elif path == '/upload?':
            upload_to_github()

        elif path == '/getsoil?':
            be_quiet()  # Stop any ongoing sound
            track = random.randint(0, len(melody) - 1)  # Select a random song
            raw_value, moisture_percent = read_soil_moisture()
            store_soil_data(moisture_percent, current_plant)
            playsong(melody[track])

        response = build_webpage(state, raw_value, moisture_percent, current_plant, required_moisture)
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(response)
        conn.close()

    except Exception as e:
        print("Error:", e)
        conn.close()




