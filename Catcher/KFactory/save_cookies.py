# save_cookies.py
import json, asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto("http://k.caict.ac.cn/")
        print("👉 请手动登录完毕后，回到终端按 Enter")
        await asyncio.get_event_loop().run_in_executor(None, input)

        cookies = await ctx.cookies()
        json.dump(cookies, open("cookies.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("✅ Cookie 已保存到 cookies.json")
        await browser.close()

asyncio.run(main())
