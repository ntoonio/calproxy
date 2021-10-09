import os
import importlib.util
import json
import time
import logging
import threading
import atexit

import requests
import schedule
import yaml
from flask import Flask

import cal
from utils import _md5

app = Flask(__name__)

def downloadSource(source):
	url = source["url"]
	h = _md5(url)

	response = requests.get(url)

	with open("data/" + h + ".ics", "w") as f:
		f.write(response.text)

	source["last_update"] = time.time()

def setUpConfig(config):
	if "id" not in config:
		config["id"] = _md5(config["name"])

	for source in config["sources"]:
		if "id" not in source:
			source["id"] = _md5(source["url"])

		if "last_update" not in source:
			source["last_update"] = 0

		if source["last_update"] + source["update"] < time.time():
			logging.info("Downloading " + source["id"])

			downloadSource(source)

		schedule.every(source["update"]).seconds.do(downloadSource, source)

def shouldBeIncluded(event, evaluators):
	for evaluator in evaluators:
		mod, func = evaluator.split(":", 1)

		p = os.path.abspath("calendars/" + mod + ".py")

		spec = importlib.util.spec_from_file_location("calendars." + mod, p)
		m = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(m)

		evalFunc = getattr(m, func)

		args = cal.setUpEvaluates(event, evalFunc)

		e = evalFunc(*args)
		if e == True:
			return True
		elif e == False:
			return False

	return True

def getEvents(md5):
	for calendar in configs:
		if md5 == calendar[0]["id"]:
			calendar = calendar[0]
			allEvents = []

			for source in calendar["sources"]:
				with open("data/" + source["id"] + ".ics") as f:
					events = cal.parseiCal(f.read())

				for event in events:
					if "evaluators" not in source or shouldBeIncluded(event, source["evaluators"]):
						allEvents.append(event)

			return allEvents

	return False

def start():
	global configs

	logging.basicConfig(level=logging.INFO)
	configFiles = [x for x in os.listdir("calendars/") if os.path.isfile("calendars/" + x) and (x.endswith(".yaml") or x.endswith(".yml"))]

	configs = []

	for c in configFiles:
		with open("calendars/" + c) as f:
			config = yaml.load(f, Loader=yaml.CLoader)
			setUpConfig(config)
			configs.append((config, c))

	def _runJobs():
		while True:
			schedule.run_pending()
			time.sleep(1)

	threading.Thread(target=_runJobs, daemon=True).start()

	atexit.register(save)

	return app

def save():
	for c in configs:
		output = yaml.dump(c[0], Dumper=yaml.CDumper)
		with open("calendars/" + c[1], "w") as f:
			f.write(output)

@app.route("/<string:string>")
def req(string):
	events = cal.eventsToiCal(getEvents(string))

	if events == False:
		return "", 404

	return events, 200

if __name__ == "__main__":
	createApp()
