import zmq
import time
import threading

class Server():
    def __init__(self):
        """Initialize server with ZeroMQ context and sockets"""
        self.context = zmq.Context()
        # ROUTER socket handles async client connections
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind("tcp://*:5555")  # Bind to port 5555
        
        # Data structures
        self.clients = {}          # {client_id: socket_identity}
        self.pending_messages = {} # {recipient_id: [messages]}
        self.last_ping = {}        # {client_id: last_ping_time}

    def _add_client(self, client_id, identity):
        """Register new client connection"""
        self.clients[client_id] = identity
        self.last_ping[client_id] = time.time()
        print(f"New client connected: {client_id}")

    def _send_online_users(self, identity):
        """Send list of online users to requesting client"""
        online_users = ",".join(self.clients.keys())
        self.router.send_multipart([
            identity, 
            b"", 
            f"ONLINE_USERS:{online_users}".encode()
        ])

    def _get_client_id(self, identity):
        """Find client ID by socket identity"""
        for client_id, stored_identity in self.clients.items():
            if stored_identity == identity:
                return client_id
        return None

    def _store_message(self, recipient_id, message):
        """Store message for offline recipient"""

        if recipient_id not in self.pending_messages:
            self.pending_messages[recipient_id] = []

        self.pending_messages[recipient_id].append(message)
        # Auto-clean after 60 seconds
        threading.Timer(60.0, self._clean_messages, args=[recipient_id]).start()

    def _clean_messages(self, recipient_id):
        """Remove expired pending messages"""

        if recipient_id in self.pending_messages:
            del self.pending_messages[recipient_id]

    def _send_pending_messages(self, client_id, identity):
        """Deliver all pending messages to reconnected client"""
        
        if client_id in self.pending_messages:
            for msg in self.pending_messages[client_id]:
                self.router.send_multipart([identity, b"", msg.encode()])
            del self.pending_messages[client_id]
        else:
            self.router.send_multipart([identity, b"", b"NO_MSGS"])

    def _process_message(self, identity, message):
        """Main message processing router"""

        # Check for pending messages request
        if message == "CHECK_MSGS":
            client_id = self._get_client_id(identity)
            if client_id:
                self._send_pending_messages(client_id, identity)
            return True
        
        # Handle online users request
        elif message == "REQUEST_ONLINE_USERS":
            self._send_online_users(identity)
            return True
        
        # Handle new client registration
        elif message.startswith("REGISTER:"):
            client_id = message.split(":")[1].strip()
            self._add_client(client_id, identity)
            return True
        
        # Handle client disconnection
        elif message.startswith("REMOVE_USER:"):
            client_id = message.split(":")[1]
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.pending_messages:
                del self.pending_messages[client_id]
            print(f"User {client_id} removed")
            return True
        
        # Handle regular messages
        elif ":" in message:
            recipient_id, content = message.split(":", 1)
            sender_id = self._get_client_id(identity)
            
            if not sender_id:
                print("Error: Unknown sender")
                return False
                
            # Deliver immediately if recipient is online
            if recipient_id in self.clients:
                self.router.send_multipart([
                    self.clients[recipient_id],
                    b"",
                    f"{sender_id}:{content}".encode()
                ])
                print(f"Delivered: {sender_id} → {recipient_id}: {content}")
            else:
                # Store for later delivery
                self._store_message(recipient_id, f"{sender_id}:{content}")
                print(f"Stored for {recipient_id}: {content}")
            return True
        
        return False

    def start(self):
        """Main server loop"""
        print("Server started. Waiting for messages...")
        while True:
            # Receive message parts [identity, delimiter, content]
            identity, _, message = self.router.recv_multipart()
            self._process_message(identity, message.decode())

if __name__ == "__main__":
    server = Server()
    server.start()