import pyorient

username="user"
password="password"

client = pyorient.OrientDB("localhost", 2424)
session_id = client.connect( "admin", "admin_passwd" )

db_name = "graph_db"

try: 
	client.db_create(db_name, pyorient.TYPE_GRAPH, pyorient.STORAGE_TYPE_PLOCAL)
except pyorient.PYORIENT_EXCEPTION as err:
	logging.critical("Failed to create TinkerHome DB: %" % err)

if (client.db_exists(db_name, pyorient.STORAGE_TYPE_PLOCAL)):
	client.db_open(db_name, username, password)
else:
	client.db_create(db_name, pyorient.TYPE_GRAPH, pyorient.STORAGE_TYPE_PLOCAL)

client.command("create class db_name extends V")
client.command("insert into db_name set node = 'example', key = 'value' ")
client.command("create class second_layer extends V")
client.command("insert into second_layer node = 'example2', key ='value2")
client.command('create class Node extend E')

node_edges = client.command(
	"create edge Node from("
	"select from db_name where node='rat"
	") to ("
	"select from second_layer where node = 'example_2"
	")"
)

#kinda like sql database
#https://github.com/mogui/pyorient/blob/master/README.md
