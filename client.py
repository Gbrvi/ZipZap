import zmq 
import threading
import time

class Client():
    def __init__(self):
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://localhost:5555")
        self.clientID = None
        self.senderID = None # Stores the last sender
        self.ping_interval = 10  # Ping a cada 5 segundos
        self.running = True

    def connect(self):
        self.clientID = input("Enter your ID: ").strip()
        self.dealer.send_multipart([b"", f"REGISTER:{self.clientID}".encode()])  
        print(f"Connected as {self.clientID}")

    def start_ping_loop(self):
        """Thread para enviar pings periodicamente"""
        while self.running:
            try:
                self.dealer.send_multipart([b"", b"PING"])
                time.sleep(self.ping_interval)
            except:
                break

    def receive_messages(self):
        while self.running:
            try:
                _, message = self.dealer.recv_multipart()
                decoded_message = message.decode()
            
                if decoded_message == "PONG":
                    continue
                elif decoded_message.startswith("ONLINE_USERS"):
                    users = decoded_message.split(":", 1)[1].split(",")
                    print(f"\nOnline Users:", ",".join(users) if users else "None")
                else:
                    sender, msg_content = decoded_message.split(":", 1)
                    self.senderID = sender
                    print(f"\n[New message from {sender}] {msg_content.strip()}\n", end="", flush=True)
                    print(f"\nReply to {sender} > ", end="")

            except zmq.ZMQError:
                break

    def show_help(self):
        print("""\n\tCOMMANDS:
        @id message    - Send to a specific user
        #chat id       - Change conversation
        #exit          - Leave the current conversation
        #close         - Close the program
        #users         - Show users online
        """)

    def check_commands(self, msg):
        if msg.startswith("#"):
            cmd = msg[1:].lower()
            
            if cmd.startswith("chat "):
                new_chat = cmd[5:].strip()
                if new_chat:
                    self.senderID = new_chat
                    print(f"Talking to: {new_chat}")
                    return None, None
            elif cmd == "exit":
                self.senderID = None
                print("Left the conversation")
                self.show_help()
                self._request_users_online()
                return None, None
            elif cmd == "close":
                self.running = False
                self._send_remove_users(self.clientID)
                return None, None
            elif cmd == "users":
                self._request_users_online()
                return None, None
                
        if msg.startswith("@"):
            parts = msg[1:].split(" ", 1)
            if len(parts) == 2:
                recipient, msg = parts
                self.senderID = recipient
                return (self.senderID, msg)
            else:
                print("Invalid format! Use '@recipient message'")
        elif self.senderID:
            return (self.senderID, msg)

    def send_message(self, senderID, msg):
        self.dealer.send_multipart([b"", f"{senderID}:{msg}".encode()])
        print(f"[Reply sent to {self.senderID}]\n")

    def _request_users_online(self):
        self.dealer.send_multipart([b"", b"REQUEST_ONLINE_USERS"])

    def _send_remove_users(self, clientID):
        self.dealer.send_multipart([b"", f"REMOVE_USER:{clientID}".encode()])


def main():
    client = Client()
    client.connect()
    client.show_help()

    # Start receiver thread
    threading.Thread(target=client.receive_messages, daemon=True).start()
    
    # Start ping thread
    threading.Thread(target=client.start_ping_loop, daemon=True).start()

    while client.running:
        try:
            msg = input("> ").strip()
            recipient, message = client.check_commands(msg)
            if recipient and message:
                client.send_message(recipient, message)
        except KeyboardInterrupt:
            client.running = False
            client._send_remove_users(client.clientID)
            break

if __name__ == "__main__":
    main()