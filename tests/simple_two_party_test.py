import hashlib
import pytest

from babble import Client, Identity


def create_client(seed: str) -> Client:
    from babble.crypto.identity import _to_bech32

    agent_key = hashlib.sha3_384(seed.encode() + b'an-agent-address').digest()[:33]
    delegate_address = _to_bech32('agent', agent_key)

    identity = Identity.from_seed(seed)

    return Client(delegate_address, identity)


def test_simple_interaction():
    # create out clients
    user1 = Identity.from_seed('the wise mans fear')
    user2 = Identity.from_seed('the name of the wind')

    msg1 = b'All the truth in the world is held in stories.'
    msg2 = b'Caution suits an arcanist. Assurance suits a namer. Fear does not suit either. It does not suit you'

    data = Identity.encrypt_message(user2.public_key, msg1)
    recovered = user2.decrypt_message(data)
    assert recovered == msg1

    # ensure you can't decrypt your own message
    with pytest.raises(ValueError):
        user1.decrypt_message(data)

    data = Identity.encrypt_message(user1.public_key, msg2)
    recovered = user1.decrypt_message(data)
    assert recovered == msg2

    # ensure you can't decrypt your own message
    with pytest.raises(ValueError):
        user2.decrypt_message(data)
