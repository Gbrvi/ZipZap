import zmq

class Server():
    # Initilize the server settings 
    def __init__(self):
        """
        NOTE: Initilize the attributes
        """
        self.context = zmq.Context() # Manage sockets
        self.router = self.context.socket(zmq.ROUTER) # Create a ROUTER -> It tacks clients by their identity 
        self.router.bind("tcp://*:5555") # Bind to a port

        self.clients = {} #Client dict id -> user

    def _addClient(self, client_id, identity):
        """
        Function to add clients to server 
        """
        self.clients[client_id] = identity
        print(f"New added client: {client_id}")

    def _send_users_online(self, identity):

        online_users = ",".join(self.clients.keys())
        self.router.send_multipart([identity,b"",f"ONLINE_USERS: {online_users}".encode()])

    def _get_client_id(self, identity):
        """
        Function to get client ID
        """
        for client_id, stored_identity in self.clients.items():
            if stored_identity == identity:
                return client_id
        return None
    
    def _handle_registration(self, identity, message):
        """
        Function to filter the pattern and add cliente

        The pattern receive is: b'REGISTER:name 
        """
        client_id = message.split(":")[1].strip() # Get only client_id
        self._addClient(client_id, identity) 
        return True
    
    def _process_message(self, identity, message):

        if(message.startswith("REGISTER")):
            self._handle_registration(identity, message)
            return True
        
        elif(message.startswith("REQUEST_ONLINE_USERS")):
            self._send_users_online(identity)
        else:
            self._handle_regular_message(identity, message)
             
    def _handle_regular_message(self, identity, message):
        """
        Function to filter message before send it 
        """
        if ":" not in message:
            return False
        
        recipient_id, actual_msg = message.split(":", 1) # Pattern: "NAME:MESSAGE"
        sender_id = self._get_client_id(identity)  # Helper to find sender's ID

        if not sender_id: # Check if sender exists
            print("Error! Unknown sender")
            return False

        if recipient_id not in self.clients: # Check if client is connected to server
            print(f"Error! Client {recipient_id} does not exist.")
            return False
    
        self._forward_message(recipient_id, sender_id, actual_msg) 

    def _forward_message(self, recipient_id, sender_id, actual_msg):
        """
        Function to send the message [sender_id] -> [recipient_id]: [message]"""
        self.router.send_multipart([
        self.clients[recipient_id],
        b"",
         f"{sender_id}:{actual_msg.strip()}".encode()  
        ])

        print(f"Forwarded: {sender_id} → {recipient_id}: {actual_msg.strip()}")
    

    def start(self):
        print("Server started. Waiting for messages...\n")
        while True:
            identity, _, message = self.router.recv_multipart()
            decoded_msg = message.decode()

            self._process_message(identity, decoded_msg)

def main():
    server = Server()
    server.start()

main()