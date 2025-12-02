# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "requests",
# ]
# ///

import asyncio

import requests


async def make_request() -> None:
    # Runs the blocking IO in a thread pool
    status_code = await asyncio.to_thread(
        lambda: requests.get("https://github.com").status_code
    )
    print(status_code)


async def main() -> None:
    while True:
        await make_request()
        await asyncio.sleep(2)


asyncio.run(main())
