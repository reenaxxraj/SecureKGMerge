from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import requests
import json
import flask
from flask import Flask, request
from google.protobuf.json_format import MessageToJson
from flask_restful import Api
from google.protobuf import json_format
import string
import random

app = Flask(__name__)
api = Api(app)

conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")
# c = None
# s = None
# current_server_items = None

DATABASE_ID = "FT"
REQUEST_ID_LENGTH = 10

LT_URL = "http://127.0.0.1:5000"

APIAddressBook = {"LT" : LT_URL, "CU" : None, "ST" : None}
LoopLog = {}
ServerDirectory = {}

@app.route("/")
def hello_world():
    resp = requests.get(LT_URL+"/MainStart")
    print(json.loads(resp.content)["Intersection"][0])
    return "ok"
  
@app.route("/Trigger", methods=["Get"])
def Trigger():

    StartDB = flask.request.args["StartDB"]
    CallingDB = flask.request.args["CallingDB"]

    q = "use foreigntransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_foreigntransactiondata = [record["n"]["name"] for record in resp]

    client_items = nodelist_foreigntransactiondata
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(client_items)
    
    buff = request.SerializeToString()

    response = requests.get(LT_URL + "/GetSetUpAndResponse", data=buff)
    print("RESPONSE")
    print(response)
    response_msg = response.json()
    print(response_msg)

    setup_msg = response_msg["setup"]
    print("SETUP message received")
    resp_msg = response_msg["resp"]
    print("resp message received")

    dstServer = psi.ServerSetup()
    json_format.Parse(setup_msg, dstServer)
    setup = dstServer
    
    dstResp = psi.Response()
    json_format.Parse(resp_msg, dstResp)
    print("done")
    resp = dstResp

    intersection = c.GetIntersection(setup, resp)
    print("INTERSECTION FOUND")
    print(intersection)
    # q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
    # print(q)
    # resp = conn.query(q, db = "neo4j")
    # # print(resp)

    # nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
    # print(nodelist_foreigntransactiondata)
    
    #Call all databases

    if len(intersection) == 0:
        return None
    else:
        return TriggerRest(intersection, StartDB)

def TriggerRest(Intersection, StartDB):
    global current_server_items
    current_server_items = Intersection

    # for API_name in API_List.keys:
    #     if API_name != DatabaseName:
    #         (API_List.get(API_name)).Trigger(StartDB, DatabaseName)

    resp = requests.get(LT_URL + "/Trigger", params = {"StartDB" : StartDB, "CallingDB": DATABASE_ID})

    return resp

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
    print("DEBUG: datatype: " + str(type(fpr)) + " " + str(type(ClientSetSize)) + " " + str(type(ServerSet[0])))    
    setup = s.CreateSetupMessage(fpr, ClientSetSize, ServerSet)
    resp = s.ProcessRequest(ClientRequest)

    setupJson = MessageToJson(setup)
    respJson = MessageToJson(resp)

    DisposeServerSet(PsiRequestID)
    return {"setup": setupJson, "resp": respJson}

@app.route("/TestSingleLoop", methods=["GET"])
def TestSingleLoop():
    API_ID = "LT"
    StartNode = flask.request.args["start_node"]
    URL = APIAddressBook.get(API_ID)

    LoopID = GenerateRequestID()
    print("Loop search started, Loop ID: " + LoopID)
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

@app.route("/TestPSI", methods=["GET"])
def TestPSI():
    client_items = GetAllEntities()
    URL = APIAddressBook.get("LT")
    intersection = InitiatePSI(client_items, URL)
    return {"intersection" : intersection}

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
    q = "use foreigntransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_foreigntransactiondata = [record["n"]["name"] for record in resp]
    print("[DEBUG]: Nodes Retrieved: " + str(nodelist_foreigntransactiondata))
    return nodelist_foreigntransactiondata

def GetOutwardNodes(Nodes):
    q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(Nodes) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
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

app.run(host='127.0.0.1', port=5001, debug=False, threaded=True)

