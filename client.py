import zmq
import threading
import time

class Client():
    def __init__(self):
        """Initialize client with ZeroMQ connection"""
        self.context = zmq.Context()
        # DEALER socket enables async messaging
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://localhost:5555")
        
        # Client state
        self.clientID = None      # Current user's ID
        self.senderID = None      # Last message sender
        self.polling_interval = 3 # Seconds between checks
        self.running = True       # Control flag
        
        # Start background threads
        self._init_polling()

    def _init_polling(self):
        """Start thread for periodic message checks"""
        def poll_messages():
            while self.running:
                try:
                    self.dealer.send_multipart([b"", b"CHECK_MSGS"])
                    time.sleep(self.polling_interval)
                except:
                    break
        threading.Thread(target=poll_messages, daemon=True).start()

    def connect(self):
        """Register client with server"""
        self.clientID = input("Enter your ID: ").strip()
        self.dealer.send_multipart([b"", f"REGISTER:{self.clientID}".encode()])
        print(f"Connected as {self.clientID}")

    def receive_messages(self):
        """Thread for handling incoming messages"""
        while self.running:
            try:
                _, message = self.dealer.recv_multipart()
                decoded = message.decode()
                
                if decoded == "NO_MSGS":
                    continue
                elif decoded.startswith("ONLINE_USERS:"):
                    # Handle online users list
                    users = decoded.split(":")[1].split(",")
                    print(f"\nOnline users: {', '.join(users) if users else 'None'}")
                elif ":" in decoded:
                    # Handle regular messages
                    sender, content = decoded.split(":", 1)
                    self.senderID = sender
                    print(f"\n[New message from {sender}] {content}\n> ", end="", flush=True)
                    
            except zmq.ZMQError:
                break

    def show_help(self):
        """Display command help"""
        print("\nCOMMANDS:")
        print("@id message    - Send to a specific user")
        print("#chat id       - Change conversation")
        print("#exit          - Leave current conversation")
        print("#users         - Show online users")
        print("#close         - Disconnect\n")

    def check_commands(self, msg):
        """Parse and execute user commands"""
        if msg.startswith("#"):
            cmd = msg[1:].lower()
            if cmd.startswith("chat "):
                # Change conversation target
                new_chat = cmd[5:].strip()
                if new_chat:
                    self.senderID = new_chat
                    print(f"Now talking to: {new_chat}")
            elif cmd == "exit":
                # Exit current chat
                self.senderID = None
                print("Left current conversation")
            elif cmd == "users":
                # Request online users list
                self.dealer.send_multipart([b"", b"REQUEST_ONLINE_USERS"])
            elif cmd == "close":
                # Graceful shutdown
                self.running = False
                self.dealer.send_multipart([b"", f"REMOVE_USER:{self.clientID}".encode()])
            return None, None
        elif msg.startswith("@"):
            # Direct message to specific user
            parts = msg[1:].split(" ", 1)
            if len(parts) == 2:
                recipient, msg_content = parts
                self.senderID = recipient
                return recipient, msg_content
            else:
                print("Invalid format! Use '@recipient message'")
                return None, None
        elif self.senderID:
            # Reply to last sender
            return self.senderID, msg
        else:
            print("No recipient selected! Use #chat or @")
            return None, None

    def send_message(self, recipient, message):
        """Send message to another client through server"""
        self.dealer.send_multipart([b"", f"{recipient}:{message}".encode()])
        print(f"[Sent to {recipient}]")

def main():
    """Main client execution flow"""
    client = Client()
    client.connect()
    client.show_help()

    # Start message receiver thread
    threading.Thread(target=client.receive_messages, daemon=True).start()

    # Main input loop
    while client.running:
        try:
            msg = input("> ").strip()
            recipient, message = client.check_commands(msg)
            if recipient and message:
                client.send_message(recipient, message)
        except KeyboardInterrupt:
            # Handle CTRL+C gracefully
            client.running = False
            client.dealer.send_multipart([b"", f"REMOVE_USER:{client.clientID}".encode()])
            break

if __name__ == "__main__":
    main()