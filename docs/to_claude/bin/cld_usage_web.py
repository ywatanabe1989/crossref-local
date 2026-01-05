#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-04 (ywatanabe)"
# File: cld_usage_web.py
# Description: Fetch Claude subscription usage from claude.ai/settings/usage
#
# Usage:
#   python cld_usage_web.py                    # Fetch usage for account 1
#   python cld_usage_web.py --account 2        # Fetch usage for account 2
#   python cld_usage_web.py --all              # Fetch usage for all accounts
#   python cld_usage_web.py --visible          # Show browser window
#   python cld_usage_web.py --json             # Output as JSON
#
# Environment Variables:
#   ANTHROPIC_1_EMAIL, ANTHROPIC_1_PW  - Account 1 credentials
#   ANTHROPIC_2_EMAIL, ANTHROPIC_2_PW  - Account 2 credentials
#
# Requirements:
#   pip install playwright && playwright install chromium
#   pip install scitex  (for Google OAuth helper)

import argparse
import asyncio
import json
import os
import re
import sys

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed.")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Try to import scitex.browser.auth for Google OAuth
try:
    from scitex.browser.auth import GoogleAuthHelper
    HAS_SCITEX_AUTH = True
except ImportError:
    HAS_SCITEX_AUTH = False


def get_account_credentials(account_num: int = 1) -> tuple:
    """Get credentials for specified account from environment variables."""
    email = os.environ.get(f"ANTHROPIC_{account_num}_EMAIL")
    password = os.environ.get(f"ANTHROPIC_{account_num}_PW")
    return email, password


async def login_to_claude(page, email: str, password: str, timeout: int = 60000) -> bool:
    """Login to Claude using Google OAuth via scitex.browser.auth."""
    debug = bool(os.environ.get("CLD_DEBUG"))

    try:
        # Check if already on login page, if not navigate
        current_url = page.url
        if "login" not in current_url:
            await page.goto("https://claude.ai/login", wait_until="domcontentloaded", timeout=timeout)
        await page.wait_for_timeout(3000)

        if HAS_SCITEX_AUTH:
            # Use scitex.browser.auth GoogleAuthHelper
            if debug:
                print("[cld_usage_web] Using scitex.browser.auth.GoogleAuthHelper", file=sys.stderr)

            auth = GoogleAuthHelper(email=email, password=password, debug=debug)
            success = await auth.login_via_google_button(
                page,
                google_button_selector='button:has-text("Continue with Google")',
                timeout=timeout,
            )

            if success:
                # Wait for redirect back to Claude
                await page.wait_for_timeout(5000)
                current_url = page.url
                if debug:
                    print(f"[cld_usage_web] Final URL: {current_url}", file=sys.stderr)
                if "claude.ai" in current_url and "login" not in current_url:
                    if debug:
                        print("[cld_usage_web] Login successful!", file=sys.stderr)
                    return True

            if debug:
                print("[cld_usage_web] Login appears to have failed", file=sys.stderr)
            return False

        else:
            # Fallback: inline Google OAuth handling (if scitex not installed)
            if debug:
                print("[cld_usage_web] scitex.browser.auth not available, using fallback", file=sys.stderr)
            return await _fallback_google_login(page, email, password, timeout, debug)

    except Exception as e:
        if debug:
            print(f"[cld_usage_web] Login error: {e}", file=sys.stderr)
        return False


async def _fallback_google_login(page, email: str, password: str, timeout: int, debug: bool) -> bool:
    """Fallback Google OAuth login when scitex is not available."""
    try:
        # Click "Continue with Google" button
        google_btn = None
        selectors = [
            'button:has-text("Continue with Google")',
            'button:has-text("Google")',
            '[data-testid="google-login"]',
        ]
        for selector in selectors:
            try:
                google_btn = await page.query_selector(selector)
                if google_btn:
                    break
            except:
                continue

        if not google_btn:
            if debug:
                print("[fallback] Google button not found!", file=sys.stderr)
            return False

        if debug:
            print("[fallback] Found Google button, clicking...", file=sys.stderr)

        # Google OAuth opens in a popup
        async with page.context.expect_page(timeout=timeout) as popup_info:
            await google_btn.click()

        popup = await popup_info.value
        if debug:
            print(f"[fallback] Popup opened: {popup.url[:80]}...", file=sys.stderr)

        # Wait for Google login page to load
        await popup.wait_for_load_state("domcontentloaded")
        await popup.wait_for_timeout(2000)

        # Fill email
        await popup.wait_for_selector('input[type="email"]', state="visible", timeout=10000)
        if debug:
            print(f"[fallback] Filling email: {email}", file=sys.stderr)
        await popup.fill('input[type="email"]', email)
        await popup.wait_for_timeout(500)

        # Click Next
        next_btn = await popup.query_selector('#identifierNext')
        if not next_btn:
            next_btn = await popup.query_selector('button:has-text("Next")')
        if next_btn:
            await next_btn.click()
            await popup.wait_for_timeout(3000)

        # Fill password
        await popup.wait_for_selector('input[type="password"]', state="visible", timeout=15000)
        if debug:
            print("[fallback] Filling password", file=sys.stderr)
        await popup.fill('input[type="password"]', password)
        await popup.wait_for_timeout(500)

        # Click Next
        next_btn = await popup.query_selector('#passwordNext')
        if not next_btn:
            next_btn = await popup.query_selector('button:has-text("Next")')
        if next_btn:
            await next_btn.click()
            await popup.wait_for_timeout(5000)

        # Check for 2FA
        try:
            page_text = await popup.inner_text("body")
            twofa_indicators = ["2-Step Verification", "Verify it's you", "Open the Gmail app"]
            is_2fa = any(ind.lower() in page_text.lower() for ind in twofa_indicators)

            if is_2fa:
                if debug:
                    print("[fallback] 2FA detected - waiting up to 60s for approval...", file=sys.stderr)
                    await popup.screenshot(path="/tmp/google_popup_debug.png")

                # Wait for 2FA approval (check every 2s for up to 60s)
                for _ in range(30):
                    await popup.wait_for_timeout(2000)
                    try:
                        # Check if popup closed or URL changed
                        current_url = popup.url
                        if "accounts.google.com" not in current_url:
                            if debug:
                                print("[fallback] 2FA completed", file=sys.stderr)
                            break
                    except:
                        # Popup closed
                        if debug:
                            print("[fallback] 2FA completed - popup closed", file=sys.stderr)
                        break
        except:
            pass

        # Wait for popup to close
        try:
            await popup.wait_for_event("close", timeout=20000)
            if debug:
                print("[fallback] Popup closed - login successful", file=sys.stderr)
        except:
            if debug:
                print("[fallback] Popup didn't close automatically", file=sys.stderr)
                try:
                    await popup.screenshot(path="/tmp/google_popup_debug.png")
                    print("[fallback] Popup screenshot: /tmp/google_popup_debug.png", file=sys.stderr)
                except:
                    pass

        # Wait for redirect back to Claude
        await page.wait_for_timeout(5000)
        current_url = page.url
        if debug:
            print(f"[fallback] Final URL: {current_url}", file=sys.stderr)
        return "claude.ai" in current_url and "login" not in current_url

    except Exception as e:
        if debug:
            print(f"[fallback] Login error: {e}", file=sys.stderr)
        return False


async def get_usage_data(account_num: int = 1, headless: bool = True, timeout: int = 60000) -> dict:
    """
    Fetch usage data from claude.ai/settings/usage.

    Returns dict with:
        - account: Account email
        - plan_usage_percent: Current session usage percentage
        - plan_reset_time: When the plan resets
        - weekly_all_percent: Weekly all models usage percentage
        - weekly_all_reset: When weekly all models resets
        - weekly_sonnet_percent: Weekly Sonnet-only usage percentage
        - weekly_sonnet_reset: When weekly Sonnet resets
    """
    email, password = get_account_credentials(account_num)
    debug = bool(os.environ.get("CLD_DEBUG"))

    usage_data = {
        "account": email or f"Account {account_num}",
        "plan_usage_percent": None,
        "plan_reset_time": None,
        "weekly_all_percent": None,
        "weekly_all_reset": None,
        "weekly_sonnet_percent": None,
        "weekly_sonnet_reset": None,
        "error": None,
    }

    if not email or not password:
        usage_data["error"] = f"Credentials not found for account {account_num}. Set ANTHROPIC_{account_num}_EMAIL and ANTHROPIC_{account_num}_PW"
        return usage_data

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        try:
            page = await context.new_page()

            # Try to go directly to usage page
            await page.goto(
                "https://claude.ai/settings/usage",
                wait_until="domcontentloaded",
                timeout=timeout,
            )
            await page.wait_for_timeout(5000)

            # Wait for any redirects to complete
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass
            await page.wait_for_timeout(3000)

            # Check if we need to login
            current_url = page.url
            if debug:
                print(f"[cld_usage_web] Current URL: {current_url}", file=sys.stderr)

            # Check page content for login indicators
            try:
                page_content = await page.content()
                needs_login = "login" in current_url or "Continue with Google" in page_content
            except:
                needs_login = "login" in current_url

            if needs_login:
                if debug:
                    print("[cld_usage_web] Login required", file=sys.stderr)
                login_success = await login_to_claude(page, email, password, timeout)
                if not login_success:
                    usage_data["error"] = "Login failed. Please check credentials."
                    return usage_data

                # Navigate to usage page after login
                await page.goto(
                    "https://claude.ai/settings/usage",
                    wait_until="domcontentloaded",
                    timeout=timeout,
                )
                await page.wait_for_timeout(5000)

            # Verify we're on the usage page
            current_url = page.url
            if "login" in current_url or "oauth" in current_url:
                usage_data["error"] = "Session expired or login failed."
                return usage_data

            # Wait for page to stabilize
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            await page.wait_for_timeout(3000)

            # Debug: save screenshot if requested
            if debug:
                await page.screenshot(path="/tmp/claude_usage_debug.png")
                print("[cld_usage_web] Screenshot: /tmp/claude_usage_debug.png", file=sys.stderr)

            # Get body text for pattern matching
            try:
                body_text = await page.inner_text("body")
            except:
                body_text = ""

            if debug:
                print(f"[cld_usage_web] Body text:\n{body_text[:2000]}", file=sys.stderr)

            # Extract usage data using multiple strategies

            # Strategy 1: Look for progress bars with aria-valuenow
            try:
                progress_elements = await page.query_selector_all('[role="progressbar"]')
                for i, elem in enumerate(progress_elements):
                    try:
                        value = await elem.get_attribute("aria-valuenow")
                        if value:
                            percent = int(float(value))
                            if i == 0:
                                usage_data["plan_usage_percent"] = percent
                            elif i == 1:
                                usage_data["weekly_all_percent"] = percent
                            elif i == 2:
                                usage_data["weekly_sonnet_percent"] = percent
                    except:
                        pass
            except:
                pass

            # Strategy 2: Find percentage patterns in text
            percent_matches = re.findall(r'(\d+)\s*%', body_text)
            if len(percent_matches) >= 1 and usage_data["plan_usage_percent"] is None:
                usage_data["plan_usage_percent"] = int(percent_matches[0])
            if len(percent_matches) >= 2 and usage_data["weekly_all_percent"] is None:
                usage_data["weekly_all_percent"] = int(percent_matches[1])
            if len(percent_matches) >= 3 and usage_data["weekly_sonnet_percent"] is None:
                usage_data["weekly_sonnet_percent"] = int(percent_matches[2])

            # Strategy 3: Look for specific sections
            plan_match = re.search(r'Plan usage.*?(\d+)\s*%', body_text, re.IGNORECASE | re.DOTALL)
            if plan_match and usage_data["plan_usage_percent"] is None:
                usage_data["plan_usage_percent"] = int(plan_match.group(1))

            all_models_match = re.search(r'All models.*?(\d+)\s*%', body_text, re.IGNORECASE | re.DOTALL)
            if all_models_match and usage_data["weekly_all_percent"] is None:
                usage_data["weekly_all_percent"] = int(all_models_match.group(1))

            sonnet_match = re.search(r'Sonnet.*?(\d+)\s*%', body_text, re.IGNORECASE | re.DOTALL)
            if sonnet_match and usage_data["weekly_sonnet_percent"] is None:
                usage_data["weekly_sonnet_percent"] = int(sonnet_match.group(1))

            # Find reset time patterns
            reset_patterns = [
                r'resets?\s+in\s+(\d+\s*(?:hr|hour|min|minute|day|week)[s]?\s*(?:\d+\s*(?:hr|hour|min|minute)[s]?)?)',
                r'resets?\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+\d+:\d+\s*(?:AM|PM)?',
            ]

            for pattern in reset_patterns:
                matches = re.findall(pattern, body_text, re.IGNORECASE)
                for i, match in enumerate(matches[:3]):
                    if i == 0 and not usage_data["plan_reset_time"]:
                        usage_data["plan_reset_time"] = match.strip()
                    elif i == 1 and not usage_data["weekly_all_reset"]:
                        usage_data["weekly_all_reset"] = match.strip()
                    elif i == 2 and not usage_data["weekly_sonnet_reset"]:
                        usage_data["weekly_sonnet_reset"] = match.strip()

        except Exception as e:
            usage_data["error"] = str(e)

        finally:
            await browser.close()

    return usage_data


def format_output(data: dict, as_json: bool = False) -> str:
    """Format usage data for display."""
    if as_json:
        return json.dumps(data, indent=2)

    if data.get("error"):
        return f"Account: {data.get('account', 'Unknown')}\nError: {data['error']}"

    lines = []
    lines.append(f"Account: {data.get('account', 'Unknown')}")
    lines.append("=" * 40)

    # Plan usage
    if data.get("plan_usage_percent") is not None:
        bar = create_progress_bar(data["plan_usage_percent"])
        lines.append(f"Plan Usage:     {bar} {data['plan_usage_percent']}%")
        if data.get("plan_reset_time"):
            lines.append(f"                Resets: {data['plan_reset_time']}")

    lines.append("")
    lines.append("Weekly Limits:")
    lines.append("-" * 40)

    # Weekly all models
    if data.get("weekly_all_percent") is not None:
        bar = create_progress_bar(data["weekly_all_percent"])
        lines.append(f"All Models:     {bar} {data['weekly_all_percent']}%")
        if data.get("weekly_all_reset"):
            lines.append(f"                Resets: {data['weekly_all_reset']}")

    # Weekly Sonnet
    if data.get("weekly_sonnet_percent") is not None:
        bar = create_progress_bar(data["weekly_sonnet_percent"])
        lines.append(f"Sonnet Only:    {bar} {data['weekly_sonnet_percent']}%")
        if data.get("weekly_sonnet_reset"):
            lines.append(f"                Resets: {data['weekly_sonnet_reset']}")

    return "\n".join(lines)


def create_progress_bar(percent: int, width: int = 20) -> str:
    """Create ASCII progress bar."""
    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'#' * filled}{'-' * empty}]"


async def fetch_all_accounts(headless: bool, timeout: int) -> list:
    """Fetch usage for all configured accounts."""
    results = []
    for i in range(1, 10):  # Check up to 9 accounts
        email, password = get_account_credentials(i)
        if email and password:
            data = await get_usage_data(i, headless, timeout)
            results.append(data)
    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch Claude usage from web")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("--timeout", type=int, default=60000, help="Timeout in ms")
    parser.add_argument("--account", "-a", type=int, default=1, help="Account number (1, 2, ...)")
    parser.add_argument("--all", action="store_true", help="Fetch all accounts")
    args = parser.parse_args()

    try:
        if args.all:
            results = asyncio.run(fetch_all_accounts(
                headless=not args.visible,
                timeout=args.timeout,
            ))
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                for i, data in enumerate(results):
                    if i > 0:
                        print("\n" + "=" * 50 + "\n")
                    print(format_output(data))
        else:
            data = asyncio.run(get_usage_data(
                account_num=args.account,
                headless=not args.visible,
                timeout=args.timeout,
            ))
            print(format_output(data, as_json=args.json))

            if data.get("error"):
                sys.exit(1)

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# EOF
