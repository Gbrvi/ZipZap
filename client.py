import zmq
import threading
class Client():
    def __init__(self):
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://localhost:5555")
        self.clientID = None

    def connect(self):
        self.clientID = input("Enter your ID: ").strip()
        # Fix: Remove space after REGISTER:
        self.dealer.send_multipart([b"", f"REGISTER:{self.clientID}".encode()])  

    def receive_messages(self):
        while True:
            try:
                _, message = self.dealer.recv_multipart()
                print(f"\n[New message] {message.decode()}\nYou: ", end="", flush=True)
            except zmq.ZMQError:
                break

def main():
    client = Client()
    client.connect()

    # Start receiver thread
    threading.Thread(target=client.receive_messages, daemon=True).start()

    while True:
        recipient_id = input("Send to (ID): ").strip()
        msg = input("Message: ").strip()
        client.dealer.send_multipart([b"", f"{recipient_id}:{msg}".encode()])

if __name__ == "__main__":
    main()