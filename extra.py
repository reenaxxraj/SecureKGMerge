# def test_serialization_setup_msg(reveal_intersection):
#     s = psi.server.CreateWithNewKey(reveal_intersection)

#     server_items = ["Element " + str(2 * i) for i in range(10000)]

#     fpr = 1.0 / (1000000000)
#     setup = s.CreateSetupMessage(fpr, 1000, server_items)

#     buff = setup.SerializeToString()
#     recreated = psi.ServerSetup()
#     recreated.ParseFromString(buff)
#     assert isinstance(buff, bytes)
#     assert setup.bits == recreated.bits

# def test_serialization_request(reveal_intersection):
#     c = psi.client.CreateWithNewKey(reveal_intersection)
#     client_items = ["Element " + str(i) for i in range(1000)]
#     request = c.CreateRequest(client_items)

#     buff = request.SerializeToString()
#     recreated = psi.Request()
#     recreated.ParseFromString(buff)
#     assert isinstance(buff, bytes)
#     assert request.encrypted_elements == recreated.encrypted_elements
#     assert request.reveal_intersection == recreated.reveal_intersection

# def test_serialization_response(reveal_intersection):
#     c = psi.client.CreateWithNewKey(reveal_intersection)
#     s = psi.server.CreateWithNewKey(reveal_intersection)

#     client_items = ["Element " + str(i) for i in range(1000)]
#     server_items = ["Element " + str(2 * i) for i in range(10000)]

#     fpr = 1.0 / (1000000000)
#     setup = s.CreateSetupMessage(fpr, len(client_items), server_items)
#     req = c.CreateRequest(client_items)
#     resp = s.ProcessRequest(req)

#     buff = resp.SerializeToString()
#     recreated = psi.Response()
#     recreated.ParseFromString(buff)

#     assert isinstance(buff, bytes)
#     assert resp.encrypted_elements == recreated.encrypted_elements

