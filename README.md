# SoilSense

For this project, dedicated to my lovely girlfriend, a RPI pico W and a generic soil moisture sensor have been used to create a fun little web interface to check the health of your plants!


## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup and Installation](#setup-and-installation)
3. [Usage Instructions](#usage-instructions)
4. [Customization](#customization)
5. [Troubleshooting](#troubleshooting)

## Prerequisites
- Raspberry Pi Pico W
- Soil moisture sensor
- jumper cables
- breadboard(or soldering)
- Python 3.x
- Thonny IDE (or arduino ide)
- Wi-Fi connectivity
(optional:)
- Active buzzer
- Oled screen


## Setup and Installation
1. Setup the RPI circuit (diagram will follow soon)
2. Clone this repository:
   ```bash
   git clone git@github.com:rcg270/soilsense.git
3. Edit the main.py file to add your wifi ssid and pw. Optional to add, else remove: token, data_url. You can request your data url from github directly https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens.
4. Also check AIR_VALUE and WATER_VARIABLE these depend on your sensor and should be changed accordingly. WATER_VARIABLE should be measured when the sensor is fully submerged in water, and AIR_VALUE when the sensor is in the air in the room where you wish to use the device.
5. Modify the pico.html file to include double brackets {}'s. This is needed because the micropython linter cannot handle brackets correctly.
so:
```html
body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #140202;
            color: #070707;
            background: url('img/WP.jpg') repeat-y;

        }
```
should become
```html
body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #140202;
            color: #070707;
            background: url('img/WP.jpg') repeat-y;

        }}
```

6. Upload all files to your Pico W.

## Usage Instructions
1. After doing the Setup, run main.py.
2. If you're using Thonny, the console will show the IP where the Pico W is hosting the website.
- Alternatively, on linux, you can use ```ipconfig``` to figure out your ipv4 address (e.g., 192.168.1.5) and subnet (something like 192.168.1.0/24), and then ```nmap -sn (your.sub.net/xx)``` (in this case 192.168.1.0/24) to find out which device is the RPI. The hostname should be something like raspberrypi.local. Otherwise you can use trial and error to find the correct ip.
- On windows, use a tool like https://www.advanced-ip-scanner.com/ to do pretty much the same as described before.
3. Open the ip on a device connected to the same WIFI as is described in main.py.
4. Select the plant you are using or add your own.
5. Use the Get Soil Measurement button on the site to update the page with the accurate soil measurement!

## Customization
1. As a customization it is possible to add an active buzzer to the circuit. This allows the project to play songs as described in https://github.com/twisst/Music-for-Raspberry-Pi-Pico.
2. Optionally a OLED screen can be added to have the device display the current moisture level.
3. You can, but don't have to, clone the repo and open a Github Pages page to have a permanently running interface of the soil website (in index.html).

## Troubleshooting
1. Everything should be pretty simple, if you have any issues use chatgpt :p.
