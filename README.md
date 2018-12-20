# destiny_json_manifest #
Download a copy of the Destiny the game manifest in JSON format.

## Make an API key: ##
Create your own API key from the Bungie website: https://www.bungie.net/en/Application

## Install the requirements: ##
pip install -r requirements.txt 

## Add your API key to the code: ##
Edit the line: API_KEY = 'YOUR_API_KEY_HERE' with your API key.
or
Add an environment variable API_KEY
Windows: set API_KEY=1234abcdefg
Linux: setenv API_KEY 1234abcdefg

## Run the code: ##
python get_manifest_json.py

## What the code does: ##
1. Sends a request for the Destiny 2 Manifest version data.
2. Writes this data to a file called: "manifest_version.json"
3. Uses the URL received from the response to grab the actual JSON formatted Manifest.
4. Sends a request for the Destiny 2 Manifest.
5. Writes this data to a file called: "manifest.json"
6. Parses the Manifest and splits each definition into a seperate file.
7. Writes all of these files in the directory "./split_json"
