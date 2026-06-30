import asyncio
import os
from playground.server import _remote_runsync

# Need to set env vars so _remote_runsync works
os.environ["RUNPOD_API_KEY"] = open(".env").read().split("RUNPOD_API_KEY=")[1].split("\n")[0].strip()
os.environ["RUNPOD_ENDPOINT_ID"] = "rov7kf93n8xr1n"

import playground.server
playground.server._runpod_key = os.environ["RUNPOD_API_KEY"]
playground.server._runpod_endpoint = os.environ["RUNPOD_ENDPOINT_ID"]

async def test():
    try:
        # Submit a small test image or just a blank 1x1 base64
        blank_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        res = await _remote_runsync("background-remove", {"image": blank_image, "node_overrides": {}})
        print("SUCCESS:", res)
    except Exception as e:
        print("ERROR:", str(e))

asyncio.run(test())
