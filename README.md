# Babble

A simple python library for interacting with the Fetch.ai messaging service (called Memorandum)

## Quick Example

```python
from babble import Client

client1 = Client(...)
client2 = Client(...)

# send a message from one client to another
client1.send(client2.delegate_address, "why hello there")

# receive the messages from the other client
for msg in client2.receive():
    print(msg.text)
```

## Developing

**Install dependences**

    poetry install

**Run examples**

    poetry run ./examples/simple-e2e.py

**Run tests**

    poetry run pytest

**Run formatter**

    poetry run black .
