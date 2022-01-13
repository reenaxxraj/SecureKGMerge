from google.protobuf import message
from API.Neo4jConnection import Neo4jConnection
import openmined_psi as psi
import json
import pandas as pd


conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")
print("Connected to Data base")

query_string = "use customerdata MATCH (n) RETURN n"
resp = conn.query(query_string, db = "neo4j")

print("\nCustomer Data:")
nodelist_customerdata = [record["n"]["name"] for record in resp]

print("\nCustomer Data:")
print(nodelist_customerdata)

q = "use localtransactions MATCH (cust {name: 'Dacia Canty'})-[:LOCAL_TRANSFER|TO*2..]->(n) RETURN n"
resp = conn.query(q, db = "neo4j")
# print(resp)

nodelist_localtranactiondata = [record["n"]["name"] for record in resp]

print("\nOutward nodes from Dacia")
print(nodelist_localtranactiondata)

c = psi.client.CreateWithNewKey(True)
s = psi.server.CreateWithNewKey(True)

client_items = nodelist_customerdata
server_items = nodelist_localtranactiondata

fpr = 1.0 / (1000000000)
setup = s.CreateSetupMessage(fpr, len(client_items), server_items)
msg = c.CreateRequest(client_items)

# print(request.encrypted_elements)
# buff = request.SerializeToString()

buff = msg.SerializeToString()

dst = psi.Request()
dst.ParseFromString(buff)
request = dst

# request = dup(True, c.CreateRequest(client_items), psi.Request())
print(request)
# print(req)

resp = s.ProcessRequest(request)

intersection = c.GetIntersection(setup, resp)
# iset = set(intersection)
print("First Intersection" + str(intersection))

custAndlocaltransaction = [client_items[i] for i in intersection]
custAndlocaltransaction = server_items
print(custAndlocaltransaction)



q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(custAndlocaltransaction) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
print(q)
resp = conn.query(q, db = "neo4j")
# print(resp)
nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
print(nodelist_foreigntransactiondata)

q = "use localtransactions MATCH (n) RETURN n"
resp = conn.query(q, db = "neo4j")
# print(resp)

nodelist_localtranactiondata = [record["n"]["name"] for record in resp]

print(nodelist_localtranactiondata)


c = psi.client.CreateWithNewKey(True)
s = psi.server.CreateWithNewKey(True)

client_items = nodelist_foreigntransactiondata
server_items = nodelist_localtranactiondata
print(server_items)

fpr = 1.0 / (1000000000)
setup = s.CreateSetupMessage(fpr, len(client_items), server_items)

request = c.CreateRequest(client_items)

resp = s.ProcessRequest(request)

fpr = 1.0 / (1000000000)
setup = s.CreateSetupMessage(fpr, len(client_items), server_items)
request = c.CreateRequest(client_items)
resp = s.ProcessRequest(request)

intersection = c.GetIntersection(setup, resp)
# iset = set(intersection)
print(intersection)

custAndlocaltransaction = [client_items[i] for i in intersection]
print(custAndlocaltransaction)

#Check relationship between both?
# q = "use foreigntransactions MATCH (n) -[:TO*1..]->(n) RETURN n"
# resp = conn.query(q, db = "neo4j")
# # print(resp)
# nodelist_foreigntransactiondata = [record["n"]["name"] for record in resp]
# print(nodelist_foreigntransactiondata)


def dup(do, msg, dst):
    if not do:
        return msg
    buff = msg.SerializeToString()
    dst.ParseFromString(buff)
    return dst


def test_sanity(reveal_intersection):
    c = psi.client.CreateWithNewKey(reveal_intersection)

def test_server_sanity(reveal_intersection):
    s = psi.server.CreateWithNewKey(reveal_intersection)
    if s == None:
        print("[DEBUG]: Server setup failed")

    key = s.GetPrivateKeyBytes()
    if key == None:
        print("[DEBUG]: Server private key missing")

    other = psi.server.CreateFromKey(key, reveal_intersection)
    newkey = other.GetPrivateKeyBytes()

    if key != newkey:
        print("[DEBUG]: Server private key does not match")

def test_client_sanity(reveal_intersection):
    c = psi.client.CreateWithNewKey(reveal_intersection)
    if c == None:
        print("[DEBUG]: Client setup failed")

    key = c.GetPrivateKeyBytes()
    if key == None:
        print("[DEBUG]: Client private key missing")

    other = psi.client.CreateFromKey(key, reveal_intersection)
    newkey = other.GetPrivateKeyBytes()

    if key != newkey:
        print("[DEBUG]: Client private key does not match")

def test_client_server(reveal_intersection, duplicate):
    c = psi.client.CreateWithNewKey(reveal_intersection)
    s = psi.server.CreateWithNewKey(reveal_intersection)

    client_items = ["Element " + "hello" + str(i) for i in range(500)]
    print(len(client_items))
    server_items = ["Element " + "hello" + str(i*2) for i in range(10000)]
    print(len(server_items))

    fpr = 1.0 / (1000000000)
    
    setup = dup(
        duplicate, s.CreateSetupMessage(fpr, len(client_items), server_items), psi.ServerSetup()
    )
    

    request = dup(duplicate, c.CreateRequest(client_items), psi.Request())
    # print(request)
    resp = dup(duplicate, s.ProcessRequest(request), psi.Response())

    if reveal_intersection:
        intersection = c.GetIntersection(setup, resp)
        iset = set(intersection)
        print(iset)
        print(len(iset))


# test_client_server(True, True)

def test_server_client(reveal_intersection):
    c = psi.client.CreateWithNewKey(reveal_intersection)
    s = psi.server.CreateWithNewKey(reveal_intersection)

    client_items = ["hello" for i in range(1000)]
    server_items = ["hello" for i in range(10000)]

    fpr = 1.0 / (1000000000)
    setup = s.CreateSetupMessage(fpr, len(client_items), server_items)
    request = c.CreateRequest(client_items)
    resp = s.ProcessRequest(request)

    if reveal_intersection:
        intersection = c.GetIntersection(setup, resp)
        iset = set(intersection)
        for idx in range(len(client_items)):
            if idx % 2 == 0:
                assert idx in iset
            else:
                assert idx not in iset
    else:
        intersection = c.GetIntersectionSize(setup, resp)
        assert intersection >= (len(client_items) / 2.0)
        assert intersection <= (1.1 * len(client_items) / 2.0)

test_client_server(True, True)