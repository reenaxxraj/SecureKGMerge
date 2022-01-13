from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
from LTServer import LTServerAPI
from FTServer import FTServerAPI

class FTClientAPI:
    conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

    DatabaseName = "FT"
    # API_List = {"LT": LocalTransactionAPI}


    def Trigger(self, StartDB):
        q = "use foreigntransactions MATCH (n) RETURN n"
        resp = self.conn.query(q, db = "neo4j")
        nodelist_foreigntransactiondata = [record["n"]["name"] for record in resp]

        client_items = nodelist_foreigntransactiondata
        c = psi.client.CreateWithNewKey(True)
        request = c.CreateRequest(client_items)

        # setup, resp = (API_List.get(CallingDB)).GetSetUpAndResponse(request)
        
        setup, resp = LTServerAPI.GetSetUpAndResponse(request)

        intersection = c.GetIntersection(setup, resp)

        q = "use foreigntransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:OVERSEA_TRANSFER_OUT|TO|OVERSEA_TRANSFER_IN|FROM*1..]->(m) RETURN m"
        print(q)
        resp = self.conn.query(q, db = "neo4j")
        # print(resp)
        nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
        print(nodelist_foreigntransactiondata)

        #Call all databases
        FTServerAPI.TriggerRest(intersection, StartDB)