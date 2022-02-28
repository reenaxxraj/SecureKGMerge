import requests
import string
import random
import openmined_psi as psi
import flask
from Neo4jConnection import Neo4jConnection
from google.protobuf.json_format import MessageToJson
from google.protobuf import json_format
from flask import Flask, request
from flask_restful import Api
from colorama import Fore

app = Flask(__name__)
api = Api(app)
conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

DATABASE_ID = "LT"
REQUEST_ID_LENGTH = 10
FT_URL = "http://127.0.0.1:5001"
ST_URL = "http://127.0.0.1:5002"
CU_URL = "http://127.0.0.1:5003"
API_ADDRESSBOOK = {"CU" : CU_URL, "FT" : FT_URL, "ST" : ST_URL}

LoopLog = {}
ServerDirectory = {}

@app.route("/TestAPI", methods = ["GET"])
def TestAPI():
    """
    Test function to check if API is set up and running successfully
    ---
    responses:
        200:
        description: Default message (for testing)
        schema:
            api: string
            msg: 
                type: string
                default: API is up and running
    """
    return { "api": DATABASE_ID, "msg" : "API is up and running" }

@app.route("/TestPSI", methods=["GET"])
def TestPSI():
    """
    To perform PSI (Private Set Intersection) with another API's KG
    ---
    parameters:
        api_id: string
    responses:
        200:
        description: Returns intersection between this API's KG and the other API's KG
        schema:
            api: User
            intersection:
                type: list
                description: list of intersecting nodes
    """
    ClientItems = GetAllEntities()
    API_ID = str(request.args.get("api_id"))
    URL = API_ADDRESSBOOK.get(API_ID)
    Intersection = InitiatePSI(ClientItems, URL)
    return {"api": API_ID, "intersection" : Intersection}

@app.route("/StartLoopSearch", methods=["GET"])
def StartLoopSearch():
    """
    To begin the loop search beginning with the current API.
    ---
    parameters:
        start_node: 
            type: string
            description: start node to begin loop search from
    responses:
        200:
        description: Returns intersection between this API's KG and the other API's KG
        schema:
            api: User
            intersection:
                type: list
                description: list of intersecting nodes
    """
    StartNode = flask.request.args["start_node"]
  
    if StartNode not in GetAllEntities():
        return "Start node: " + StartNode + " does not exist in this KG"

    LoopID = GenerateRequestID()
    PrintInfo("Loop search started...")
    PrintDebug("Loop ID: " + LoopID)
    LoopLog[LoopID] = StartNode
    OutwardNodes = GetOutwardNodes([StartNode]) + [StartNode]

    Path = ",".join([DATABASE_ID])
    for api in API_ADDRESSBOOK.keys():
        PSIRequestID = GenerateRequestID()
        PrintInfo("Initiating PSI with " + api + " API...")
        PrintDebug("Request ID generated: " + PSIRequestID)
        ServerDirectory[PSIRequestID] = OutwardNodes

        URL = API_ADDRESSBOOK.get(api)
        response = requests.get(URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : DATABASE_ID, "path" : Path, "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        PrintDebug("Response: " + response.json()["msg"])

        if response.json()["msg"] == "Found":
            DisposeLoopID(LoopID)
            return "Loop found"

    DisposeLoopID(LoopID)
    return "Loop Not Found"

@app.route("/GetSetUpAndResponse", methods=["GET"])
def GetSetUpAndResponse():
    """
    To begin the loop search beginning with the current API.
    ---
    parameters:
        start_node: 
            type: string
            description: start node to begin loop search from
    responses:
        200:
        description: Returns intersection between this API's KG and the other API's KG
        schema:
            api: User
            intersection:
                type: list
                description: list of intersecting nodes
    """
    PrintInfo("Server setup request received...")
    PrintInfo("Client ID: " + str(request.args.get("ID")))

    ClientSetSize = int(request.args.get("set_size"))
    ClientRequestMessage = request.data
    PrintDebug("Client Set Size: " + str(ClientSetSize))

    dstReq = psi.Request()
    dstReq.ParseFromString(ClientRequestMessage)
    ClientRequest = dstReq
    
    fpr = 1.0 / (1000000000)
    s = psi.server.CreateWithNewKey(True)

    PsiRequestID = request.args.get("psi_request_id")
    ServerSet = ServerDirectory.get(PsiRequestID)
    # PrintDebug("Datatype: " + str(type(fpr)) + " " + str(type(ClientSetSize)) + " " + str(type(ServerSet[0])))    
    setup = s.CreateSetupMessage(fpr, ClientSetSize, ServerSet)
    resp = s.ProcessRequest(ClientRequest)

    setupJson = MessageToJson(setup)
    respJson = MessageToJson(resp)

    DisposeServerSet(PsiRequestID)
    return {"setup": setupJson, "resp": respJson}

@app.route("/TestSingleLoop", methods=["GET"])
def TestSingleLoop():
    """
    To begin the loop search beginning with the current API.
    ---
    parameters:
        start_node: 
            type: string
            description: start node to begin loop search from
    responses:
        200:
        description: Returns intersection between this API's KG and the other API's KG
        schema:
            api: User
            intersection:
                type: list
                description: list of intersecting nodes
    """
    ApiID = flask.request.args["api"]
    StartNode = flask.request.args["start_node"]
    URL = API_ADDRESSBOOK.get(ApiID)
    PrintDebug("Start Node: " + StartNode)

    LoopID = GenerateRequestID()
    PrintInfo("Loop search started...")
    PrintInfo("Loop ID: " + LoopID)
    LoopLog[LoopID] = StartNode

    PSIRequestID = GenerateRequestID()
    OutwardNodes = GetOutwardNodes([StartNode])
    ServerDirectory[PSIRequestID] = OutwardNodes

    PrintInfo("PSI initiating with " + api + " API...")
    PrintInfo("Request ID: " + PSIRequestID)    
    response = requests.get(URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : DATABASE_ID, "psi_request_id" : PSIRequestID, "loop_id" : LoopID, "path": "LT"})
    response_msg = response.json()
    PrintInfo("Response: " + response.json()["msg"])

    if response.json()["msg"] == "Found":
        return {"msg" : "Found"}

    DisposeLoopID(LoopID)
    return response_msg


@app.route("/PSI", methods=["GET"])
def StartPSI():
    """
    To begin the loop search beginning with the current API.
    ---
    parameters:
        start_node: 
            type: string
            description: start node to begin loop search from
    responses:
        200:
        description: Returns intersection between this API's KG and the other API's KG
        schema:
            api: User
            intersection:
                type: list
                description: list of intersecting nodes
    """
    EndAPI = flask.request.args["end_id"]
    PSIRequestID = flask.request.args["psi_request_id"]
    LoopID = flask.request.args["loop_id"]
    PathList = (flask.request.args["path"]).split(",")
    PathList.append(DATABASE_ID)
    PathListString = ",".join(PathList)
    # print("[DEBUG]: Path List: " + str(PathList))

    client_items = GetAllEntities()
    Initiator_ID = flask.request.args["initiator_id"]
    PrintInfo("PSI Initiation Request received from  " + Initiator_ID + " API")
    PrintInfo("PSI Request ID: " + PSIRequestID)
    PrintDebug("Path retrieved: " + str(PathList))
    URL = API_ADDRESSBOOK.get(Initiator_ID)

    Intersection = InitiatePSI(client_items, URL, PSIRequestID)
    OutwardNodes = GetOutwardNodes(Intersection)   

    if OutwardNodes == []:
        return {"msg" : "Not Found"}

    if (EndAPI == DATABASE_ID):
        StartNode = LoopLog.get(LoopID)
        if StartNode in Intersection or StartNode in OutwardNodes:
            return {"msg" : "Found"}
        else:
            return {"msg" : "Not Found"}

    for api in API_ADDRESSBOOK.keys():
        if api in PathList and api != EndAPI:
            continue
        API_URL = API_ADDRESSBOOK.get(api)
        PSIRequestID = GenerateRequestID()
        ServerDirectory[PSIRequestID] = OutwardNodes
        
        PrintInfo("Initiating PSI with " + api + " API")
        PrintInfo("Request ID: " + PSIRequestID)
        # print("[DEBUG]: PSI initiation request sent")
        response = requests.get(API_URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : EndAPI, "path" : PathListString , "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        PrintInfo("Response: " + response.json()["msg"])

        if response.json()["msg"] == "Found":
            return {"msg" : "Found"}

    return {"msg" : "Not Found"}


def InitiatePSI(client_items, URL, PSIRequestID):
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(client_items)
    buff = request.SerializeToString()

    PrintInfo("PSI set up & response message request sent...")
    response = requests.get(URL + "/GetSetUpAndResponse", data=buff, params={"ID" : DATABASE_ID, "set_size" : str(len(client_items)), "psi_request_id" : PSIRequestID})
    response_msg = response.json()

    setup_msg = response_msg["setup"]
    resp_msg = response_msg["resp"]

    dstServer = psi.ServerSetup()
    json_format.Parse(setup_msg, dstServer)
    setup = dstServer
    PrintInfo("Setup message received")
    
    dstResp = psi.Response()
    json_format.Parse(resp_msg, dstResp)
    resp = dstResp
    PrintInfo("Resp message received")

    intersection = c.GetIntersection(setup, resp)
    actualIntersection = [client_items[i] for i in intersection]
    PrintDebug("Intersection: " + str(actualIntersection))
    return actualIntersection

def GetAllEntities():
    q = "use localtransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_localtransactiondata = [record["n"]["name"] for record in resp]
    # PrintDebug("Nodes Retrieved: " + str(nodelist_localtransactiondata))
    return nodelist_localtransactiondata

def GetOutwardNodes(Nodes):
    q = "use localtransactions MATCH (n) WHERE n.name IN " + str(Nodes) + " MATCH (n)-[:LOCAL_TRANSFER|TO*2..]->(m) RETURN m"
    # PrintDebug("neo4j query: " + q)
    resp = conn.query(q, db = "neo4j")
    OutwardNodes = [record["m"]["name"] for record in resp]
    PrintDebug("Outward Nodes found: " + str(OutwardNodes))
    return OutwardNodes

def GenerateRequestID():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(REQUEST_ID_LENGTH))

def DisposeServerSet(RequestID):
    ServerDirectory.pop(RequestID)
    PrintInfo("Server set removed")
    PrintInfo("Removed Request ID: " + RequestID)
    return

def DisposeLoopID(LoopID):
    LoopLog.pop(LoopID)
    PrintDebug("Loop finished and removed") 
    PrintDebug("Removed Loop ID: " + LoopID)
    return

def PrintInfo(Text):
    print(Fore.GREEN + "[INFO]: " + Text + Fore.RESET)

def PrintDebug(Text):
    print(Fore.YELLOW + "[DEBUG]: " + Text + Fore.RESET)

def PrintError(Text):
    print(Fore.RED + "[ERROR]: " + Text + Fore.RESET)

app.run()
