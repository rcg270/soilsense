import network
import socket
import time
import random
from machine import Pin, ADC

# Create an LED object on pin 'LED'
led = Pin('LED', Pin.OUT)
led.value(1)

# Wi-Fi credentials
ssid = 'Ziggo7404164'
password = 'evjcgvfRguyddn9r'

# Constants for soil moisture calibration
AIR_VALUE = 49000  # Replace with your sensor's air value
WATER_VALUE = 20000  # Replace with your sensor's water value

# Soil moisture sensor pin (ADC0)
soil_moisture_sensor = ADC(Pin(26))  # GP26 corresponds to ADC0 on Pico

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
def webpage(random_value, state, raw_value, moisture_percent):
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pico Web Server</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Raspberry Pi Pico Web Server</h1>
            <h2>LED Control</h2>
            <form action="./lighton">
                <input type="submit" value="Light on" />
            </form>
            <br>
            <form action="./lightoff">
                <input type="submit" value="Light off" />
            </form>
            <p>LED state: {state}</p>
            <h2>Fetch New Value</h2>
            <form action="./value">
                <input type="submit" value="Fetch value" />
            </form>
            <p>Fetched value: {random_value}</p>
            <h2>Soil Moisture</h2>
            <p>Raw Value: {raw_value}</p>
            <p>Soil Moisture: {moisture_percent}%</p>
        </body>
        </html>
        """
    return str(html)

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

# Main loop to listen for connections
while True:
    try:
        conn, addr = s.accept()
        print('Got a connection from', addr)
        
        # Receive and parse the request
        request = conn.recv(1024)
        request = str(request)
        print('Request content = %s' % request)

        try:
            request = request.split()[1]
            print('Request:', request)
        except IndexError:
            pass
        
        # Process the request and update variables
        if request == '/lighton?':
            print("LED on")
            led.value(1)
            state = "ON"
        elif request == '/lightoff?':
            led.value(0)
            state = 'OFF'
        elif request == '/value?':
            random_value = random.randint(0, 20)
            # Get soil moisture data when the button is pressed
            raw_value, moisture_percent = read_soil_moisture()

        # Generate HTML response
        response = webpage(random_value, state, raw_value, moisture_percent)  

        # Send the HTTP response and close the connection
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(response)
        conn.close()

    except OSError as e:
        conn.close()
        print('Connection closed')

