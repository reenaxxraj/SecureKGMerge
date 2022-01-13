from API.Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import pandas as pd

# print("Connected to Customer API")
conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

# print(nodelist_customerdata)

c = psi.client.CreateWithNewKey(True)
s = psi.server.CreateWithNewKey(True)


def Start(request):



    query_string = "use customerdata MATCH (n) RETURN n"
    resp = conn.query(query_string, db = "neo4j")
    nodelist_customerdata = [record["n"]["name"] for record in resp]
    print(nodelist_customerdata)

    server_items = nodelist_customerdata
    fpr = 1.0 / (1000000000)


    len_client_items = len[request.data]
    setup = s.CreateSetupMessage(fpr, len(len_client_items), server_items)

    resp = s.ProcessRequest(request)

    intersection = c.GetIntersection(setup, resp)

    print(intersection)

def TriggerCalls():



def SendRequest():
