#!/bin/bash

bindir=$(cd $(dirname $BASH_SOURCE[0]) && pwd)
projhome=$(dirname $bindir)

source $projhome/venv/bin/activate
python $projhome/mqtt.py
