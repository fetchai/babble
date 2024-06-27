import os

MAINNET_CHAIN_ID = "fetchhub-4"
TESTNET_CHAIN_ID = "dorado-1"

DEFAULT_REQUEST_TIMEOUT = 30
AUTH_SERVER = os.environ.get("AUTH_SERVER", "https://accounts.fetch.ai/v1")
MEMORANDUM_SERVER = os.environ.get(
    "MEMORANDUM_SERVER",
    "https://messaging.fetch-ai.network",
)
