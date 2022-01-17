import os
import importlib.util
import time
import logging
import hashlib

import requests
import schedule
import yaml

import cal
import web

logging.basicConfig(level=logging.INFO)

def _md5(s):
	return hashlib.md5(s.encode()).hexdigest()

def downloadSource(source):
	url = source["url"]
	h = _md5(url)

	response = requests.get(url)

	if response.status_code != 200:
		print("Source '" + source["name"]["name"] + "' no longer exists")
		return

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

		if "update" not in source:
			source["update"] = 1800

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

def getEvents(md5, configs, sourceId=None):
	for calendar in configs:
		if md5 == calendar[0]["id"]:
			calendar = calendar[0]
			allEvents = []

			for source in calendar["sources"]:
				if sourceId != None and sourceId != source["id"]:
						continue

				with open("data/" + source["id"] + ".ics") as f:
					events = cal.parseiCal(f.read())

				for event in events:
					if "evaluators" not in source or shouldBeIncluded(event, source["evaluators"]):
						allEvents.append(event)

			return allEvents

	return False

def saveConfig(configs):
	for c in configs:
		output = yaml.dump(c[0], Dumper=yaml.CDumper)
		with open("calendars/" + c[1], "w") as f:
			f.write(output)

