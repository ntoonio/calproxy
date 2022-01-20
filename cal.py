import inspect
import requests

ESCAPES = [["\\\\", "\\"], ["\\;", ";"], ["\\,", ","], ["\\n", "\n"], ["\\N", "\n"]]

def parseiCal(data):
	events = []
	event = None

	lastKey = None

	for line in data.split("\n"):
		if line == "":
			continue
		elif event != None and line.startswith(" "):
			value = line.strip()
			for r in ESCAPES:
				value = value.replace(r[0], r[1])
			event[lastKey] += value
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

			for r in ESCAPES:
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
			value = event[key]
			for r in ESCAPES:
				value = value.replace(r[1], r[0])
			o += key + ":" + value + "\n"

		o += "END:VEVENT" + "\n"

	o += "END:VCALENDAR" + "\n"

	return o

def setUpEvaluates(event, func):
	#print("-----", event, func)
	selectedArgs = inspect.getargspec(func).args
	#print("selectedArgs:", selectedArgs)

	keys = {ek.lower().replace("-", "_"): ek for ek in event}
	#print("keys:", keys)

	args = [event[keys[a]] if a in [k for k in keys] else None for a in selectedArgs]
	#print("args:", args)

	return args
