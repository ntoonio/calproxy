import os
import importlib.util
import time
import logging
import hashlib
import json

import requests
import schedule
import yaml

import cal
import app

logging.basicConfig(level=logging.INFO)

def _md5(s):
	return hashlib.md5(s.encode()).hexdigest()

def downloadSource(source):
	logging.info("Downloading " + source["name"])

	url = source["url"]
	h = _md5(url)

	response = requests.get(url)

	if response.status_code != 200:
		print("Source '" + source["name"] + "' no longer exists")
		return

	with open(app.DATA_PATH + h + ".ics", "w") as f:
		f.write(response.text)

	writeData(h, "last_update", time.time())

def writeData(id, key, value):
	fileName = app.DATA_PATH + id + ".json"

	with open(fileName) as f:
		data = json.load(f)

	data[key] = value

	with open(fileName, "w") as f:
		json.dump(data, f)

def getData(id, key):
	fileName = app.DATA_PATH + id + ".json"

	with open(fileName) as f:
		data = json.load(f)

	return data[key]

def assureDataFile(id):
	# Set up data file
	fileName = app.DATA_PATH + id + ".json"

	# Create the data file if it does not already exist
	if not os.path.exists(fileName):
		with open(fileName, "w+") as f:
			json.dump({
				"last_update": 0
			}, f)

def setUpConfig(config):
	for source in config["sources"]:
		# Set up default configuration
		if "update" not in source:
			source["update"] = 1800

		# Set up automatic configs
		source["id"] = _md5(source["url"])

		# Create a template data file if it does not exist
		assureDataFile(source["id"])

		# Refresh the source if it needs to
		if getData(source["id"], "last_update") + source["update"] < time.time():
			downloadSource(source)

		# Refresh the source at the update interval
		schedule.every(source["update"]).seconds.do(downloadSource, source)
	
	app.configs[config["code"]] = config

def getFunctionFromString(s):
	mod, funcName = s.split(":", 1)

	p = os.path.abspath(app.CALENDAR_PATH + mod + ".py")

	spec = importlib.util.spec_from_file_location("calendars." + mod, p)
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)

	return getattr(m, funcName)

def shouldBeIncluded(event, evaluators):
	for evaluator in evaluators:
		evalFunc = getFunctionFromString(evaluator)

		args = cal.setUpEvaluates(event, evalFunc)

		e = evalFunc(*args)
		if e == True:
			return True
		elif e == False:
			return False

	return True

def applyFilter(f, event):
	filterFunc = getFunctionFromString(f)
	return filterFunc(event)

def getEvents(code):
	config = app.configs[code] if code in app.configs else {}

	if "sources" not in config:
		return False

	# Loop though all the sources for the calendar config
	for source in config["sources"]:
		# Open the calendar file for the coresponing url
		with open(app.DATA_PATH + _md5(source["url"]) + ".ics") as f:
			# Loop thorugh the read events in the file, decoded from iCal
			for event in cal.parseiCal(f.read()):
				# If there are no evaluators or they conclude it should be included...
				if "evaluators" not in source or shouldBeIncluded(event, source["evaluators"]):
					if "filters" in source:
						for f in source["filters"]:
							event = applyFilter(f, event)
					yield event

