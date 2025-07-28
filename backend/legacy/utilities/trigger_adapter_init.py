#!/usr/bin/env python3
"""Test WebSocket connection to see adapter initialization logs."""

import asyncio
import aiohttp
import json

async def test_ws():
    session = aiohttp.ClientSession()
    try:
        async with session.ws_connect('ws://localhost:5050/ws/lobby') as ws:
            print("Connected to WebSocket")
            
            # Send a message to trigger adapter handling
            await ws.send_json({
                "event": "ping",
                "data": {}
            })
            
            # Wait for response
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    print(f"Received: {data}")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"Error: {ws.exception()}")
                    break
                    
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await session.close()

asyncio.run(test_ws())