import datetime
import json
import re
import os
import sys
import time
import xml.etree.ElementTree as et
from pathlib import Path

import paho.mqtt.client
import paho.mqtt.client as mqtt
import requests

DATADIR = os.getenv('DATADIR', 'data')
SAMPLEFILE = Path(DATADIR) / 'kwl_detail.xml'
MAICO_HOST = os.getenv('MAICOHOST', '10.4.4.14')
MAICO_URL = f"http://{MAICO_HOST}/details.cgx"
MAICO_USER = os.getenv('MAICOUSR', 'admin')
MAICO_PASS = os.getenv('MAICOPW', '')
MQTT_CLIENT = os.getenv('MQTT_CLIENT', 'cloudberry.maico')
MQTT_BROKER = os.getenv('MQTT_BROKER', '10.4.4.17')
MQTT_USER = os.getenv('MQTT_USER', 'mqtt')
MQTT_PASS = os.getenv('MQTT_PASS', '')

class MqttConnectError(Exception):
    pass


# Numeric mappings for text-valued sensors
FAN_LEVEL_MAP = {
    "Aus": 0,
    "Reduziert": 1,
    "Nenn": 2,
    "Feuchteschutz": 3,
}

BYPASS_STATE_MAP = {
    "zu": 0,
    "auf": 1,
}

def main():
    get_sample_from_maico()
    dataset = convert_xml_to_dict()
    mqtt_client = get_mqtt_client()
    publish_mqtt(mqtt_client, dataset)


def get_sample_from_maico():
    with open(SAMPLEFILE, 'w', encoding='utf-8') as fd:
        response = requests.get(MAICO_URL, auth=(MAICO_USER, MAICO_PASS))
        if response.status_code == 200:
            fd.write(response.text)
        else:
            print(f"request returned status code {response.status_code}", file=sys.stderr)
            exit(1)


def convert_xml_to_dict() -> dict:
    xtree = et.parse(SAMPLEFILE)
    xroot = xtree.getroot()
    dataset = {'datetime': datetime.datetime.now().replace(microsecond=0).isoformat()}
    for node in xroot:
        id = node.find("id").text.strip()
        value = node.find("value").text.strip()
        value = strip_unit_from_value(value)
        if is_selected_datapoint(id):
            dataset[id] = value
    return dataset


def is_selected_datapoint(id: str) -> bool:
    return id in get_sensors()


def get_sensors() -> list:
    return ['FanLevel', 'VolumenstromAb', 'VolumenstromZu', 'DrehzahlZu', 'DrehzahlAb', 'T_Lufteintritt', 'T_Zuluft',
     'T_Abluft', 'RfIntern', 'BypassZustand',]


def strip_unit_from_value(value: str) -> str:
    v = re.sub(r' rpm$', '', value)
    v = re.sub(' m3/h$', '', v)
    v = re.sub(' %', '', v)
    return re.sub(r' °C$', '', v)


def get_mqtt_client() -> paho.mqtt.client.Client:
    def on_connect(client, userdata, flags, rc, unused):
        if rc == 0:
            client.connected_flag = True
        else:
            print(f"Connect to MQTT broker failed with status {rc}", file=sys.stderr)
            client.connected_flag = False

    client = mqtt.Client(client_id=MQTT_CLIENT,
                         transport='tcp',
                         protocol=mqtt.MQTTv5)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER)
    client.loop_start()
    time.sleep(1)  # Wait for connection setup to complete
    client.loop_stop()
    if not client.connected_flag:
        raise MqttConnectError(f"Connect to MQTT broker failed")
    return client


def publish_mqtt(mqtt_client: object, dataset: dict):
    # using a message per variable because of home assistant config issue -> single JSON msg would be preferred
        sensor_topic = '/home/ventilation/SENSOR/'
        for sensor in get_sensors():
            (result, mid) = mqtt_client.publish(sensor_topic + sensor, dataset[sensor])
            if result:
                print(f"mqtt publish returned status code {result}", file=sys.stderr)

        # Publish numeric variants for text-valued sensors
        if 'FanLevel' in dataset:
            fan_level_num = FAN_LEVEL_MAP.get(dataset['FanLevel'], -1)
            (result, mid) = mqtt_client.publish(sensor_topic + 'FanLevelNum', fan_level_num)
            if result:
                print(f"mqtt publish FanLevelNum returned status code {result}", file=sys.stderr)

        if 'BypassZustand' in dataset:
            bypass_num = BYPASS_STATE_MAP.get(dataset['BypassZustand'], -1)
            (result, mid) = mqtt_client.publish(sensor_topic + 'BypassZustandNum', bypass_num)
            if result:
                print(f"mqtt publish BypassZustandNum returned status code {result}", file=sys.stderr)


def publish_mqtt_json(mqtt_client: object, dataset: dict):
        topic = '/home/ventilation/SENSORS'
        (result, mid) = mqtt_client.publish(topic, json.dumps(dataset))
        if result:
            print(f"mqtt publish returned status code {result}", file=sys.stderr)

if __name__ == '__main__':
    try:
        main()
    except MqttConnectError:
        exit(1)

