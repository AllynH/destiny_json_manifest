import requests
import json
from datetime import datetime
import time
import os
import sys
import errno

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

def get_manifest_version():
	""" Send the request to Bungie for the Manifest version information: """
	print("\t-I- Requesting Manifest!")
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

def check_manifest_version():
	""" 
		Check if the Manifest has been updated from the stored version.
		DestinyVaultRaider.com stores a cache in Redis, so I'll put the code to compare both versions here.
		Implement how you see fit.
	"""

	return True

def get_json_manifest(manifest_url):
	""" 
	Make the HTTP request to Bungie for the JSON Manifest.
	"""
	print("\t-I- Requesting JSON Manifest!")
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

	# Print the info to a file:
	print("\t-I- Wrting Manifest file!")
	#write_json_file(FILE_LIST['MANIFEST'], manifest_response.json())

	print("\t-I- Writing separate manifest files!")
	split_manifest(manifest_response.json())

	return manifest_response.json()

def split_manifest(manifest_json):
	""" Take the JSON Manifest file and writes a new JSON file for each key """

	key_list = []

	for key in manifest_json.keys():
		key_list.append(key)
	
	print("\t-I- Found", len(key_list), "definitions.")

	for current_key in key_list:		
		file_name = os.path.join(FILE_LIST['SPLIT_DIR'], current_key + ".json")
		write_json_file(file_name, manifest_json[current_key])

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

if __name__ == "__main__":
	print("\t-I- This is the main function!")

	# Initialise some values:
	manifest_changed_status = False

	start_time = time.time()
	manifest_version = get_manifest_version()

	if manifest_version != "Error":
		# print(manifest_version)
		manifest_url = URL_LIST['BUNGIE_BASE_URL'] + manifest_version['Response']['jsonWorldContentPaths']['en']
		print("\t-I- Manifest version:", manifest_version['Response']['jsonWorldContentPaths']['en'])
	else:
		sys.exit()

	# Dummy function that always returns True, you can modify for your own needs:
	manifest_changed_status = check_manifest_version()

	if manifest_changed_status:
		# Create the directory if it doesn't exist:
		make_sure_path_exists(FILE_LIST['SPLIT_DIR'])
		# Stores the Manifest in the json_manifest object, so you can use it:
		json_manifest = get_json_manifest(manifest_url)

	end_time = time.time() - start_time
	print("-I- Run time:", end_time, "seconds")
