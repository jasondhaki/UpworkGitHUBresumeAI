from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_default_timeout(120000)

    page.goto("http://127.0.0.1:8000/")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="scratchpad_form.png", full_page=True)

    upwork_sample = (
        "I'm an automation specialist helping SMBs eliminate manual busywork.\n\n"
        'One client wrote, "The workflow he built runs flawlessly and saved us thousands of dollars."'
    )
    page.set_input_files("#cv_file", "scripts/fixtures_sample_cv.pdf")
    page.fill("#github_username", "torvalds")
    page.fill("#upwork_text", upwork_sample)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle", timeout=90000)

    print("URL after submit:", page.url)
    print("Body text snippet:", page.inner_text("h1"))
    page.screenshot(path="scratchpad_result.png", full_page=True)

    browser.close()
