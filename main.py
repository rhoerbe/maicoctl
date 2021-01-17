import datetime
import re
import sys
import xml.etree.ElementTree as et
from pathlib import Path
import pandas as pd
import requests

LOGFILE = Path('data/kwl_log.csv')
LASTSAMPLE = Path('data/kwl_log_last.csv')
SAMPLEFILE = Path('data/kwp_detail.xml')
MAICOURL = 'http://192.168.0.14/details.cgx'
USER = 'admin'
PASS = ''

def is_selected(id: str) -> bool:
    return id in ('FanLevel', 'VolumenstromZu', 'DrehzahlZu', 'DrehzahlAb', 'T_Lufteintritt', 'T_Zuluft',
                  'T_Abluft', 'T_Fortluft', 'RfIntern', 'BypassZustand', )


def strip_unit_from_value(value: str) -> str:
    v = re.sub(r' rpm$', '', value)
    v = re.sub(' m3/h$', '', v)
    return re.sub(r' °C$', '', v)


def get_sample_from_maico():
    with open(SAMPLEFILE, 'w', encoding='utf-8') as fd:
        response = requests.get(MAICOURL, auth=(USER, PASS))
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
        if is_selected(id):
            dataset[id] = value
    return dataset


def create_or_append_csv(dataset: dict):
    df = pd.DataFrame.from_dict([dataset], orient="columns")
    if LOGFILE.is_file():
        df.to_csv(LASTSAMPLE, sep=';', header=False)
        with open(LASTSAMPLE) as fd_in:
            line = fd_in.readline()
            # line = re.sub('^0;', '', line)  # strip unexpected first column containing 0
            with open(LOGFILE, 'a') as fd_out:
                fd_out.write(line)
    else:
        df.to_csv(LOGFILE, sep=';')


def main():
    get_sample_from_maico()
    dataset = convert_xml_to_dict()
    create_or_append_csv(dataset)


if __name__ == '__main__':
    main()

