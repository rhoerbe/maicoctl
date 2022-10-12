# Maico KWL logging client

This proof of concept was developed against a Maico WS-320 B manufactured in 2018.

The invocation of the program will append a hard-coded set of parameters to a log file.

The intended use is to execute the program in regular intervals, such as 60 minutes.

main.py will write to a log file, whereas mqtt.py will publish messages via mqtt.

## Maico

Maico's WS 320 is the central unit for a whole-house ventilation system. 
It delivers various data feeds about temperature, air flow and settings.
A build-in web server provides an API that is used by Maico's own Javascript-based client,
and is used by this program as well.

Vendor: https://www.maico-ventilatoren.com/

## Setup

Install python 3.6+ venv with dependencies in requirements.txt

    python3 -m venv /path/to/venv
    pip install -r requirements.txt

    # on a Raspberry OS one might need to install libatlas
    sudo apt-get install libatlas-base-dev -Y


To invoke the program on *nix from crontab etc:

    # set DATADIR, MAICOUSR and MAICOPW in the environment
    mkdir -p DATADIR
    source <path tp venv>/bin/activate
    python main.py

File locations and configuration fo data to be logged must be done in the source code.
