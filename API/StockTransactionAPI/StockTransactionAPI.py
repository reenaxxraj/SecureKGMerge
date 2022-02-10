import json
from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import requests
import string
import random
from google.protobuf.json_format import MessageToJson
from google.protobuf import json_format
import flask
from flask import Flask, request
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")
DATABASE_ID = "LT"
REQUEST_ID_LENGTH = 10

FT_URL = "http://127.0.0.1:5001"
LT_URL = "http://127.0.0.1:5000"
CU_URL = "http://127.0.0.1:5003"

APIAddressBook = {"FT" : FT_URL, "CU" : CU_URL, "LT" : LT_URL}
LoopLog = {}
ServerDirectory = {}

@app.route("/TestAPI")
def hello_world():
    resp = requests.get(LT_URL+"/MainStart")
    print(json.loads(resp.content)["Intersection"][0])
    return "ok"
  
@app.route("/TestPSI", methods=["GET"])
def TestPSI():
    client_items = GetAllEntities()
    URL = APIAddressBook.get("FT")
    intersection = InitiatePSI(client_items, URL)
    return {"intersection" : intersection}

@app.route("/GetSetUpAndResponse", methods=["GET"])
def GetSetUpAndResponse():

    print("[INFO]: client request to setup server received")
    print("[INFO]: client ID: " + str(request.args.get("ID")))

    ClientSetSize = int(request.args.get("set_size"))
    ClientRequestMessage = request.data
    print("[INFO]: client set size: " + str(ClientSetSize))

    dstReq = psi.Request()
    dstReq.ParseFromString(ClientRequestMessage)
    ClientRequest = dstReq
    print("[DEBUG]: client request processed")
    
    fpr = 1.0 / (1000000000)
    s = psi.server.CreateWithNewKey(True)

    PsiRequestID = request.args.get("psi_request_id")
    # ServerSet = GetAllEntities()
    ServerSet = ServerDirectory.get(PsiRequestID)
    print("DEBUG: datatype: " + str(type(fpr)) + " " + str(type(ClientSetSize)) + " " + str(type(ServerSet)))
    setup = s.CreateSetupMessage(fpr, ClientSetSize, ServerSet)
    resp = s.ProcessRequest(ClientRequest)

    setupJson = MessageToJson(setup)
    respJson = MessageToJson(resp)
    
    DisposeServerSet(PsiRequestID)
    return {"setup": setupJson, "resp": respJson}

@app.route("/TestSingleLoop", methods=["GET"])
def TestSingleLoop():
    API_ID = "FT"
    StartNode = flask.request.args["start_node"]
    URL = APIAddressBook.get(API_ID)
    print("DEBUG: start_node: " + StartNode)

    LoopID = GenerateRequestID()
    print("[INFO]: Loop search started, Loop ID: " + LoopID)
    LoopLog[LoopID] = StartNode

    PSIRequestID = GenerateRequestID()
    print("[INFO]: Request ID generated: " + PSIRequestID)
    OutwardNodes = GetOutwardNodes([StartNode])
    ServerDirectory[PSIRequestID] = OutwardNodes

    response = requests.get(URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : DATABASE_ID, "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
    response_msg = response.json()

    DisposeLoopID(LoopID)
    return response_msg

@app.route("/PSI", methods=["GET"])
def StartPSI():

    EndAPI = flask.request.args["end_id"]
    PSIRequestID = flask.request.args["psi_request_id"]
    LoopID = flask.request.args["loop_id"]

    client_items = GetAllEntities()
    Initiator_ID = flask.request.args["initiator_id"]
    URL = APIAddressBook.get(Initiator_ID)

    Intersection = InitiatePSI(client_items, URL, PSIRequestID)
    OutwardNodes = GetOutwardNodes(Intersection)

    if (EndAPI == DATABASE_ID):
        print("[DEBUG]: End Reached")
        StartNode = LoopLog.get(LoopID)
        if StartNode in OutwardNodes:
            return {"msg" : "Loop exist"}

    for api in APIAddressBook.keys():
        API_URL = APIAddressBook.get(api)
        PSIRequestID = GenerateRequestID()
        ServerDirectory[PSIRequestID] = OutwardNodes
        
        print("[INFO]: Request ID generated: " + PSIRequestID)
        response = requests.get(API_URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : EndAPI, "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        return response.json()


def InitiatePSI(client_items, URL, PSIRequestID):
    print("[INFO]: FT API has initiated PSI")
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(client_items)
    buff = request.SerializeToString()

    response = requests.get(URL + "/GetSetUpAndResponse", data=buff, params={"ID" : DATABASE_ID, "set_size" : str(len(client_items)), "psi_request_id" : PSIRequestID})
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
    actualIntersection = [client_items[i] for i in intersection]
    print("[INFO]: Intersection found: " + str(actualIntersection))
    return actualIntersection

def GetAllEntities():
    q = "use stocktransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_localtransactiondata = [record["n"]["name"] for record in resp]
    print("[DEBUG]: Nodes Retrieved: " + str(nodelist_localtransactiondata))
    return nodelist_localtransactiondata

def GetOutwardNodes(Nodes):
    q = "use stocktransactions MATCH (n) WHERE n.name IN " + str(Nodes) + " MATCH (n)-[:BUY_STOCKS|OF*2..]->(m) RETURN m"
    print("[DEBUG]: neo4j query: " + q)
    resp = conn.query(q, db = "neo4j")
    OutwardNodes = [record["m"]["name"] for record in resp]
    print("[DEBUG]: Outward Nodes found: " + str(OutwardNodes))
    return OutwardNodes

def GenerateRequestID():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(REQUEST_ID_LENGTH))

def DisposeServerSet(RequestID):
    ServerDirectory.pop(RequestID)
    print("[INFO]: Server set removed; Request ID: " + RequestID)
    return

def DisposeLoopID(LoopID):
    LoopLog.pop(LoopID)
    print("[INFO]: Loop finished and removed; Loop ID: " + LoopID)
    return

app.run(host='127.0.0.2', port=5002, debug=False, threaded=True)


