"""Capture screenshots and a short GIF from the live FastAPI browser demo.

Start the API with a freshly trained model, then run:
    uv run --extra demo-capture python scripts/capture_demo.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.output_dir / "demo_input.png"
    result_path = args.output_dir / "demo_prediction.png"
    gif_path = args.output_dir / "demo_prediction.gif"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 1100},
            device_scale_factor=1,
        )
        page.goto(f"{args.base_url.rstrip('/')}/demo", wait_until="networkidle")

        try:
            page.wait_for_function(
                "() => document.querySelector('#api-status')?.classList.contains('ok')",
                timeout=10_000,
            )
        except PlaywrightTimeoutError as exc:
            browser.close()
            raise SystemExit(
                "The API/model is not healthy. Train the model and verify GET /health first."
            ) from exc

        page.screenshot(path=str(input_path), full_page=True)
        page.locator("#submit-button").click()

        try:
            page.locator("#result.visible").wait_for(timeout=20_000)
        except PlaywrightTimeoutError as exc:
            error = page.locator("#request-error").inner_text()
            browser.close()
            raise SystemExit(
                f"The live prediction failed; no result image was saved. {error}"
            ) from exc

        prediction = page.locator("#prediction-class").inner_text()
        probability = page.locator("#probability").inner_text()
        if not prediction or probability == "—":
            browser.close()
            raise SystemExit("No prediction was returned by the live API.")

        page.screenshot(path=str(result_path), full_page=True)
        browser.close()

    before = Image.open(input_path).convert("RGB")
    after = Image.open(result_path).convert("RGB")
    if before.size != after.size:
        after = after.resize(before.size)

    frames = [before.copy(), before.copy()]
    frames.extend(Image.blend(before, after, step / 8) for step in range(1, 9))
    frames.extend([after.copy(), after.copy()])
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=[650, 250] + [90] * 8 + [650, 650],
        loop=0,
        optimize=True,
    )

    print(f"Saved {input_path}, {result_path}, and {gif_path}")
    print(f"Live API result: {prediction}; churn probability: {probability}")


if __name__ == "__main__":
    main()
