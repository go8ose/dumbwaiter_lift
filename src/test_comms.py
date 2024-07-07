import asyncio

from dumb_waiter.comms import Comms

async def main():
    c = Comms('localhost')
    await c.connect()
    await c.send('hello', 'connected')
    await asyncio.sleep(10)
    c.stop()


asyncio.run(main())