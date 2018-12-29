import redis
from datetime import datetime

def create_database(redis_db):
	"""
	Create an empty Redis database structure.
	"""

	destiny_version = "D2"
	db_revision = "0"

	# Set revision to "0"
	# print(destiny_version + ":" + revision)
	# redis_db.set(destiny_version + ":" + "revision", "0")

	# set metadata to empty:
	redis_db.set(destiny_version + ":" + "metadata:date", str(datetime.now()))
	redis_db.set(destiny_version + ":" + "metadata:revision", db_revision)
	redis_db.set(destiny_version + ":" + "metadata:update_type", "forced")
	redis_db.set(destiny_version + ":" + "metadata:successful", "True")

	return True

def set_metadata(redis_db, db_revision):
	""" 
	set: 
		Current revision
		Date of update
		Update type - e.g. forced update, or new Manifest revision
		successful update - set upon completion, to test for errors.
	"""
	destiny_version = "D2"
	# print("date: ", datetime.now())
	# print("revision:", db_revision)

	# set metadata to empty:
	redis_db.set(destiny_version + ":" + "metadata:date", str(datetime.now()))
	redis_db.set(destiny_version + ":" + "metadata:revision", db_revision)
	redis_db.set(destiny_version + ":" + "metadata:update_type", "forced")
	redis_db.set(destiny_version + ":" + "metadata:successful", "True")
	
	return True
