from API.CustomerAPI.Neo4jConnection import Neo4jConnection
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

def InitiatePSI(client_items):
    print("[INFO]: FT API has initiated PSI")
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(client_items)

    buff = request.SerializeToString()
    response = requests.get(LT_URL + "/GetSetUpAndResponse", data=buff)
    response_msg = response.json()

    setup_msg = response_msg["setup"]
    resp_msg = response_msg["resp"]

    dstServer = psi.ServerSetup()
    json_format.Parse(setup_msg, dstServer)
    setup = dstServer
    print("[INFO]: setup message received from server")
    
    dstResp = psi.Response()
    json_format.Parse(resp_msg, dstResp)
    resp = dstResp
    print("[INFO]: resp message received from server")

    intersection = c.GetIntersection(setup, resp)
    print("[INFO]: Intersection found" + str(intersection))
   