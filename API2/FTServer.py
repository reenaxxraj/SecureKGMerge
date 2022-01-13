
from Neo4jConnection import Neo4jConnection
import openmined_psi as psi
from LTClient import LTClientAPI

class FTServerAPI:
    conn = Neo4jConnection(uri="bolt://localhost:7687", user="reena", pwd="1234")

    c = None
    s = None

    DatabaseName = "FT"
    # API_List = {"LT": LocalTransactionAPI}

    current_server_items = None


    def GetSetUpAndResponse(self, ClientRequest):
        
        fpr = 1.0 / (1000000000)
        client_items_len = len(self.current_server_items)
        s = psi.server.CreateWithNewKey(True)

        setup = s.CreateSetupMessage(fpr, client_items_len, self.current_server_items)
        resp = s.ProcessRequest(ClientRequest)

        return setup, resp

