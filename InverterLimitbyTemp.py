# Dieses Script versucht die SOC an die Gegebenheit(Volt) der Akkus anzupassen
import time
import paho.mqtt.client as mqtt
import datetime
import logging
import json

verbunden = 0
cerboserial = "123456789"    # Ist auch gleich VRM Portal ID
broker_address = "192.168.1.xxx"
temptopic = "temperature/25"

#  Einstellen der Limits

Templimit = 50
Wattlimit = 3000

#  Variablen
maxdischarge = -1
temperature = 30
tempname = "Sensor"
durchlauf = 0



logging.basicConfig(filename='Error.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

def on_disconnect(client, userdata, rc):
    global verbunden
    print("Client Got Disconnected")
    if rc != 0:
        print('Unexpected MQTT disconnection. Will auto-reconnect')

    else:
        print('rc value:' + str(rc))

    try:
        print("Trying to Reconnect")
        client.connect(broker_address)
        verbunden = 1
    except Exception as e:
        logging.exception("Fehler beim reconnecten mit Broker")
        print("Error in Retrying to Connect with Broker")
        verbunden = 0
        print(e)

def on_connect(client, userdata, flags, rc):
        global verbunden
        if rc == 0:
            print("Connected to MQTT Broker!")
            verbunden = 1
            client.subscribe("N/" + cerboserial + "/settings/0/Settings/CGwacs/MaxDischargePower")
            client.subscribe("N/" + cerboserial + "/" + temptopic + "/Temperature")
            client.subscribe("N/" + cerboserial + "/" + temptopic + "/CustomName")
        else:
            print("Failed to connect, return code %d\n", rc)


def on_message(client, userdata, msg):
    try:

        global maxdischarge, temperature, tempname
        if msg.topic == "N/" + cerboserial + "/settings/0/Settings/CGwacs/MaxDischargePower":   # MaxDischargePower

            maxdischarge = json.loads(msg.payload)
            maxdischarge = round(float(maxdischarge['value']), 2)

        if msg.topic == "N/" + cerboserial + "/" + temptopic + "/Temperature":   # Temperature

            temperature = json.loads(msg.payload)
            temperature = round(float(temperature['value']), 2)

        if msg.topic == "N/" + cerboserial + "/" + temptopic + "/CustomName":   # Name of Temp Sensor

            tempname = json.loads(msg.payload)
            tempname = tempname['value']

    except Exception as e:
        print(e)
        print("Im ILbT Programm ist etwas beim auslesen der Nachrichten schief gegangen")

# Konfiguration MQTT
client = mqtt.Client("InverterLimitbyTemp")  # create new instance
client.on_disconnect = on_disconnect
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address)  # connect to broker

logging.debug("Programm MinSoc by Month wurde gestartet")

client.loop_start()
time.sleep(2)
#  Abfragen der aktuellen Werte
#client.publish("R/" + cerboserial + "/settings/0/Settings/CGwacs/MaxDischargePower")
#client.publish("R/" + cerboserial + "/" + temptopic + "/Temperature")
client.publish("R/" + cerboserial + "/" + temptopic + "/CustomName",'{}')
while(1):

    time.sleep(60)
    print("Lese folgenden TemperaturSensor aus: " + (tempname))
    print("Aktuelle Temperatur: " + str(temperature))
    print("Aktuelles Limit: " + str(maxdischarge) + ", (-1 = kein Limit)")
    durchlauf = durchlauf + 1
    print("Dies ist Durchlauf " + str(durchlauf) +" des InverterLimitbyTemp Programm")
    if temperature > Templimit:
        if maxdischarge == -1:
            print("Temperatur ist höher als 50C°, Limit wird aktiviert\n")
            client.publish("W/" + cerboserial + "/settings/0/Settings/CGwacs/MaxDischargePower",'{"value":' + str(Wattlimit + '}')
        else:
            print("Temperatur ist noch immer höher als 50°C, behalte Limit bei\n")
    else:
        if maxdischarge == -1:
            print("Aktuelle Temperatur ist unter 50°C, daher wird kein Limit aktiviert\n")
        else:
            print("Aktuelle Temperatur ist unter 50°C, daher wird das Limit wieder deaktiviert\n")
            client.publish("W/" + cerboserial + "/settings/0/Settings/CGwacs/MaxDischargePower",'{"value": -1}')