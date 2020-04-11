import pyorient

username="user"
password="password"

client = pyorient.OrientDB("localhost", 2424)
session_id = client.connect( username, password )

db_name = "graph_db"

try: 
	client.db_create(db_name, pyorient.TYPE_GRAPH, pyorient.STORAGE_TYPE_PLOCAL)
except pyorient.PYORIENT_EXCEPTION as err:
	logging.critical("Failed to create TinkerHome DB: %" % err)

if (client.db_exists(db_name, pyorient.STORAGE_TYPE_PLOCAL)):
	client.db_open(db_name, username, password)
else:
	client.db_create(db_name, pyorient.TYPE_GRAPH, pyorient.STORAGE_TYPE_PLOCAL)

