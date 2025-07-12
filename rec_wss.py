#!/usr/bin/env python3
# coding: utf-8
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et :

"""
pre-flight:
    pip install requests websocket-client

usage:
    rec_wss --provider jcba --station heartfm --time 1800 | ffplay -nodisp -hide_banner -autoexit -i pipe:
    rec_wss --provider fmplapla --station amasakifm | mpv -
    env DEBUG=1 rec_wss -p jcba -s fmkaratsu # debug print
"""

import os
import sys
import time
import argparse
import requests
import websocket
import pprint
import http
import unicodedata
import sched
import datetime

class wss:
    def __init__(self, provider, station_id, duration=0):
        self.station_id = station_id
        self.duration = duration
        self.start_time = time.time()
        if 'DEBUG' in os.environ:
            websocket.enableTrace(True)
            http.client.HTTPConnection.debuglevel=1

        # token, location
        if provider == 'jcba':
            headers = {
                    "Origin": "https://www.jcbasimul.com"
                    }
            url = 'https://api.radimo.smen.biz/api/v1/select_stream?station={st}&channel=0&quality=high&burst=5'.format(st=self.station_id)
        elif provider == 'fmplapla':
            headers = {
                    "Origin": "https://fmplapla.com"
                    }
            url = 'https://fmplapla.com/api/select_stream?station={st}&burst=5'.format(st=self.station_id)
        else:
            print('Not provider.')
            print('jcba or fmplapla.')
            sys.exit()
        res = requests.post(url, headers=headers)
        json = res.json()
        if 'DEBUG' in os.environ:
            print(url)
            pprint.pprint(json)
        self.token = json['token']
        self.location = json['location']

        self.ws = websocket.WebSocketApp(
            self.location,
            subprotocols=['listener.fmplapla.com'],
            on_open=self._on_open, on_message=self._on_message)
        try:
            self.ws.run_forever()
        except (Exception, KeyboardInterrupt, SystemExit) as e:
            self.ws.close()

    def _on_message(self, data, message):
        if data:
            sys.stdout.buffer.write(message)
        if self.duration > 0:
            if self.duration < (time.time() - self.start_time):
                raise KeyboardInterrupt

    def _on_open(self, data):
        self.ws.send(self.token)

def find_programme(provider, station, programme):

    if provider == "fmplapla":
        updates = requests.get("https://api.fmplapla.com/api/v1/mobile/updates").json().get('updates')

        timetable = next(filter(
            lambda x: x.get('station') == station
            and x.get('type') == 'timetable', updates), {})

        programmes = timetable.get("data")
    elif provider == "jcba":
        timetables_response = requests.get(f"https://api.radimo.smen.biz/api/v1/mobile/timetables?station={station}")

        if timetables_response.status_code == 304:
            print("This station does not provide a full timetable")
            sys.exit()

        timetables = timetables_response.json()
        programmes = timetables.get("timetables")

    if programmes is None:
        print('Timetable not found. Is the station id correct?')
        sys.exit()

    now = time.time()

    for prog in programmes:
        if unicodedata.normalize("NFKC", programme) in unicodedata.normalize("NFKC", prog["title"]):
            if prog["end"] > time.time():
                return prog["start"], prog["end"], prog["title"]


def main():
    parser = argparse.ArgumentParser(
        description='example: python rec_wss.py -p jcba -s fmkaratsu -t 1800 | ffplay -i pipe:')
    parser.add_argument('-p', '--provider', required=True,
                        help='provider. jcba or fmplapla')
    parser.add_argument('-s', '--station', required=True,
                        help='station id. example: fmkaratsu')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', '--time', type=int, default=0,
                        help='stop writing the output after its seconds reaches duration. it defaults to 0, meaning that loop forever.')
    group.add_argument('-b', '--bangumi', '--programme',
                        help='programme to record. It will wait until the scheduled start time, and then record until the end time. Currently only works with fmplapla.')

    args = parser.parse_args()

    if not args.bangumi:
        radio = wss(args.provider, args.station, args.time)
    else:
        start, end, title = find_programme(args.provider, args.station, args.bangumi)
        if start < time.time():
            start = time.time()

        length = end - start

        pretty_start = datetime.datetime.fromtimestamp(start)
        pretty_end = datetime.datetime.fromtimestamp(end)

        sys.stderr.buffer.write(f"Recording {title} from {pretty_start} to {pretty_end}\n".encode())
        sys.stderr.buffer.flush()

        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enterabs(start, 1, wss, (args.provider, args.station, length))
        scheduler.run()


if __name__ == '__main__':
    main()
