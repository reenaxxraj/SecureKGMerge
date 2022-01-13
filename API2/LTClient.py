
from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
from FTServer import FTServerAPI
from FTClient import FTClientAPI
from LTServer import LTServerAPI


class LTClientAPI:
    conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")
    c = None
    s = None
    DatabaseName = "LT"
    # API_List = {"FT":ForeignTransactionAPI}
    StartNode = None
    current_server_items = None

    def MainStart(self):
        StartNode = "Dacia Canty"
        q = "use localtransactions MATCH (cust {name: 'Dacia Canty'})-[:LOCAL_TRANSFER|TO*2..]->(n) RETURN n"
        resp = self.conn.query(q, db = "neo4j")
        nodelist_localtranactiondata = [record["n"]["name"] for record in resp]
    
        self.TriggerRest(nodelist_localtranactiondata, self.DatabaseName)

    def Trigger(self, StartDB):
        q = "use localtransactions MATCH (n) RETURN n"
        resp = self.conn.query(q, db = "neo4j")
        nodelist_localtransactiondata = [record["n"]["name"] for record in resp]

        client_items = nodelist_localtransactiondata
        c = psi.client.CreateWithNewKey(True)
        request = c.CreateRequest(client_items)

        # setup, resp = (API_List.get(CallingDB)).GetSetUpAndResponse(request)
        
        setup, resp = FTServerAPI.GetSetUpAndResponse(request)

        intersection = c.GetIntersection(setup, resp)

        if StartDB == self.DatabaseName:
            return intersection
        else:
            q = "use localtransactions MATCH (n) WHERE n.name IN " + str(intersection) + " MATCH (n)-[:LOCAL_TRANSFER|TO*2..]->(m) RETURN m"
            print(q)
            resp = self.conn.query(q, db = "neo4j")
            # print(resp)
            nodelist_foreigntransactiondata = [record["m"]["name"] for record in resp]
            print(nodelist_foreigntransactiondata)

            #Call all databases
            LTServerAPI.TriggerRest(intersection, StartDB)

    def TriggerRest(self, Intersection, StartDB):
        LTServerAPI.current_server_items = Intersection
        FTClientAPI.Trigger(StartDB, self.DatabaseName)


LTClientAPI.MainStart()
