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
        NOTE: If you're in a conversation, and you got a new user sending a message to you, the next message will reply THIS person
        '''
        while True:
            try:
                _, message = self.dealer.recv_multipart() # Get the message
                message_decoded = message.decode() # Decoded the message
                sender, msg_content = message_decoded.split(":", 1)
                sender = sender.strip()
                msg_content = msg_content.strip()

                # Update the recipient 
                self.senderID = sender
                
                # Displays the received message
                print(f"[New message from {sender}] {msg_content.strip()}\n", end="", flush=True)
                
                print(f"\nReply to {sender} > ", end="", flush=True)

            except zmq.ZMQError:
                break

    def show_help(self):
        print("\nCOMMANDS:")
        print("@id message    - Send to a specific user")
        print("#chat id       - Change conversation")
        print("#exit          - Leave the current conversation\n")

def main():
    client = Client()
    client.connect()
    client.show_help()

    # Start receiver thread
    threading.Thread(target=client.receive_messages, daemon=True).start() 

    while True:
        msg = input("> ").strip()

        # Special commands
        if msg.startswith("#"):
            cmd = msg[1:].lower()
            
            if cmd.startswith("chat "):
                new_chat = cmd[5:].strip()
                if new_chat:
                    client.senderID = new_chat  # Set new sender for replies
                    print(f"Talking to: {new_chat}")
            elif cmd == "exit":
                client.current_recipient = None
                print("Left the conversation")
                client.show_help()
                
            continue

        if msg.startswith("@"):
            parts = msg[1:].split(" ", 1)
            
            if len(parts) == 2:
                recipient, msg = parts
                client.senderID = recipient  # Updates the sender for future replies
                client.dealer.send_multipart([b"", f"{recipient}:{msg}".encode()])
                print(f"[Message sent to {recipient}]\n")
            else:
                print("Invalid format! Use '@recipient message'")
        
        # Reply to the last sender (if any)
        elif client.senderID:
            client.dealer.send_multipart([b"", f"{client.senderID}:{msg}".encode()])
            print(f"[Reply sent to {client.senderID}]\n")

if __name__ == "__main__":
    main()