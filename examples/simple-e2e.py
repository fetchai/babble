import base64
from datetime import datetime, timezone

from babble import Client, Identity

MAINNET_CHAIN_ID = "fetchhub-4"
TESTNET_CHAIN_ID = "dorado-1"


def create_client(seed: str, chain_id: str = MAINNET_CHAIN_ID) -> Client:
    delegate_identity = Identity.from_seed(f"{seed}")
    delegate_address = delegate_identity.address
    delegate_pubkey = delegate_identity.public_key
    delegate_pubkey_b64 = base64.b64encode(bytes.fromhex(delegate_pubkey)).decode()

    # Important: Messaging public key to be registered should be different even though delegate address can be same.
    identity = Identity.from_seed(f"{seed} {chain_id}")
    signed_bytes, signature = delegate_identity.sign_arbitrary(
        identity.public_key.encode()
    )

    return Client(
        delegate_address,
        delegate_pubkey_b64,
        signature,
        signed_bytes,
        identity,
        chain_id,
    )


# create out clients
client1 = create_client("the wise mans fear none name")
client2 = create_client("the name of the wind man fear")

# create out clients with same seed phrase, should not be an issue
client1_dorado = create_client("the wise mans fear none name", TESTNET_CHAIN_ID)
client2_dorado = create_client("the name of the wind man fear", TESTNET_CHAIN_ID)

# print some debug
print("Client1", repr(client1))
print("Client2", repr(client2))
print()
print("Client1 Dorado", repr(client1_dorado))
print("Client2 Dorado", repr(client2_dorado))
print()

# start sending of a message
client1.send(
    client2.delegate_address,
    "why hello there " + datetime.now(timezone.utc).isoformat(),
)

# simulate the reading of the message
for msg in client2.receive():
    print(f"RX({client2.delegate_address}): {msg.text}")
    client2.send(client1.delegate_address, "thanks for the message: " + msg.text)

for msg in client1.receive():
    print(f"RX({client1.delegate_address}): {msg.text}")


client1_dorado.send(
    client2_dorado.delegate_address,
    "why hello there on dorado" + datetime.now(timezone.utc).isoformat(),
)

for msg in client2_dorado.receive():
    print(f"RX({client2_dorado.delegate_address}): {msg.text}")
    client2_dorado.send(
        client1_dorado.delegate_address, "thanks for the message on dorado: " + msg.text
    )

for msg in client1_dorado.receive():
    print(f"RX({client1_dorado.delegate_address}): {msg.text}")
