
import base64
from re import T
from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import pandas as pd
import requests
import json
import google.protobuf.text_format

from flask import Flask, request
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")
c = None
s = None
DatabaseName = "LT"
# API_List = {"FT":ForeignTransactionAPI}
StartNode = None
current_server_items = None

FT_URL = "http://127.0.0.1:5001/"

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
    StartDB = request.args["StartDB"]
    CallingDB = request.args["CallingDB"]

    q = "use localtransactions MATCH (n) RETURN n"
    resp = conn.query(q, db = "neo4j")
    nodelist_localtransactiondata = [record["n"]["name"] for record in resp]

    client_items = nodelist_localtransactiondata
    c = psi.client.CreateWithNewKey(True)
    request = c.CreateRequest(client_items)

    # setup, resp = (API_List.get(CallingDB)).GetSetUpAndResponse(request)
    
    buff = request.SerializeToString()
    params = {"request" : buff}

    response = requests.get(FT_URL + "/GetSetUpAndResponse", params=params)
    response_msg = json.loads(response.content)
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
        return {"Intersection" : [client_items[i] for i in intersection]}
    else:
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

    return resp.json

@app.route("/GetSetUpAndResponse", methods=["GET"])
def GetSetUpAndResponse():

    print("HELO")
    ClientRequestMessage = request.data

    # print("HELO")
    # print(request.data)
    print(ClientRequestMessage)

    dstReq = psi.Request()
    dstReq.ParseFromString(ClientRequestMessage)
    ClientRequest = dstReq

    # print("DONE")
    
    fpr = 1.0 / (1000000000)
    client_items_len = len(current_server_items)
    s = psi.server.CreateWithNewKey(True)

    setup = s.CreateSetupMessage(fpr, client_items_len, current_server_items)
    resp = s.ProcessRequest(ClientRequest)

    # print("DONE")
    s = base64.b64decode(setup.SerializeToString())
    
    return {"setup": s}

app.run()

# LocalTransactionAPI.MainStart()

# def TriggerCall(server_items):

#     fpr = 1.0 / (1000000000)
#     client_items_len = len(server_items)
#     s = psi.server.CreateWithNewKey(True)

#     setup = s.CreateSetupMessage(fpr, client_items_len, server_items)

#     clientrequest = ForeignTransactionAPI.ProcessServerRequest()

#     resp = s.ProcessRequest(clientrequest)
    
#     result = ForeignTransactionAPI.ProcessServerResponse(resp, setup)

# def ProcessServerRequest():
#     q = "use localtransactions MATCH (n) RETURN n"
#     resp = conn.query(q, db = "neo4j")
#     # print(resp)
#     nodelist_localtranactiondata = [record["n"]["name"] for record in resp]
#     client_items = nodelist_localtranactiondata

#     c = psi.client.CreateWithNewKey(True)
#     request = c.CreateRequest(client_items)
#     return request

# def ProcessServerResponse(resp, setup):
#     intersection = c.GetIntersection(setup, resp)
#     print(intersection)

#     if (len(intersection) == 0):
#         return None
    
#     elif 
#         return TriggerCall(intersection)


