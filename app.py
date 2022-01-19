import os
import importlib.util
import json
import time
import logging
import threading

import requests
import schedule
import yaml
from flask import Flask

import cal
import utils

PATH = os.path.dirname(os.path.abspath(__file__)) + "/"
CALENDAR_PATH = PATH + "calendars/"
DATA_PATH = PATH + "data/"

configs = {}

app = Flask(__name__)

def start():
	if not os.path.exists(CALENDAR_PATH):
		os.mkdir(CALENDAR_PATH)

	if not os.path.exists(DATA_PATH):
		os.mkdir(DATA_PATH)

	configFiles = [x for x in os.listdir(CALENDAR_PATH) if os.path.isfile(CALENDAR_PATH + x) and (x.endswith(".yaml") or x.endswith(".yml"))]

	for c in configFiles:
		with open(CALENDAR_PATH + c) as f:
			config = yaml.load(f, Loader=yaml.CLoader)
			utils.setUpConfig(config)

	def _runJobs():
		while True:
			schedule.run_pending()
			time.sleep(1)

	threading.Thread(target=_runJobs, daemon=True).start()

	return app

@app.route("/<string:code>")
def req(code):
	events = cal.eventsToiCal(utils.getEvents(code))

	if events == False:
		return "", 404

	return events, 200

if __name__ == "__main__":
	start().run(port=5678)
