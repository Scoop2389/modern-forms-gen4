import asyncio
import aiohttp
from custom_components.modern_forms.aiomodernforms import ModernFormsDeviceAuto

async def main():
    # Replace with your fan's actual IP address
    host = "192.168.88.65" 
    
    async with aiohttp.ClientSession() as session:
        device = ModernFormsDeviceAuto(host, session=session)
        
        print(f"Connecting to fan at {host}...")
        state = await device.update()
        print(f"Detected G4: {device.is_g4()}")
        print(f"Current State: {state}")

        # 1. Test Discrete Speed (1-6)
        print("\nTesting Speed 3...")
        await device.fan(speed=3)
        
        # 2. Test Breeze ON/OFF (Separated switch logic)
        print("Testing Breeze ON...")
        await device.fan(wind=True)
        
        # 3. Test Downlight & Color Temperature
        if state.light_color_temp_kelvin is not None:
            print(f"Testing Downlight 3000K (Current: {state.light_color_temp_kelvin})...")
            await device.light(color_temp_kelvin=3000)
        
        # 4. Test Uplight
        if device.has_uplight():
            print(f"Testing Uplight ON (Current: {state.uplight_on})...")
            await device.uplight(on=True, brightness=50, color_temp_kelvin=2700)
        else:
            print("No Uplight detected.")

        print("\nTest complete. Check your fan!")

if __name__ == "__main__":
    asyncio.run(main())
