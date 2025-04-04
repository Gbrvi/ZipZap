import zmq 
import threading

class Client():
    def __init__(self):
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://localhost:5555")
        self.clientID = None
        self.senderID = None # Stores the last sender

    def connect(self):
        self.clientID = input("Enter your ID: ").strip()
        # Fix: Remove space after REGISTER:
        self.dealer.send_multipart([b"", f"REGISTER:{self.clientID}".encode()])  
        print(f"Connected as {self.clientID}")

    def receive_messages(self):
        '''
        NOTE: If you're in a conversation, and you got a new user sending a message to you, the next message will reply and get connected to this person
        '''
        while True:
            try:
                _, message = self.dealer.recv_multipart() # Get the message
                decoded_message = message.decode() # Decoded the message
               
                if(decoded_message.startswith("ONLINE_USERS")):
                    users = decoded_message.split(":", 1)[1].split(",")
                    print(f"\nOnline Users:", ",".join(users) if users else "None")
                else:
                    sender, msg_content = decoded_message.split(":", 1)

                    #UPTADE SenderID
                    self.senderID = sender
                
                    # Displays the received message
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
        # Special commands

        if msg.startswith("#"):
            cmd = msg[1:].lower()
            
            if cmd.startswith("chat "):
                new_chat = cmd[5:].strip()
                if new_chat:
                    self.senderID = new_chat  # Set new sender for replies
                    print(f"Talking to: {new_chat}")
                    return None, None
            elif cmd == "exit":
                self.current_recipient = None
                print("Left the conversation")
                self.show_help()
                self._request_users_online()
                return None, None
        
            elif cmd == "close":
                self._send_remove_users(self.clientID)
                exit()
                return None, None
            
            elif cmd == "users":
                self._request_users_online()
                return None, None
                
        if msg.startswith("@"):
            parts = msg[1:].split(" ", 1)
            
            if len(parts) == 2:
                recipient, msg = parts
                self.senderID = recipient  # Updates the sender for future replies
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

    while True:
        msg = input("> ").strip()

        recipient, message = client.check_commands(msg)
        
        if(recipient and message):
            client.send_message(recipient, message)

if __name__ == "__main__":
    main()