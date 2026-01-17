import asyncio
import json
import os
import signal
import sys

import aiohttp
from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "")
BROADCAST_URL = os.getenv("BROADCAST_URL", "")
SUBJECT = os.getenv("BROADCAST_SUBJECT", "todo.events")
QUEUE_GROUP = os.getenv("QUEUE_GROUP", "todo-broadcaster")
LOG_ONLY = os.getenv("LOG_ONLY", "false").lower() == "true"


def build_message(payload: dict) -> str:
    event_type = payload.get("type", "todo_event")
    todo = payload.get("todo", {})
    content = todo.get("content", "")
    done = todo.get("done")
    if event_type == "todo_created":
        return f"A todo was created: {content}"
    if event_type == "todo_updated":
        return f"Todo updated: {content} (done={done})"
    return f"Todo event: {content}"


async def main():
    if not NATS_URL:
        print("NATS_URL is not set, exiting", flush=True)
        sys.exit(1)
    if not BROADCAST_URL and not LOG_ONLY:
        print("BROADCAST_URL is not set and LOG_ONLY is false, exiting", flush=True)
        sys.exit(1)

    nc = NATS()
    await nc.connect(servers=[NATS_URL])

    session = aiohttp.ClientSession()

    async def handler(msg):
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            payload = {}

        message = build_message(payload)
        data = {"user": "bot", "message": message}

        if LOG_ONLY:
            print(f"[LOG_ONLY] {data}", flush=True)
            return

        try:
            async with session.post(BROADCAST_URL, json=data, timeout=5) as resp:
                if resp.status >= 400:
                    print(f"Broadcast failed: {resp.status}", flush=True)
        except Exception as e:
            print(f"Broadcast error: {e}", flush=True)

    await nc.subscribe(SUBJECT, queue=QUEUE_GROUP, cb=handler)

    stop_event = asyncio.Event()

    def _stop(*_):
        stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    await stop_event.wait()
    await session.close()
    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
