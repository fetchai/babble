import os

AUTH_SERVER = os.environ.get(
    "AUTH_SERVER", "https://auth-attila.sandbox-london-b.fetch-ai.com"
)
MEMORANDUM_SERVER = os.environ.get(
    "MEMORANDUM_SERVER",
    "https://messaging-server.sandbox-london-b.fetch-ai.com/graphql",
)
