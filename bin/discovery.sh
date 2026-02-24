#!/bin/bash

bindir=$(cd $(dirname $BASH_SOURCE[0]) && pwd)
projhome=$(dirname $bindir)

cd $projhome
source venv/bin/activate
source bin/mqtt_pass.sh
python discovery.py
