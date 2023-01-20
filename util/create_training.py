import configparser
import csv

import osmnx as ox
import psycopg2

config = configparser.ConfigParser()
config.sections()
config.read('conf.ini')
config['DEFAULT']['base_path'] = "datasets/porto"
graphml_file_path = config['osm']['graphml_file_path']

db_name = config['database']['db_name']
db_user = config['database']['user']
db_password = config['database']['password']
db_host = config['database']['host']
db_port = config['database']['port']

G = ox.load_graphml(graphml_file_path)
G = ox.get_digraph(G)

G_nodes = list(G.nodes)

conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
print("Opened database connection successfully")

cursor = conn.cursor()

query = """
SELECT tripid, taxiid, trajtimestamp,startnode,endnode,cpath,realduration,mappedduration
FROM trajectory, datasets
WHERE EXTRACT(YEAR from trajtimestamp) = 2013
AND EXTRACT(MONTH from trajtimestamp) = 7
AND EXTRACT(DAY from trajtimestamp) = 2
AND realduration - mappedduration > 0
AND trajectory.datasetid = datasets.datasetid
"""

cursor.execute(query)
results = cursor.fetchall()

header = ['TRIP_ID', 'CALL_TYPE', 'ORIGIN_CALL', 'ORIGIN_STAND', 'TAXI_ID', 'TIMESTAMP', 'DAY_TYPE', 'MISSING_DATA',
          'POLYLINE', 'START_NODE', 'END_NODE', 'CPATH', 'OPATH', 'REAL_DURATION', 'MAPPED_DURATION']
print(len(header))

with open('test.csv', 'w', encoding='UTF8') as f:
    writer = csv.writer(f)

    # write the header
    writer.writerow(header)

    for row in results:
        # data.append
        if row[3] in G.nodes and row[4] in G.nodes:
            data = [row[0], "", "", "", row[1], row[2], "", "", "", row[3], row[4], row[5], "", row[6], row[7]]
            writer.writerow(data)

conn.close()
print("Closed database connection successfully")
