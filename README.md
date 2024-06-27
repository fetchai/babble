[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# Babble

A simple python library for interacting with the Fetch.ai messaging service (called Memorandum)

## Quick Example

```python
from babble import Client, Identity

# create a set of agents with random identities
client1 = Client('agent1.....', Identity.generate())
client2 = Client('agent1.....', Identity.generate())

# send a message from one client to another
client1.send(client2.delegate_address, "why hello there")

# receive the messages from the other client
for msg in client2.receive():
    print(msg.text)
```

## Developing

**Install dependencies**

    poetry install

**Run examples**

    poetry run ./examples/simple-e2e.py

**Run tests**

    poetry run pytest

**Run formatter**

    poetry run ruff check --fix && ruff format
