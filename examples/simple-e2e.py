import base64
from datetime import datetime

from babble import Client, Identity


def create_client(seed: str) -> Client:
    delegate_identity = Identity.from_seed(f"{seed} cool")
    delegate_address = delegate_identity.address
    delegate_pubkey = delegate_identity.public_key
    delegate_pubkey_b64 = base64.b64encode(bytes.fromhex(delegate_pubkey)).decode()

    identity = Identity.from_seed(seed)
    signed_bytes, signature = delegate_identity.sign_arbitrary(
        identity.public_key.encode()
    )

    return Client(
        delegate_address, delegate_pubkey_b64, signature, signed_bytes, identity
    )


# create out clients
client1 = create_client("the wise mans fear none name the man the")
client2 = create_client("the name of the wind man fear the man the")

# print some debug
print("Client1", repr(client1))
print("Client2", repr(client2))
print()

# start sending of a message
client1.send(
    client2.delegate_address, "why hello there " + datetime.utcnow().isoformat()
)

# simulate the reading of the message
for msg in client2.receive():
    print(f"RX({client2.delegate_address}): {msg.text}")
    client2.send(client1.delegate_address, "thanks for the message: " + msg.text)

for msg in client1.receive():
    print(f"RX({client1.delegate_address}): {msg.text}")
