"""Home Assistant MQTT autodiscovery for Maico WS-320 ventilation.

Generates discovery payloads for ventilation sensors following
the HA MQTT discovery protocol.

Discovery topics:
  homeassistant/sensor/maico_ws320/<sensor_id>/config

State topics (existing):
  /home/ventilation/SENSOR/<sensor_name>
"""

import json
import logging
import os
import sys
import time
from typing import Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

DISCOVERY_PREFIX = "homeassistant"
MANUFACTURER = "Maico"
MODEL = "WS-320"
DEVICE_ID = "maico_ws320"

MQTT_CLIENT = os.getenv('MQTT_CLIENT', 'cloudberry.maico.discovery')
MQTT_BROKER = os.getenv('MQTT_BROKER', '10.4.4.17')
MQTT_USER = os.getenv('MQTT_USER', 'mqtt')
MQTT_PASS = os.getenv('MQTT_PASS', '')

STATE_TOPIC_BASE = "/home/ventilation/SENSOR"

# Sensor definitions: (sensor_id, name, device_class, unit, icon)
# device_class None means no HA device class
SENSORS = [
    ("FanLevel", "Fan Level", None, None, "mdi:fan"),
    ("FanLevelNum", "Fan Level Numeric", None, None, "mdi:fan"),
    ("VolumenstromZu", "Supply Air Flow", None, "m³/h", "mdi:weather-windy"),
    ("VolumenstromAb", "Extract Air Flow", None, "m³/h", "mdi:weather-windy"),
    ("DrehzahlZu", "Supply Fan Speed", None, "rpm", "mdi:rotate-right"),
    ("DrehzahlAb", "Extract Fan Speed", None, "rpm", "mdi:rotate-right"),
    ("T_Lufteintritt", "Outside Air Temperature", "temperature", "°C", None),
    ("T_Zuluft", "Supply Air Temperature", "temperature", "°C", None),
    ("T_Abluft", "Extract Air Temperature", "temperature", "°C", None),
    ("RfIntern", "Internal Humidity", "humidity", "%", None),
    ("BypassZustand", "Bypass State", None, None, "mdi:valve"),
    ("BypassZustandNum", "Bypass State Numeric", None, None, "mdi:valve"),
]

# Text-valued sensors that should NOT have state_class: measurement
TEXT_SENSORS = {"FanLevel", "BypassZustand"}


class MqttConnectError(Exception):
    pass


def _device_block() -> dict:
    """Generate the shared device block for the Maico unit."""
    return {
        "identifiers": [DEVICE_ID],
        "name": "Maico WS-320 Ventilation",
        "manufacturer": MANUFACTURER,
        "model": MODEL,
    }


def make_sensor_discovery_payload(
    sensor_id: str,
    name: str,
    device_class: Optional[str],
    unit: Optional[str],
    icon: Optional[str],
) -> dict:
    """Generate HA discovery payload for a sensor.

    Args:
        sensor_id: The sensor identifier (e.g., "T_Zuluft")
        name: Human-readable sensor name
        device_class: HA device class (e.g., "temperature", "humidity")
        unit: Unit of measurement (e.g., "°C", "%")
        icon: MDI icon (e.g., "mdi:fan")

    Returns:
        Discovery payload dict ready for JSON serialization
    """
    payload = {
        "name": name,
        "unique_id": f"{DEVICE_ID}_{sensor_id}",
        "state_topic": f"{STATE_TOPIC_BASE}/{sensor_id}",
        "device": _device_block(),
    }

    # Only add state_class for numeric sensors (not text-valued ones)
    if sensor_id not in TEXT_SENSORS:
        payload["state_class"] = "measurement"

    if device_class:
        payload["device_class"] = device_class
    if unit:
        payload["unit_of_measurement"] = unit
    if icon:
        payload["icon"] = icon

    return payload


def discovery_topic(sensor_id: str) -> str:
    """Generate the HA discovery config topic.

    Args:
        sensor_id: The sensor identifier

    Returns:
        Discovery topic string (e.g., "homeassistant/sensor/maico_ws320/T_Zuluft/config")
    """
    return f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/{sensor_id}/config"


def get_mqtt_client() -> mqtt.Client:
    """Create and connect MQTT client."""
    def on_connect(client, userdata, flags, rc, unused):
        if rc == 0:
            client.connected_flag = True
        else:
            print(f"Connect to MQTT broker failed with status {rc}", file=sys.stderr)
            client.connected_flag = False

    client = mqtt.Client(
        client_id=MQTT_CLIENT,
        transport='tcp',
        protocol=mqtt.MQTTv5
    )
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER)
    client.loop_start()
    time.sleep(1)
    client.loop_stop()
    if not client.connected_flag:
        raise MqttConnectError("Connect to MQTT broker failed")
    return client


def publish_discovery(client: mqtt.Client) -> None:
    """Publish HA autodiscovery messages for all sensors.

    Uses QoS 1 and retain=True so HA picks up the config on restart.

    Args:
        client: Connected MQTT client
    """
    for sensor_id, name, device_class, unit, icon in SENSORS:
        topic = discovery_topic(sensor_id)
        payload = json.dumps(
            make_sensor_discovery_payload(sensor_id, name, device_class, unit, icon)
        )
        result = client.publish(topic, payload, qos=1, retain=True)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("Published HA discovery for %s", sensor_id)
            print(f"Published discovery for {sensor_id}")
        else:
            logger.error("Failed to publish HA discovery for %s: rc=%d", sensor_id, result.rc)
            print(f"Failed to publish discovery for {sensor_id}: rc={result.rc}", file=sys.stderr)


def main():
    client = get_mqtt_client()
    client.loop_start()
    publish_discovery(client)
    time.sleep(2)  # Allow time for QoS 1 messages to be delivered
    client.loop_stop()
    client.disconnect()


if __name__ == '__main__':
    try:
        main()
    except MqttConnectError:
        exit(1)
