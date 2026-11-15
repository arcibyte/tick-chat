import asyncio


async def background_supervisor():
    while True:
        await asyncio.sleep(3600)
