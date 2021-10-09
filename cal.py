import inspect
import requests

def parseiCal(data):
	events = []
	event = {}

	lastKey = None

	for line in data.split("\n"):
		if line == "":
			continue
		elif line.startswith(" "):
			event[lastKey] += line.strip()
			continue

		line = line.strip()

		if line == "BEGIN:VEVENT":
			event = {}
		elif line == "END:VEVENT":
			events.append(event)
			event = None
		elif event != None:
			key, value = line.split(":", 1)
			assert key != "END"
			lastKey = key

			replace = [["\\\\", "\\"], ["\\;", ";"], ["\\,", ","], ["\\N", "\n"], ["\\n", "\n"]]
			for r in replace:
				value = value.replace(r[0], r[1])
			event[key] = value

	return events

def eventsToiCal(events):
	o = """BEGIN:VCALENDAR
VERSION:2.0
METHOD:PUBLISH
X-WR-CALNAME:Temp-name
X-WR-CALDESC:Date limit -
X-PUBLISHED-TTL:PT20M
CALSCALE:GREGORIAN
PRODID:Temp-prod-id""" + "\n"

	for event in events:
		o += "BEGIN:VEVENT" + "\n"

		for key in event:
			o += key + ":" + event[key] + "\n"

		o += "END:VEVENT" + "\n"

	o += "END:VCALENDAR" + "\n"

	return o

def setUpEvaluates(event, func):
	selectedArgs = inspect.getargspec(func).args

	keys = {ek.lower().replace("-", "_"): ek for ek in event}

	args = [event[keys[a]] if a in [k for k in keys] else None for a in selectedArgs]

	return args
