"""Tiny pub/sub so the bot can push live events to the dashboard (via SSE)."""
import asyncio

_subs: set[asyncio.Queue] = set()


def subscribe():
    q = asyncio.Queue()
    _subs.add(q)
    return q


def unsubscribe(q):
    _subs.discard(q)


def publish(event: dict):
    for q in list(_subs):
        q.put_nowait(event)