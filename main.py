from machine import Pin
import time

import time                   # Allows use of time.sleep() for delays
from mqtt import MQTTClient  # For use of MQTT protocol to talk to Adafruit IO
import ubinascii              # Needed to run any MicroPython code
import machine                # Interfaces with hardware components
import micropython            # Needed to run any MicroPython code

import camera
import gc
import dht

DHT = dht.DHT11(machine.Pin(15))
    

intruderDetected = False
threshold = 60 #centimeter

trigPin = Pin(13, Pin.OUT, 0)
echoPin = Pin(14, Pin.IN, 0)

soundVelocity = 340
distance = 0

#Sonar function, returns distance in cm.
def getSonar():
    trigPin.value(1)
    time.sleep_us(10)
    trigPin.value(0)
    while not echoPin.value():
        pass
    pingStart = time.ticks_us()
    while echoPin.value():
        pass
    pingStop = time.ticks_us()
    pingTime = time.ticks_diff(pingStop, pingStart)
    distance = pingTime * soundVelocity//2//10000
    
    return int(distance)
time.sleep_ms(2000)
    
# BEGIN SETTINGS
# These need to be change to suit your environment
MESSAGE_INTERVAL = 10000 # milliseconds
last_random_sent_ticks1 = 0  # milliseconds
last_random_sent_ticks2 = -61000*5  # milliseconds


# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "Bendude_510"
AIO_KEY = "aio_PbdE60yraPq27RqoCUq0cwloVHP4"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_INTRUDER_FEED = "Bendude_510/feeds/intruderfeed"
AIO_TEXT_FEED = "Bendude_510/feeds/textfeed"
AIO_TEMP_FEED = "Bendude_510/feeds/tempfeed"
#AIO_CAMERA_FEED = "Bendude_510/feeds/camerafeed"
# END SETTINGS


# We'll use the LED to respond to messages from Adafruit IO
time.sleep(0.1) # Workaround for a bug.
                # Above line is not actioned if another
                # process occurs immediately afterwards


def distance_sensor():
    global last_random_sent_ticks1
    global MESSAGE_INTERVAL
    global intruderDetected
    global threshold


    time.sleep_ms(500)
    if getSonar() < threshold and not intruderDetected:
        intruderDetected = True

    if ((time.ticks_ms() - last_random_sent_ticks1) < MESSAGE_INTERVAL):
        return; # Too soon since last one sent.

    try:
        if not intruderDetected:
            client.publish(topic=AIO_INTRUDER_FEED, msg = "3")
            print("DONE1")
        elif intruderDetected:
            client.publish(topic=AIO_INTRUDER_FEED, msg = "1")  #Condition on adafruit, On if value is less than 2.
            client.publish(topic=AIO_TEXT_FEED, msg = "Intruder Detected!")
            intruderDetected = False
            print("DONE1")

    except Exception as e:
        print("FAILED1")
    finally:
        last_random_sent_ticks1 = time.ticks_ms()

def temp_sensor():
    global last_random_sent_ticks2
    global MESSAGE_INTERVAL
    global statusIndicator

    if ((time.ticks_ms() - last_random_sent_ticks2) < 60000*5):
        return; # Too soon since last one sent.

    try:
        DHT.measure()
        a = 'temperature: ' + str(DHT.temperature()) +' humidity: ' +str(DHT.humidity())
        client.publish(topic=AIO_TEMP_FEED, msg = a)

        print("DONE")
    except Exception as e:
        print("FAILED")
    finally:
        last_random_sent_ticks2 = time.ticks_ms()
        
# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)

client.connect()
print("Connected to %s, subscribed to no topics" % (AIO_SERVER))


try:                      # Code between try: and finally: may cause an error
                          # so ensure the client disconnects the server if
                          # that happens.
    while 1:              # Repeat this loop forever
        distance_sensor()
        temp_sensor()
finally:                  # If an exception is thrown ...
    client.disconnect()   # ... disconnect the client and clean up.
    client = None
    print("Disconnected from Adafruit IO.")
