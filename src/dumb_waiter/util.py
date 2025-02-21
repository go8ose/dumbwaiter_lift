import sys
import asyncio

async def run_later(delay, callback):
    "Coroutine to call a synchronous callback in delay seconds"
    # To run callback() later in your calling code you should use 
    # asyncio.create_task(run_later(delay=200,callback=foo))
    await asyncio.sleep(delay)
    callback()

async def ainput(string: str) -> str:
    await asyncio.to_thread(sys.stdout.write, f'{string} ')
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip('\n')