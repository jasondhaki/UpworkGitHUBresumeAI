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
    # Skipping GitHub username this run -- torvalds's Linux-kernel repos are a known
    # mismatch for this niche (see CONTEXT.md); leaving it out keeps this test focused
    # on the actually-new code (the 5 new dimension formulas + stated_rate).
    page.fill("#upwork_text", upwork_sample)
    page.fill("#stated_rate", "95")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle", timeout=90000)

    print("URL after submit:", page.url)
    print("Body text snippet:", page.inner_text("h1"))
    page.screenshot(path="scratchpad_result.png", full_page=True)

    page.goto("http://127.0.0.1:8000/runs")
    page.wait_for_load_state("networkidle")
    print("\n--- /runs page ---")
    print(page.inner_text("body")[:500].encode("ascii", "replace").decode())
    page.screenshot(path="scratchpad_runs.png", full_page=True)

    view_links = page.locator("a", has_text="view")
    if view_links.count() > 0:
        view_links.first.click()
        page.wait_for_load_state("networkidle")
        print("\n--- clicked into a saved run ---")
        print("URL:", page.url)
        print("Body text snippet:", page.inner_text("h1"))

    browser.close()
