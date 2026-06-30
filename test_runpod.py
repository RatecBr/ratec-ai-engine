import asyncio
import httpx
import os

api_key = open(".env").read().split("RUNPOD_API_KEY=")[1].split("\n")[0].strip()
url = "https://api.runpod.ai/v2/rov7kf93n8xr1n/runsync"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
blank_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
payload = {"input": {"workflow_id": "background-remove", "input": {"image": blank_image}}}

async def test():
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(url, headers=headers, json=payload)
        print("Status Code:", r.status_code)
        print("Response:", r.text)

asyncio.run(test())
