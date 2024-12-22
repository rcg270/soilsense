import network
import socket
import time
import random
from machine import Pin, ADC, PWM
from utime import sleep

from melodies import *  # import melodies.py
from notes import *     # import notes.py


# Create an LED object on pin 'LED'
led = Pin('LED', Pin.OUT)
led.value(1)
buzzer = PWM(Pin(3))  # Replace 15 with your chosen GPIO pin
volume = 600
track = 0
is_muted = False


# Wi-Fi credentials
ssid = 'Ziggo7404164'
password = 'evjcgvfRguyddn9r'

# Constants for soil moisture calibration
AIR_VALUE = 49000  # Replace with your sensor's air value
WATER_VALUE = 20000  # Replace with your sensor's water value

# Soil moisture sensor pin (ADC0)
soil_moisture_sensor = ADC(Pin(26))  # GP26 corresponds to ADC0 on Pico

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
        # be_quiet()
        
# Blink function to indicate startup
def blink(n):
    for i in range(0, n):
        led.value(1)
        time.sleep(1)
        led.value(0)
        time.sleep(1)

blink(3)

# Function to read soil moisture
def read_soil_moisture():
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
    """Replace placeholders in the HTML with actual values."""
    html_template = load_html('pico.html')
    html = html_template.format(
        state=state,
        raw_value=raw_value,
        moisture_percent=moisture_percent,
        current_plant=current_plant,
        required_moisture=required_moisture
    )
    return html


# Connect to WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

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
            if "Monsterra" in path:
                current_plant = "Monsterra"
                required_moisture = 30
            elif "Flamingo" in path:
                current_plant = "Flamingo Plant"
                required_moisture = 25

        elif path == '/lighton?':
            led.value(1)
            state = "ON"
        elif path == '/lightoff?':
            led.value(0)
            state = 'OFF'
        elif path == '/getsoil?':
            be_quiet()  # Stop any ongoing sound
            track = random.randint(0, len(melody) - 1)  # Select a random song
            raw_value, moisture_percent = read_soil_moisture()
            playsong(melody[track])

        response = build_webpage(state, raw_value, moisture_percent, current_plant, required_moisture)
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(response)
        conn.close()

    except Exception as e:
        print("Error:", e)
        conn.close()


