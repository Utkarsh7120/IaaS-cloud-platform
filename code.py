# main.py — Raspberry Pi Pico W
# Sensors: DHT11, PIR, Buzzer, LED, Water Flow Sensor (YF-S201)
# Sends JSON data to laptop app.py via HTTP on local WiFi network

import network
import socket
import time
import json
import machine
from machine import Pin
import dht
# CONFIGURATION — edit these before uploading
WIFI_SSID      = "OPPO"
WIFI_PASSWORD  = "qwerty11"
LAPTOP_IP      = "10.144.68.253"  
LAPTOP_PORT    = 5000            
SEND_INTERVAL  = 5                 

# DHT11  DATA  → GP2  (Pin 4)  with 10kΩ pull-up to 3V3
# PIR    OUT   → GP4  (Pin 6)  HC-SR501, powered from VSYS (5V)
# LED    +     → GP5  (Pin 7)  with 220Ω series resistor
# BUZZER +     → GP6  (Pin 9)  Active buzzer, direct 3.3V ok
# WFS    SIG   → GP7  (Pin 10) YF-S201 Yellow wire, 10kΩ pull-up
# All GNDs share any GND pin. PIR+WFS VCC → VSYS (Pin 39) for 5V.

DHT_PIN   = 2
PIR_PIN   = 4
LED_PIN   = 5
BUZZ_PIN  = 6
FLOW_PIN  = 7
def beep(times=1, ms=100):
    for _ in range(times):
        buzzer.on();  time.sleep_ms(ms)
        buzzer.off(); time.sleep_ms(100)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    print("Connecting to WiFi:", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            break
        time.sleep(1)
        print(".", end="")
    print()
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("WiFi OK — Pico IP:", ip)
        blink(3, 80)
        return ip
    print("WiFi FAILED")
    beep(5, 50)
    return None

def read_dht():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
    except:
        return None, None

def read_flow(sample_ms=1000):
    global pulse_count
    pulse_count = 0
    time.sleep_ms(sample_ms)
    freq = pulse_count / (sample_ms / 1000.0)
    lpm  = round(freq / 7.5, 2)      # YF-S201: 7.5 Hz = 1 L/min
    return lpm

def http_post(payload_dict):
    body = json.dumps(payload_dict)
    request = (
        "POST /data HTTP/1.1\r\n"
        "Host: {}:{}\r\n".format(LAPTOP_IP, LAPTOP_PORT) +
        "Content-Type: application/json\r\n"
        "Content-Length: {}\r\n".format(len(body)) +
        "Connection: close\r\n\r\n" +
        body
    )
    try:
        addr = socket.getaddrinfo(LAPTOP_IP, LAPTOP_PORT)[0][-1]
        s = socket.socket()
        s.settimeout(5)
        s.connect(addr)
        s.send(request.encode())
        s.recv(256)   # read and discard response
        s.close()
        return True
    except Exception as e:
        print("HTTP error:", e)
        return False
run()
