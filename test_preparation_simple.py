import asyncio
from playwright.async_api import async_playwright

async def test_preparation_phase():
    """Simple test to verify pieces display in preparation phase"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Enable console logs
        page = await context.new_page()
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        
        print("\n=== Opening app ===")
        await page.goto("http://localhost:5050")
        await page.wait_for_load_state('networkidle')
        
        # Take a screenshot to see what's on the page
        await page.screenshot(path="test_screenshot.png")
        print("Screenshot saved as test_screenshot.png")
        
        # Try to find any input field
        inputs = await page.query_selector_all('input')
        print(f"Found {len(inputs)} input fields")
        
        for i, input_elem in enumerate(inputs):
            placeholder = await input_elem.get_attribute('placeholder')
            print(f"Input {i}: placeholder='{placeholder}'")
        
        # Check what's on the page
        page_content = await page.content()
        if "Enter your name" in page_content:
            print("Found 'Enter your name' in page content")
        else:
            print("'Enter your name' NOT found in page content")
            # Print first 500 chars of page content
            print(f"Page content preview: {page_content[:500]}...")
        
        await asyncio.sleep(3)
        await browser.close()

asyncio.run(test_preparation_phase())