import asyncio


async def foo():
    await asyncio.sleep(1)
    return 2


async def bar():
    r = await foo()
    return r + 1
