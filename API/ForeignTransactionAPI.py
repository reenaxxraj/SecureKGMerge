from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import requests
import json
import flask
from flask import Flask, request
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

c = None
s = None

DatabaseName = "FT"

LT_URL = "http://127.0.0.1:5000"

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

    # params = {"request" : buff.decode()}

    response = requests.get(LT_URL + "/GetSetUpAndResponse", data=buff)
    print("RESPONSE")
    print(response)
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

    q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
    print(q)
    resp = conn.query(q, db = "neo4j")
    # print(resp)

    nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
    print(nodelist_foreigntransactiondata)
    
    #Call all databases
    return TriggerRest(intersection, StartDB)

current_server_items = None

def TriggerRest(Intersection, StartDB):
    global current_server_items
    current_server_items = Intersection

    # for API_name in API_List.keys:
    #     if API_name != DatabaseName:
    #         (API_List.get(API_name)).Trigger(StartDB, DatabaseName)

    resp = requests.get(LT_URL + "/Trigger", params = {"StartDB" : StartDB, "CallingDB": DatabaseName})

    return resp.json



@app.route('/GetSetUpAndResponse', methods=['GET'])
def GetSetUpAndResponse(ClientRequest):
    
    fpr = 1.0 / (1000000000)
    client_items_len = len(current_server_items)
    s = psi.server.CreateWithNewKey(True)

    setup = s.CreateSetupMessage(fpr, client_items_len, current_server_items)
    resp = s.ProcessRequest(ClientRequest)

    return setup, resp

app.run(host='127.0.0.1', port=5001, debug=False, threaded=True)

# class ForeignTransactionAPI:
#     conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

#     c = None
#     s = None

#     DatabaseName = "FT"


#     def Trigger(self, StartDB, CallingDB):
#         q = "use foreigntransactions MATCH (n) RETURN n"
#         resp = self.conn.query(q, db = "neo4j")
#         nodelist_foreigntransactiondata = [record["n"]["name"] for record in resp]

#         client_items = nodelist_foreigntransactiondata
#         c = psi.client.CreateWithNewKey(True)
#         request = c.CreateRequest(client_items)

#         # setup, resp = (API_List.get(CallingDB)).GetSetUpAndResponse(request)
        
#         setup, resp = LocalTransactionAPI.GetSetUpAndResponse(request)

#         intersection = c.GetIntersection(setup, resp)

#         q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
#         print(q)
#         resp = self.conn.query(q, db = "neo4j")
#         # print(resp)
#         nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
#         print(nodelist_foreigntransactiondata)

#         #Call all databases
#         self.TriggerRest(intersection, StartDB)

#     current_server_items = None

#     def TriggerRest(self, Intersection, StartDB):
#         current_server_items = Intersection

#         # for API_name in API_List.keys:
#         #     if API_name != DatabaseName:
#         #         (API_List.get(API_name)).Trigger(StartDB, DatabaseName)

#         LocalTransactionAPI.Trigger(StartDB, self.DatabaseName)

#     def GetSetUpAndResponse(self, ClientRequest):
        
#         fpr = 1.0 / (1000000000)
#         client_items_len = len(self.current_server_items)
#         s = psi.server.CreateWithNewKey(True)

#         setup = s.CreateSetupMessage(fpr, client_items_len, self.current_server_items)
#         resp = s.ProcessRequest(ClientRequest)

#         return setup, resp


# api.add_resource(ForeignTransactionAPI, "FTAPI")


# def ProcessServerRequest():
#     q = "use foreigntransactions MATCH (n) RETURN n"
#     resp = conn.query(q, db = "neo4j")
#     nodelist_foreigntranactiondata = [record["n"]["name"] for record in resp]
#     client_items = nodelist_foreigntranactiondata
#     c = psi.client.CreateWithNewKey(True)
#     request = c.CreateRequest(client_items)
#     return request

# def ProcessServerResponse(resp, setup):
#     intersection = c.GetIntersection(setup, resp)
#     print(intersection)

#     if (len(intersection) == 0):
#         return None
    
#     else:
#         return TriggerCall(intersection)


# def TriggerCall(intersection):
#     q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
#     print(q)
#     resp = conn.query(q, db = "neo4j")
#     # print(resp)
#     nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
#     print(nodelist_foreigntransactiondata)
#     server_items = intersection

#     #Call LocalTransactions API
#     fpr = 1.0 / (1000000000)
#     client_items_len = len(server_items)
#     s = psi.server.CreateWithNewKey(True)

#     setup = s.CreateSetupMessage(fpr, client_items_len, server_items)
#     clientrequest = LocalTransactionAPI.ProcessServerRequest()

#     resp = s.ProcessRequest(clientrequest)   
#     result = LocalTransactionAPI.ProcessServerResponse(resp, setup)


