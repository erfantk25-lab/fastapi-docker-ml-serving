"""Capture genuine screenshots and a short GIF from the running FastAPI browser demo.

Start the API with a trained model first:
    uv run uvicorn churn.api:app --reload

Install the optional capture dependencies:
    python -m pip install playwright pillow
    python -m playwright install chromium

Then run from the repository root:
    python scripts/capture_demo.py

The script loads /demo, saves the real form state, submits the prefilled
fictional customer to the live /predict endpoint, waits for the actual result,
and writes docs/demo_input.png, docs/demo_prediction.png and
docs/demo_prediction.gif. It fails rather than fabricating a result if the
API is unavailable or the prediction request fails.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"
DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 1100},
            device_scale_factor=1,
        )
        page.goto(f"{BASE_URL}/demo", wait_until="networkidle")
        page.locator("#api-status").wait_for()
        if "API online" not in page.locator("#api-status").inner_text():
            raise RuntimeError("The live API/model is not healthy; no screenshots saved.")

        page.screenshot(path=str(DOCS / "demo_input.png"), full_page=True)
        page.locator("#submit-button").click()
        page.locator("#result.visible").wait_for(timeout=30000)
        page.screenshot(path=str(DOCS / "demo_prediction.png"), full_page=True)

        frames = [
            Image.open(DOCS / "demo_input.png").convert("RGB"),
            Image.open(DOCS / "demo_prediction.png").convert("RGB"),
        ]
        # GIF frames must share dimensions; full-page heights can differ slightly.
        width = min(frame.width for frame in frames)
        height = min(frame.height for frame in frames)
        frames = [frame.resize((width, height)) for frame in frames]
        frames[0].save(
            DOCS / "demo_prediction.gif",
            save_all=True,
            append_images=[frames[1]],
            duration=[1200, 1800],
            loop=0,
            optimize=True,
        )
        browser.close()
        print("Saved docs/demo_input.png, docs/demo_prediction.png and docs/demo_prediction.gif")


if __name__ == "__main__":
    main()
