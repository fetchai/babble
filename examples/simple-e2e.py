import hashlib
from datetime import datetime

from babble import Client, Identity


def create_client(seed: str) -> Client:
    from babble.crypto.identity import _to_bech32

    agent_key = hashlib.sha3_384(seed.encode() + b'an-agent-address').digest()[:33]
    delegate_address = _to_bech32('agent', agent_key)

    identity = Identity.from_seed(seed)

    return Client(delegate_address, identity)


# create out clients
client1 = create_client('the wise mans fear')
client2 = create_client('the name of the wind')

# print some debug
print('Client1', repr(client1))
print('Client2', repr(client2))
print()

# start sending of a message
client1.send(client2.delegate_address, 'why hello there ' + datetime.utcnow().isoformat())

# simulate the reading of the message
for msg in client2.receive():
    print(f'RX({client2.delegate_address}): {msg.text}')
    client2.send(client1.delegate_address, 'thanks for the message: ' + msg.text)

for msg in client1.receive():
    print(f'RX({client1.delegate_address}): {msg.text}')

