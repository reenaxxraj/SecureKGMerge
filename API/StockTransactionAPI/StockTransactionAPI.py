import requests
import string
import random
import openmined_psi as psi
import flask
from Neo4jConnection import Neo4jConnection
from google.protobuf.json_format import MessageToJson
from google.protobuf import json_format
from flask import Flask, abort, request
from flask_restful import Api
from colorama import Fore

app = Flask(__name__)
api = Api(app)
conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

DATABASE_ID = "ST"
REQUEST_ID_LENGTH = 10
FT_URL = "http://127.0.0.1:5001"
LT_URL = "http://127.0.0.1:5000"
CU_URL = "http://127.0.0.1:5003"
API_ADDRESSBOOK = {"CU" : CU_URL,"FT" : FT_URL, "LT" : LT_URL}

LoopLog = {}
ServerDirectory = {}

@app.route("/StartLoopSearch", methods=["GET"])
def StartLoopSearch():
    """
    To begin the loop search beginning with the current API.
    ---
    parameters:
        start_node: 
            type:           string
            description:    start node to begin loop search
    responses:
        200:
            description: Returns a report on loop findings
            schema:
                current_api: string
                report:
                    paths_searched: 
                        type:           list of lists of strings
                        description:    list of all paths that were searched
                        example:        [["FT", "LT", "FT"], ["FT", "CU"]]
                    loop_found:
                        type:           Boolean
                        description:    True if loop found; Fales if loop not found
                    path_found:
                        type:           list of strings
                        description:    if loop_found == True, returns the path of the loop. Else, returns None.
                        example:        ["FT", "LT", "FT"], None
        404:
            description: Start node was not found in this API's KG
    """
    StartNode = flask.request.args["start_node"]
  
    if StartNode not in GetAllEntities():
        abort(404, description="Start node:" + StartNode + " does not exist in this KG. Unable to conduct search.")

    LoopID = GenerateRequestID()
    PrintInfo("Loop search started...")
    PrintDebug("Loop ID: " + LoopID)
    LoopLog[LoopID] = StartNode
    OutwardNodes = GetOutwardNodes([StartNode]) + [StartNode]

    PathSoFar = [DATABASE_ID]
    PathsSearched = []
    LoopFound = False
    PathFound = None
    for api in API_ADDRESSBOOK.keys():
        PSIRequestID = GenerateRequestID()
        PrintInfo("Initiating PSI with " + api + " API...")
        PrintDebug("Request ID generated: " + PSIRequestID)
        ServerDirectory[PSIRequestID] = OutwardNodes

        URL = API_ADDRESSBOOK.get(api)
        response = requests.get(URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : DATABASE_ID, "path_so_far" : PathSoFar, "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        LoopFound = response.json()["loop_found"]
        PathsSearched += response.json()["paths_searched"]
        PrintDebug("Path Searched: " + str(PathsSearched))
        PrintInfo("Response: Loop_found = " + str(response.json()["loop_found"]))

        if LoopFound == True:
            PathFound = response.json()["path_found"]
            break

    DisposeLoopID(LoopID)
    return {"current_api": DATABASE_ID, "report": {"path_searched": PathsSearched, "loop_found": LoopFound, "path_found": PathFound}}

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
    PathSoFar = (flask.request.args["path_so_far"]).split(",")
    PathSoFar.append(DATABASE_ID)
    PathSoFarString = ",".join(PathSoFar)

    client_items = GetAllEntities()
    Initiator_ID = flask.request.args["initiator_id"]
    PrintInfo("PSI Initiation Request received from  " + Initiator_ID + " API")
    PrintInfo("PSI Request ID: " + PSIRequestID)
    PrintDebug("Path retrieved: " + str(PathSoFar))
    URL = API_ADDRESSBOOK.get(Initiator_ID)

    Intersection = InitiatePSI(client_items, URL, PSIRequestID)
    if Intersection == []:
        return {"loop_found" : False, "paths_searched": [PathSoFar]}

    OutwardNodes = GetOutwardNodes(Intersection)   
    if Intersection == [] or OutwardNodes == []:
        return {"loop_found" : False, "paths_searched": [PathSoFar]}

    if (EndAPI == DATABASE_ID):
        StartNode = LoopLog.get(LoopID)
        if StartNode in Intersection or StartNode in OutwardNodes:
            return {"loop_found" : True, "paths_searched": [PathSoFar], "path_found": PathSoFar}
        else:
            return {"loop_found" : False, "paths_searched": [PathSoFar]}

    PathsSearched = []
    for api in API_ADDRESSBOOK.keys():
        if api in PathSoFar and api != EndAPI:
            continue
        API_URL = API_ADDRESSBOOK.get(api)
        PSIRequestID = GenerateRequestID()
        ServerDirectory[PSIRequestID] = OutwardNodes
        
        PrintInfo("Initiating PSI with " + api + " API")
        PrintInfo("Request ID: " + PSIRequestID)
        response = requests.get(API_URL + "/PSI", params={"initiator_id" : DATABASE_ID, "end_id" : EndAPI, "path_so_far" : PathSoFarString , "psi_request_id" : PSIRequestID, "loop_id" : LoopID})
        LoopFound = response.json()["loop_found"]
        PathsSearched += response.json()["paths_searched"]
        PrintDebug("Path Searched: " + str(PathsSearched))
        PrintInfo("Response: Loop_found = " + str(response.json()["loop_found"]))

        if LoopFound == True:
            PathFound = response.json()["path_found"]
            return {"loop_found" : LoopFound, "paths_searched": PathsSearched, "path_found": PathFound}

    return {"loop_found" : LoopFound, "paths_searched": PathsSearched}

def InitiatePSI(ClientItems, URL, PSIRequestID):
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(ClientItems)
    buff = request.SerializeToString()

    PrintInfo("PSI set up & response message request sent...")
    response = requests.get(URL + "/GetSetUpAndResponse", data=buff, params={"ID" : DATABASE_ID, "set_size" : str(len(ClientItems)), "psi_request_id" : PSIRequestID})
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
    actualIntersection = [ClientItems[i] for i in intersection]
    PrintDebug("Intersection: " + str(actualIntersection))
    return actualIntersection

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

def GetAllEntities():
    q = "use stocktransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist = [record["n"]["name"] for record in resp]
    # PrintDebug("Nodes Retrieved: " + str(nodelist))
    return nodelist

def GetOutwardNodes(Nodes):
    q = "use stocktransactions MATCH (n) WHERE n.name IN " + str(Nodes) + " MATCH (n)-[:BUY_STOCKS|OF*2..]->(m) RETURN m"
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

app.run(host='127.0.0.1', port=5002, debug=False, threaded=True)


