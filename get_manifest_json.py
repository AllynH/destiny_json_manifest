import requests
import redis
import json
from datetime import datetime
import time
import os
import sys
import errno
from urllib.parse import urlparse
from redis_functions import *

# Use your own API key, from https://www.bungie.net/en/Application
API_KEY = 'YOUR_API_KEY_HERE'
BUNGIE_API_KEY = os.getenv('API_KEY') or API_KEY

# URL list:
URL_LIST = {
	'DESTINY_BASE_URL'		: 'https://www.bungie.net/Platform/Destiny2/',
	'BUNGIE_BASE_URL'		: 'https://www.bungie.net',
	'DESTINY_MANIFEST_URL'	: 'https://www.bungie.net/Platform/Destiny2/Manifest/'
}

# File list:
FILE_LIST = {
	'MANIFEST_VERSION'		: 'manifest_version.json',
	'MANIFEST'				: 'manifest.json',
	'SPLIT_DIR'				: os.path.normpath(os.getcwd() + "/split_json/")
}

# HTTP Request header, this sends your API key to Bungie and let's them know you want the response to be gzipped.
# The Requests library handles unzipping the response.
HEADERS = {
	"X-API-Key"				: BUNGIE_API_KEY,
	'Accept-Encoding'		: 'gzip',
	'Content-Encoding'		: 'gzip'
}

# Setup Redis:
if os.environ.get('REDIS_URL'):
	REDIS_HOST = os.environ.get('REDIS_HOST')
	REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
	REDIS_PORT = os.environ.get('REDIS_PORT')
	REDIS_URI = os.environ.get('REDIS_URI')
	REDIS_URL = os.environ.get('REDIS_URL')
	redis_url = urlparse(REDIS_URL)
	redis_db = redis.StrictRedis(host=redis_url.hostname, port=redis_url.port, db=2, password=redis_url.password, charset='utf-8', decode_responses=True)
else:
	redis_db = redis.StrictRedis(host='localhost', port=6379, db=2, charset='utf-8', decode_responses=True)

def connect_redis():
	""" 
		Connect to the Redis server.
		Test the connection
		The following options return a String object instead of a byte stream:
		return charset=utf-8
		decode_response=True
	"""
	# Test the Redis connection:
	try: 
		redis_db.ping()
		print("\t-I- Redis is connected.")
		return True
	except redis.ConnectionError:
		print("\t-E- Redis connection error!")
		return False

	# This should be unreachable:
	return False 

def get_manifest_version():
	""" Send the request to Bungie for the Manifest version information: """
	print("\t-I- Requesting Manifest.")
	manifest_info = requests.get(URL_LIST['DESTINY_MANIFEST_URL'], headers=HEADERS)
	# print(manifest_info.status_code)
	# print(manifest_info.text)
	# print(manifest_info.encoding)

	if not manifest_info.status_code == 200 or manifest_info.json()["ErrorCode"] == 2101:
		print("\t-E- Bungie returned an error")
		print(manifest_info.status_code)
		print(manifest_info.text)
		return "Error"
	else:
		print("\t-I- Successfully recieved the Manifest version information!")
		# Convert text to JSON as it can be displayed very neatly:
		manifest_info_json = json.loads(manifest_info.text)

	# Print the info to a file:
	write_json_file(FILE_LIST['MANIFEST_VERSION'], manifest_info_json)

	return manifest_info_json

def check_manifest_version(manifest_version, db_revision):
	""" 
		Check if the Manifest has been updated from the stored version.
		DestinyVaultRaider.com stores a cache in Redis, so I'll put the code to compare both versions here.
		Implement how you see fit.
	"""

	revision_key = "D2:" + db_revision + ":version"

	manifest_version = manifest_version['Response']['jsonWorldContentPaths']['en']

	if redis_db.get(revision_key) is None:
		return True

	redis_version = json.loads(redis_db.get(revision_key))
	redis_version = redis_version['Response']['jsonWorldContentPaths']['en']

	if redis_version == manifest_version:
		print("\t-I- No difference between stored Manifest and downloaded version!")
		return False

	return True

def get_json_manifest(manifest_url):
	""" 
	Make the HTTP request to Bungie for the JSON Manifest.
	"""
	print("\t-I- Requesting JSON Manifest.")
	manifest_response = requests.get(manifest_url, headers=HEADERS)
	
	# Some useful debug print statements:
	# print(manifest_response.status_code)
	# print(manifest_response.json())
	# print("Printing content")
	# print(manifest_response.content)
	# print(manifest_response.text)
	# print("\t-I- Headers:", manifest_response.headers)

	if not manifest_response.status_code == 200:
		print("\t-E- Bungie returned an error")
		print(manifest_response.status_code)
		print(manifest_response.text)
		return "Error"

	# Print the info to a file - disabled as it causes memory errors:
	# print("\t-I- Wrting Manifest file.")
	# write_json_file(FILE_LIST['MANIFEST'], manifest_response.json())

	print("\t-I- Writing separate manifest files to Redis")
	split_manifest(manifest_response.json())

	return manifest_response.json()

def split_manifest(manifest_json):
	""" Take the JSON Manifest file and writes a new JSON file for each key """

	key_list = manifest_json.keys()

	for key in key_list:
		print("\t\t-I-", key)
		for definition_key, definition_value in manifest_json[key].items():
			redis_db.set("D2:0:" + str(key) + ":" + str(definition_key), json.dumps(definition_value))	
			# print(definition_key)
			# print(definition_value)
	
	print("\t-I- Found", len(key_list), "definitions.")

	# for current_key in key_list:		
	# 	file_name = os.path.join(FILE_LIST['SPLIT_DIR'], current_key + ".json")
	# 	write_json_file(file_name, manifest_json[current_key])

	return True

def make_sure_path_exists(path):
	""" Check to see if a path exists """
	try:
		print("\t-I- Creating: ", path)
		os.makedirs(path)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	return True

def write_json_file(file_name, write_json):
	""" Write JSON to a file: """

	#print("\t-I- Writing file for:", str(file_name))
	
	with open(file_name, 'w') as json_file:
		json_file.write(json.dumps(write_json, sort_keys=True, indent=4))

	return True

def get_definition(definition, def_hash):
	""" 
	Function to find a given definition, return the JSON response: 
	The Last Word: 1364093401
	"""

	revision_key = "D2:metadata:revision"
	db_revision = redis_db.get(revision_key)
	db_namespace = "D2:" + str(db_revision) + ":" + str(definition) + ":" + str(def_hash)

	try:
		definition = json.loads(redis_db.get(db_namespace))
	except TypeError:
		definition = {}

	return definition

if __name__ == "__main__":
	print("\t-I- This is the main function.")

	# Initialise some values:
	manifest_changed_status = False

	# Redis variables:
	db_revision = None
	revision_key = "D2:metadata:revision"

	start_time = time.time()
	redis_status = connect_redis()
	if not redis_status:
		print("\t-E- Redis connection error, exiting!")
		sys.exit()

	manifest_version = get_manifest_version()
	if manifest_version != "Error":
		# print(manifest_version)
		manifest_url = URL_LIST['BUNGIE_BASE_URL'] + manifest_version['Response']['jsonWorldContentPaths']['en']
		print("\t-I- Manifest version:", manifest_version['Response']['jsonWorldContentPaths']['en'])
	else:
		sys.exit()

	db_revision = redis_db.get(revision_key)
	if not db_revision or db_revision is None:
		print("\t-I- Creating Redis database structure.")	
		create_database(redis_db)
		# I've updated db_revision - grab it again:
		db_revision = redis_db.get(revision_key)
		print("\t-I- Current revision is:", db_revision)
	else:
		print("\t-I- Current revision is:", db_revision)
	
	# Temporarily set to False, this will flag any incomplete updates. 
	redis_db.set("D2:" + "metadata:successful", "False")

	# Check to see if the stored manifest version matches the downloaded version:
	manifest_changed_status = check_manifest_version(manifest_version, db_revision)

	redis_manifest_version = "D2:" + db_revision + ":version"
	redis_db.set(redis_manifest_version, json.dumps(manifest_version))
	set_metadata(redis_db, db_revision)

	if manifest_changed_status:
		# Create the directory if it doesn't exist:
		make_sure_path_exists(FILE_LIST['SPLIT_DIR'])
		# Stores the Manifest in the json_manifest object, so you can use it:
		json_manifest = get_json_manifest(manifest_url)

	end_time = time.time() - start_time
	print("-I- Run time:", end_time, "seconds")

	my_def = get_definition("DestinyInventoryItemDefinition", "1364093401")
	print(my_def.get('displayProperties', None))

	my_def = get_definition("DestinyInventoryItemDefinition", "347366834")
	print(my_def.get('displayProperties', None))

	my_def = get_definition("DestinyClassDefinition", "2271682572")
	print(my_def.get('displayProperties', None))

	my_def = get_definition("DestinyMilestoneDefinition", "1300394968")
	print(my_def.get('displayProperties', None))
