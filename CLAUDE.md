# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

maicoctl is a Python logging client for Maico WS-320 whole-house ventilation systems. It fetches sensor data via HTTP from the Maico's built-in web server and either logs to CSV files or publishes to MQTT (for Home Assistant integration).

## Running the Application

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# CSV logging mode
export DATADIR=data MAICOUSR=admin MAICOPW=<password> MAICOHOST=10.4.4.14
python main.py

# MQTT publishing mode
cp bin/mqtt_pass.sh.default bin/mqtt_pass.sh  # edit with MQTT password
bin/mqtt_pub.sh
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| MAICOHOST | 10.4.4.14 | Maico device IP |
| MAICOUSR | admin | Maico web auth user |
| MAICOPW | (empty) | Maico web auth password |
| DATADIR | data | Output directory for XML/CSV |
| MQTT_BROKER | 10.4.4.17 | MQTT broker IP |
| MQTT_USER | mqtt | MQTT username |
| MQTT_PASS | (empty) | MQTT password |
| MQTT_CLIENT | cloudberry.maico | MQTT client ID |

## Architecture

Two independent entry points, both fetching from Maico's `/details.cgx` XML API:

- **main.py**: Fetches XML, parses selected sensors, appends to CSV log (`data/kwl_log.csv`)
- **mqtt.py**: Fetches XML, parses selected sensors, publishes individual messages per sensor to MQTT topic `/home/ventilation/SENSOR/<sensor_name>`

Both scripts write intermediate XML to `DATADIR/kwl_detail.xml`.

## Monitored Sensors

Configured in `is_selected()` (main.py) and `get_sensors()` (mqtt.py):
- FanLevel, VolumenstromZu, VolumenstromAb, DrehzahlZu, DrehzahlAb
- T_Lufteintritt, T_Zuluft, T_Abluft, T_Fortluft, RfIntern, BypassZustand
