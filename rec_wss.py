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
import json
import base64

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
        stream_json = res.json()
        if 'DEBUG' in os.environ:
            print(url)
            pprint.pprint(stream_json)
        self.token = stream_json['token']
        self.location = stream_json['location']

        payload = json.loads(base64.b64decode(self.token.split('.')[1] + '=='))
        if payload.get('sub', '').startswith('/announce'):
            print('You are geo-blocked.')
            sys.exit()

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


def main():
    parser = argparse.ArgumentParser(
        description='example: python rec_wss.py -p jcba -s fmkaratsu -t 1800 | ffplay -i pipe:')
    parser.add_argument('-p', '--provider', required=True,
                        help='provider', choices=['jcba', 'fmplapla'])
    parser.add_argument('-s', '--station', required=True,
                        help='station id. example: fmkaratsu')
    parser.add_argument('-t', '--time', type=int, default=0,
                        help='stop writing the output after its seconds reaches duration. it defaults to 0, meaning that loop forever.')
    args = parser.parse_args()
    radio = wss(args.provider, args.station, args.time)


if __name__ == '__main__':
    main()
