from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


SEARCH_URL = "https://emma.msrb.org/Search/Search.aspx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover EMMA selectors")
    parser.add_argument("--save-html", action="store_true")
    parser.add_argument("--out", default="./output/discovery")
    parser.add_argument("--visible", action="store_true")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not args.visible)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(SEARCH_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        rows = ["id,name,type,text"]
        elements = page.locator("input, select, button, a")
        count = await elements.count()
        for idx in range(count):
            el = elements.nth(idx)
            id_attr = (await el.get_attribute("id") or "").replace(",", " ")
            name_attr = (await el.get_attribute("name") or "").replace(",", " ")
            type_attr = (await el.get_attribute("type") or "").replace(",", " ")
            text = (await el.inner_text() if await el.is_visible() else "").strip().replace(",", " ")
            rows.append(f"{id_attr},{name_attr},{type_attr},{text[:80]}")
        (out_dir / "search_elements.csv").write_text("\n".join(rows), encoding="utf-8")

        if args.save_html:
            html = await page.content()
            (out_dir / "search_page.html").write_text(html, encoding="utf-8")

        await browser.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
