from aiohttp_sse_client import client as sse_client
import asyncio

async def main():
    async with sse_client.EventSource(
            'http://localhost:8080/api/v1/pools/event-stream'
    ) as event_source:
        async for event in event_source:
            print(event)

asyncio.run(main())
