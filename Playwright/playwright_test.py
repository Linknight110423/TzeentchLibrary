import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.wikipedia.org/")
    page.get_by_role("link", name="中文 1,482,000+ 条目").click()
    page.locator("a").filter(has_text="第51届七国集团会议").click()
    page.get_by_role("link", name="改善本条目").click()
    page.get_by_role("button", name="切换为可视化编辑器").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
