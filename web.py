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

app = Flask(__name__)

def start():
	global configs

	configFiles = [x for x in os.listdir("calendars/") if os.path.isfile("calendars/" + x) and (x.endswith(".yaml") or x.endswith(".yml"))]

	configs = []

	for c in configFiles:
		with open("calendars/" + c) as f:
			config = yaml.load(f, Loader=yaml.CLoader)
			utils.setUpConfig(config)
			configs.append((config, c))

	def _runJobs():
		while True:
			schedule.run_pending()
			time.sleep(1)

	threading.Thread(target=_runJobs, daemon=True).start()

	return app

@app.route("/<string:string>")
def req(string):
	events = cal.eventsToiCal(utils.getEvents(string, configs))

	if events == False:
		return "", 404

	return events, 200

if __name__ == "__main__":
	start().run(port=5678)
