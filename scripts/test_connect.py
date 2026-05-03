import asyncio
from bleak import BleakClient

ADDRESS = "F1E3FD35-6B27-4E97-24E2-FFF8EE7E2C90"
LIVE_UUID = "7b46a201-fd8a-4a28-8f4b-4b3e7c4f0001"

async def main():
    try:
        async with BleakClient(ADDRESS, timeout=10.0) as client:
            print("Connected!")
            for s in client.services:
                print(f"- {s.uuid}")
                for c in s.characteristics:
                    print(f"  - {c.uuid} ({','.join(c.properties)})")
            
            def callback(sender, data):
                print(f"Notification: {data.hex()}")

            await client.start_notify(LIVE_UUID, callback)
            await asyncio.sleep(5.0)
            await client.stop_notify(LIVE_UUID)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
