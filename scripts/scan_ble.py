import asyncio
from bleak import BleakScanner

def callback(device, adv):
    if device.name and "AQI" in device.name:
        print(f"Name: {device.name}, Address: {device.address}")
        print(f"Services: {adv.service_uuids}")
        print(f"Manuf data: {adv.manufacturer_data}")

async def main():
    scanner = BleakScanner(callback)
    await scanner.start()
    await asyncio.sleep(5.0)
    await scanner.stop()

asyncio.run(main())
