import yaml

import utils

configFile = "UMU.yaml"
sourceId = "b8e3b74c4b8d155337bbf8aa1e75e0ea"

with open("calendars/" + configFile) as f:
	config = yaml.load(f, Loader=yaml.CLoader)
	utils.setUpConfig(config)

events = utils.getEvents(config["id"], [(config, configFile)], sourceId)

if events == False:
	print("No events")
else:
	for e in events:
		print("-", e["SUMMARY"])

utils.saveConfig([(config, configFile)])
