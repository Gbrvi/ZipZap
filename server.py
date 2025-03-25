import zmq

class Server():
    # Initilize the server settings 
    def __init__(self):
        self.context = zmq.Context() # Manage sockets
        self.router = self.context.socket(zmq.ROUTER) # Create a ROUTER -> It tacks clients by their identity 
        self.router.bind("tcp://*:5555") # Bind to a port

        self.clients = {} #Client dict id -> user

    def _addClient(self, client_id, identity):
        self.clients[client_id] = identity

    def start(self):
        print("Server started. Waiting for messages...")
        while True:
            identity, _, message = self.router.recv_multipart()
            decoded_msg = message.decode()

            # Handle registration (remove space after "REGISTER:")
            if decoded_msg.startswith("REGISTER:"):
                client_id = decoded_msg.split(":")[1].strip()  # <- Fix: Add .strip()
                self._addClient(client_id, identity)
                print(f"{client_id} registered.")
                continue

            # Handle messages
            if ":" not in decoded_msg:
                continue

            # Split into [recipient_id, actual_msg]
            recipient_id, actual_msg = decoded_msg.split(":", 1)
            sender_id = self._get_client_id(identity)  # Helper to find sender's ID

            if recipient_id not in self.clients:
                print(f"Error! Client {recipient_id} does not exist.")
                continue

            # Forward message format: "sender_id:actual_msg"
            self.router.send_multipart([
                self.clients[recipient_id],
                b"",
                f"{sender_id}:{actual_msg}".encode()
            ])
            print(f"Forwarded: {sender_id} → {recipient_id}: {actual_msg}")

    def _get_client_id(self, identity):
        for client_id, stored_identity in self.clients.items():
            if stored_identity == identity:
                return client_id
        return None

def main():
    server = Server()
    server.start()

main()