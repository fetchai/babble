import os

AUTH_SERVER = os.environ.get("AUTH_SERVER", "https://accounts.fetch.ai/v1")
MEMORANDUM_SERVER = os.environ.get(
    "MEMORANDUM_SERVER",
    "https://messaging-server.prod.fetch-ai.com/graphql",
)
