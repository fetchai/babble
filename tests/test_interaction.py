import base64
import unittest
from datetime import datetime, timezone

from babble.client import Client
from babble.config import MAINNET_CHAIN_ID, TESTNET_CHAIN_ID
from babble.crypto.identity import Identity

CLIENT_1_SEED = "the wise mans fear none name"
CLIENT_2_SEED = "the name of the wind man fear"


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


class TestInteraction(unittest.TestCase):
    def test_simple_interaction_main(self):
        client1 = create_client(CLIENT_1_SEED, MAINNET_CHAIN_ID)
        client2 = create_client(CLIENT_2_SEED, MAINNET_CHAIN_ID)

        message = "why hello there " + datetime.now(timezone.utc).isoformat()

        client1.send(client2.delegate_address, message)

        for msg in client2.receive():
            self.assertEqual(msg.text, message)
            client2.send(client1.delegate_address, message)

        for msg in client1.receive():
            self.assertEqual(msg.text, message)

    def test_simple_interaction_test(self):
        client1_dorado = create_client(CLIENT_1_SEED, TESTNET_CHAIN_ID)
        client2_dorado = create_client(CLIENT_2_SEED, TESTNET_CHAIN_ID)

        message = "why hello there on dorado" + datetime.now(timezone.utc).isoformat()

        client1_dorado.send(client2_dorado.delegate_address, message)

        for msg in client2_dorado.receive():
            self.assertEqual(msg.text, message)
            client2_dorado.send(client1_dorado.delegate_address, message)

        for msg in client1_dorado.receive():
            self.assertEqual(msg.text, message)
