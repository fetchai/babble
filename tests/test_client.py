import base64

import pytest
from babble import Client, Identity
from babble.config import MAINNET_CHAIN_ID, TESTNET_CHAIN_ID


def create_client(seed: str, chain_id: str) -> Client:
    delegate_identity = Identity.from_seed(f"{seed}")
    delegate_address = delegate_identity.address
    delegate_pubkey = delegate_identity.public_key
    delegate_pubkey_b64 = base64.b64encode(bytes.fromhex(delegate_pubkey)).decode()

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


def test_create_client_main():
    client = create_client("the wise mans fear none name", MAINNET_CHAIN_ID)
    assert client


def test_create_client_test():
    client = create_client("the name of the wind man fear", TESTNET_CHAIN_ID)
    assert client


def test_message_handling():
    # create identities
    user1 = Identity.from_seed("the wise mans fear")
    user2 = Identity.from_seed("the name of the wind")

    msg1 = b"All the truth in the world is held in stories."
    msg2 = b"Caution suits an arcanist. Assurance suits a namer. Fear does not suit either. It does not suit you"

    data = Identity.encrypt_message(user2.public_key, msg1)
    recovered = user2.decrypt_message(data)
    assert recovered == msg1

    # ensure user1 can't decrypt their own message
    with pytest.raises(ValueError):
        user1.decrypt_message(data)

    data = Identity.encrypt_message(user1.public_key, msg2)
    recovered = user1.decrypt_message(data)
    assert recovered == msg2

    # ensure user2 can't decrypt their own message
    with pytest.raises(ValueError):
        user2.decrypt_message(data)
