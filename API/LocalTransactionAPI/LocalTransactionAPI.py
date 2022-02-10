from ast import In
import re
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
# c = None
# s = None
DATABASE_ID = "LT"
REQUEST_ID_LENGTH = 10

# StartNode = None
# current_server_items = None

FT_URL = "http://127.0.0.1:5001"

APIAddressBook = {"FT" : FT_URL, "CU" : None, "ST" : None}
LoopLog = {}
ServerDirectory = {}

@app.route("/MainStart", methods=["Get"])
def MainStart():
    StartNode = "Dacia Canty"
    q = "use localtransactions MATCH (cust {name: 'Dacia Canty'})-[:LOCAL_TRANSFER|TO*2..]->(n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_localtranactiondata = [record["n"]["name"] for record in resp]
    result = TriggerRest(nodelist_localtranactiondata, DatabaseName)
    return result

@app.route("/Trigger", methods=["Get"])
def Trigger():
    StartDB = flask.request.args["StartDB"]
    print("Inside Trigger method")
    CallingDB = flask.request.args["CallingDB"]

    q = "use localtransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_localtransactiondata = [record["n"]["name"] for record in resp]

    client_items = nodelist_localtransactiondata
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(client_items)

    # setup, resp = (API_List.get(CallingDB)).GetSetUpAndResponse(request)
    
    buff = request.SerializeToString()
    # params = {"request" : buff}

    response = requests.get(FT_URL + "/GetSetUpAndResponse", data=buff)
    # response_msg = json.loads(response.content)
    response_msg = response.json()
    print(response_msg)

    setup_msg = response_msg["setup"]
    resp_msg = response_msg["resp"]

    dstServer = psi.ServerSetup()
    dstServer.ParseFromString(setup_msg)
    setup = dstServer
    
    dstResp = psi.Response()
    dstResp.ParseFromString(resp_msg)
    resp = dstResp
    intersection = c.GetIntersection(setup, resp)

    if StartDB == DatabaseName:
        print("RETURN Successfully")
        return {"Intersection" : [client_items[i] for i in intersection]}
    else:
        print("Kill me")
        q = "use localtransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:LOCAL_TRANSFER|TO*2..]->(m) RETURN m"
        print(q)
        resp = conn.query(q, db = "neo4j")
        # print(resp)
        nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
        print(nodelist_foreigntransactiondata)

        #Call all databases
        return TriggerRest(intersection, StartDB)        

def TriggerRest( Intersection, StartDB):
    global current_server_items
    current_server_items = Intersection
    print("DEBUG:")
    print(Intersection)

    # for API_name in API_List.keys():
    #     if API_name != DatabaseName:
    #         (API_List.get(API_name)).Trigger(StartDB, DatabaseName)

    resp = requests.get(FT_URL + "/Trigger", params = {"StartDB" : StartDB, "CallingDB": DatabaseName})

    return resp

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
    q = "use localtransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_localtransactiondata = [record["n"]["name"] for record in resp]
    print("[DEBUG]: Nodes Retrieved: " + str(nodelist_localtransactiondata))
    return nodelist_localtransactiondata

def GetOutwardNodes(Nodes):
    q = "use localtransactions MATCH (n) WHERE n.name IN " + str(Nodes) + " MATCH (n)-[:LOCAL_TRANSFER|TO*2..]->(m) RETURN m"
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

app.run()
