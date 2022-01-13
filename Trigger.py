from API.Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import pandas as pd

# print("Connected to Customer API")
conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

print(nodelist_customerdata)


c = psi.client.CreateWithNewKey(True)
s = psi.server.CreateWithNewKey(True)