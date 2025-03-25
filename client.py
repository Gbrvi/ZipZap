import zmq
import threading
class Client():
    def __init__(self):
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://localhost:5555")
        self.clientID = None
        self.senderID = None

    def connect(self):
        self.clientID = input("Enter your ID: ").strip()
        # Fix: Remove space after REGISTER:
        self.dealer.send_multipart([b"", f"REGISTER:{self.clientID}".encode()])  

    def receive_messages(self):
        '''
        NOTE: If you're in a conversation, and you got a new user sending a message to you, the next message will reply THIS person
        '''
        while True:
            try:
                _, message = self.dealer.recv_multipart() # Get the message
                message_decoded = message.decode() # Decoded the message
                self.senderID = message_decoded.split(":")[0].strip() # Get the senderID format client1:message
                print(f"\n[New message from {self.senderID}] {message_decoded}", end="", flush=True) #Show up the message

                print(f"Reply to {self.senderID} > ", end="", flush=True) #Reply to the person
            except zmq.ZMQError:
                break

def set_recipientID(): # Set the recipient ID (Who you gonna send the message)
    return input("Send to (ID): ").strip()

def main():
    client = Client()
    client.connect()

    # Start receiver thread
    threading.Thread(target=client.receive_messages, daemon=True).start() 

    recipient_id = set_recipientID()

    while True:
        msg = input(f"Message to {recipient_id}:  ([-1] to change contact) ").strip()

        if(msg == "-1"):
            recipient_id = set_recipientID()
            continue # restart the loop 

        client.dealer.send_multipart([b"", f"{recipient_id}:{msg}".encode()]) # Send message

if __name__ == "__main__":
    main()