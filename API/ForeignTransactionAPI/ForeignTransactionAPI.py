from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import requests
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
DATABASE_ID = "FT"
REQUEST_ID_LENGTH = 10

LT_URL = "http://127.0.0.1:5000"
ST_URL = "http://127.0.0.1:5002"
CU_URL = "http://127.0.0.1:5003"

APIAddressBook = {"CU" : CU_URL,"LT" : LT_URL, "ST" : ST_URL}
LoopLog = {}
ServerDirectory = {}

@app.route("/TestAPI", methods=["GET"])
def Test():
    return {"message" : "hello"}

@app.route("/StartLoopSearch", methods=["GET"])
def StartLoopSearch():
    StartNode = flask.request.args["start_node"]

    if StartNode not in GetAllEntities():
        return "Start node: " + StartNode + " does not exist in this KG"

    LoopID = GenerateRequestID()
    print("Loop search started, Loop ID: " + LoopID)
    LoopLog[LoopID] = StartNode
    OutwardNodes = GetOutwardNodes([StartNode]) + [StartNode]

    Path = ",".join([DATABASE_ID])
    for api in APIAddressBook.keys():
        PSIRequestID = GenerateRequestID()
        print("[INFO]: Initiating PSI with " + api + " API")
        print("[INFO]: Request ID generated: " + PSIRequestID)
        ServerDirectory[PSIRequestID] = OutwardNodes

        URL = APIAddressBook.get(api)
        response = requests.get(URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : DATABASE_ID, "path" : Path, "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        print("[INFO]: Response: " + response.json()["msg"])

        if response.json()["msg"] == "Found":
            DisposeLoopID(LoopID)
            return "Loop found"

    DisposeLoopID(LoopID)
    return "Loop Not Found"
  

@app.route("/GetSetUpAndResponse", methods=["GET"])
def GetSetUpAndResponse():
    print("[INFO]: Client request to setup server received")
    print("[INFO]: Client ID: " + str(request.args.get("ID")))

    ClientSetSize = int(request.args.get("set_size"))
    ClientRequestMessage = request.data
    print("[INFO]: Client set size: " + str(ClientSetSize))

    dstReq = psi.Request()
    dstReq.ParseFromString(ClientRequestMessage)
    ClientRequest = dstReq
    
    fpr = 1.0 / (1000000000)
    s = psi.server.CreateWithNewKey(True)

    PsiRequestID = request.args.get("psi_request_id")
    ServerSet = ServerDirectory.get(PsiRequestID)
    # print("DEBUG: datatype: " + str(type(fpr)) + " " + str(type(ClientSetSize)) + " " + str(type(ServerSet[0])))    
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
    # print("[INFO]: PSI Initiated " + str(flask.request))
    EndAPI = flask.request.args["end_id"]
    PSIRequestID = flask.request.args["psi_request_id"]
    LoopID = flask.request.args["loop_id"]
    PathList = (flask.request.args["path"]).split(",")
    print("[DEBUG]: Path retrieved: " + str(PathList))
    PathList.append(DATABASE_ID)
    PathListString = ",".join(PathList)
    # print("[DEBUG]: Path List: " + str(PathList))

    client_items = GetAllEntities()
    Initiator_ID = flask.request.args["initiator_id"]
    URL = APIAddressBook.get(Initiator_ID)

    Intersection = InitiatePSI(client_items, URL, PSIRequestID)
    OutwardNodes = GetOutwardNodes(Intersection)   

    if OutwardNodes == []:
        return {"msg" : "Not Found"}

    if (EndAPI == DATABASE_ID):
        StartNode = LoopLog.get(LoopID)
        if StartNode in OutwardNodes or StartNode in Intersection:
            return {"msg" : "Found"}
        else:
            return {"msg" : "Not Found"}

    for api in APIAddressBook.keys():
        if api in PathList and api != EndAPI:
            continue
        API_URL = APIAddressBook.get(api)
        PSIRequestID = GenerateRequestID()
        ServerDirectory[PSIRequestID] = OutwardNodes
        
        print("[INFO]: PSI initiating with " + api + " API")
        print("[INFO]: Request ID: " + PSIRequestID)
        # print("[DEBUG]: PSI initiation request sent")
        response = requests.get(API_URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : EndAPI, "path" : PathListString , "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        print("[INFO]: Response: " + response.json()["msg"])

        if response.json()["msg"] == "Found":
            return {"msg" : "Found"}

    return {"msg" : "Not Found"}

@app.route("/TestPSI", methods=["GET"])
def TestPSI():
    client_items = GetAllEntities()
    URL = APIAddressBook.get("LT")
    intersection = InitiatePSI(client_items, URL)
    return {"intersection" : intersection}

def InitiatePSI(client_items, URL, PSIRequestID):
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
    print("[DEBUG]: Setup message received from server")
    
    dstResp = psi.Response()
    json_format.Parse(resp_msg, dstResp)
    resp = dstResp
    print("[DEBUG]: Resp message received from server")

    intersection = c.GetIntersection(setup, resp)
    actualIntersection = [client_items[i] for i in intersection]
    print("[INFO]: Intersection: " + str(actualIntersection))
    return actualIntersection

def GetAllEntities():
    q = "use foreigntransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_foreigntransactiondata = [record["n"]["name"] for record in resp]
    print("[DEBUG]: Nodes Retrieved: " + str(nodelist_foreigntransactiondata))
    return nodelist_foreigntransactiondata

def GetOutwardNodes(Nodes):
    q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(Nodes) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
    # print("[DEBUG]: neo4j query: " + q)
    resp = conn.query(q, db = "neo4j")
    OutwardNodes = [record["m"]["name"] for record in resp]
    print("[DEBUG]: Outward Nodes found: " + str(OutwardNodes))
    return OutwardNodes

def GenerateRequestID():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(REQUEST_ID_LENGTH))

def DisposeServerSet(RequestID):
    ServerDirectory.pop(RequestID)
    print("[INFO]: Server set removed; Removed Request ID: " + RequestID)
    return

def DisposeLoopID(LoopID):
    LoopLog.pop(LoopID)
    print("[INFO]: Loop finished and removed; Removed Loop ID: " + LoopID)
    return

app.run(host='127.0.0.1', port=5001, debug=False, threaded=True)

