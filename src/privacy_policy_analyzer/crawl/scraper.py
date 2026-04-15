import gzip
import re
import ssl
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import StrEnum
from html import unescape
from http.cookiejar import CookieJar
from urllib import request

from bs4 import BeautifulSoup
from bs4.element import Tag
from playwright.sync_api import sync_playwright

from privacy_policy_analyzer.crawl.err import NoHTML, NoMainContent
from privacy_policy_analyzer.shared.logging import get_logger

logger = get_logger(__name__)

HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "sec-Ch-Ua": '"Chromium";v="143", "Google Chrome";v="143", ";Not A Brand";v="24"',
    "sec-Ch-Ua-Mobile": "?0",
    "sec-Ch-Ua-Platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
}


HEADERS_EN_US: dict[str, str] = {
    "Accept-Language": "en-US,en;q=0.5",
    "Cookie": "chosen_country=US;rs_geo=US;rw_locale=%2Fus%2Fen;",
}

HEADERS_EN_GB: dict[str, str] = {
    "Accept-Language": "en-GB,en;q=0.5",
    "Cookie": "chosen_country=GB;rs_geo=GB;rw_locale=%2Fgb%2Fen;",
}

HEADERS_DE: dict[str, str] = {
    "Accept-Language": "de-DE,de;q=0.5",
    "Cookie": "chosen_country=DE;rs_geo=DE;rw_locale=%2Fde%2Fde;",
}


class ScraperLang(StrEnum):
    """Enumeration of supported languages."""

    EN_US = "en-US"
    EN_GB = "en-GB"
    DE_DE = "de-DE"

    @staticmethod
    def from_str(s: str) -> "ScraperLang":
        if s.lower() == "en-US":
            return ScraperLang.EN_US
        elif s.lower() == "en-GB":
            return ScraperLang.EN_GB
        elif s.lower() == "de-DE":
            return ScraperLang.DE_DE

        assert False, f"Unsupported language: {s}"


class WebScraper:
    request_timeout: int
    playwright_timeout: int
    min_content_length: int
    playwright_wait_after_load: float
    language_setting: ScraperLang

    headers: dict[str, str]
    opener: request.OpenerDirector

    def __init__(
        self,
        language_setting: ScraperLang = ScraperLang.EN_US,
        request_timeout: int = 10,
        playwright_timeout: int = 15000,
        min_content_length: int = 400,
        playwright_wait_after_load: float = 8.0,
    ):
        self.request_timeout = request_timeout
        self.playwright_timeout = playwright_timeout
        self.min_content_length = min_content_length
        self.playwright_wait_after_load = playwright_wait_after_load

        self.language_setting = language_setting

        match language_setting:
            case ScraperLang.EN_US:
                self.headers = HEADERS.copy()
                self.headers.update(HEADERS_EN_US)
            case ScraperLang.EN_GB:
                self.headers = HEADERS.copy()
                self.headers.update(HEADERS_EN_GB)
            case ScraperLang.DE_DE:
                self.headers = HEADERS.copy()
                self.headers.update(HEADERS_DE)
            case _:
                assert False, f"Unsupported language setting: {language_setting}"

        # Create context that doesn't verify certificates
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        cookie_jar = CookieJar()

        # Create opener with cookie and SSL handling
        self.opener = request.build_opener(
            request.HTTPSHandler(context=ctx),
            request.HTTPCookieProcessor(cookie_jar),
        )

    def _is_content_sufficient(self, html: str, javascript_check: bool) -> bool:
        """
        Check if the HTML content is sufficient (not just a skeleton page).
        """
        soup = BeautifulSoup(html, "html5lib")

        # Get text content (excluding script and style tags)
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        body_text = soup.get_text(strip=False)

        # Check heuristics
        text_length_ok = len(body_text) >= self.min_content_length

        if javascript_check and "javascript" in body_text.lower():
            logger.info("Content contains 'javascript' keyword, likely JS-heavy")
            return False

        return text_length_ok

    def _html_preprocessing(self, html: str) -> str:
        html = unescape(html)
        html = html.replace("&nbsp;", " ")
        html = html.replace("\xa0", " ")

        # replace multiple spaces with single space
        html = re.sub(r"\s+", " ", html)

        # replace \n with space
        html = html.replace("\n", " ")

        return html

    def get_main_content_area(self, html: str) -> Tag | None:
        assert isinstance(html, str)

        html = self._html_preprocessing(html)
        soup = BeautifulSoup(html, "html5lib")

        for element in soup(
            [
                "script",
                "style",
                "link",
                # "header",
                "footer",
                "nav",
                "button",
                "dialog",
                "aside",
                "meta",
            ]
        ):
            element.decompose()

        min_len = self.min_content_length

        # check for <main> tag first
        content = soup.find("main")
        if content:
            logger.debug("Checking <main> as main content area")
            if len(content.get_text(strip=True)) >= min_len:
                logger.debug("Using <main> as main content area")
                return content

        # check for role="main"
        content = soup.find(attrs={"role": "main"})
        if content:
            logger.debug("Checking role='main' as main content area")
            # check if it has substantial content
            if len(content.get_text(strip=True)) >= min_len:
                logger.debug("Using role='main' as main content area")
                return content

        # check for id containing "main"
        content = soup.find(id=re.compile(r"^main$", re.IGNORECASE))
        if content:
            logger.debug("Checking id='main' as main content area")
            if len(content.get_text(strip=True)) >= min_len:
                logger.debug("Using id='main' as main content area")
                return content

        # check for <article> tag
        content = soup.find("article")
        if content:
            logger.debug("Checking <article> as main content area")
            if len(content.get_text(strip=True)) >= min_len:
                logger.debug("Using <article> as main content area")
                return content

        content = soup.find("body")
        if content:
            logger.debug("Checking <body> as main content area")
            if len(content.get_text(strip=True)) >= min_len:
                logger.debug("Using <body> as main content area")
                return content

        logger.debug("No suitable main content area found")
        return None

    def _scrape_simple(self, url: str) -> str | None:
        request_obj = request.Request(url, headers=self.headers)
        try:
            res = request.urlopen(request_obj, timeout=self.request_timeout)
        except Exception as e:
            logger.warning("Simple request failed for url=%s: %s", url, e)
            return None

        html: str
        encoding = res.headers.get("Content-Encoding", "").lower()
        data = res.read()

        # check for PDF
        if res.headers.get("Content-Type", "").lower() == "application/pdf":
            logger.warning(
                "PDF content detected, skipping HTML parsing for url=%s", url
            )
            raise ValueError("PDF content detected, skipping HTML parsing.")

        if encoding == "gzip":
            html = gzip.decompress(data).decode("utf-8", errors="ignore")
        elif encoding == "deflate":
            html = zlib.decompress(data).decode("utf-8", errors="ignore")
        else:
            html = data.decode("utf-8", errors="ignore")

        if self._is_content_sufficient(html, javascript_check=False):
            return html
        else:
            logger.debug("Insufficient content from simple request for url=%s", url)
            return None

    def _scrape_playwright(
        self,
        url: str,
        headless: bool,
        cancel_event: threading.Event | None = None,
    ) -> str | None:
        """
        Scrape using Playwright (JavaScript execution).

        Args:
            url: The URL to scrape.
            headless: Whether to run the browser in headless mode.
            cancel_event: Optional event to signal cancellation. If set, the method
                will abort early and clean up resources.
        """
        try:
            with sync_playwright() as p:
                # Check for cancellation before launching browser
                if cancel_event is not None and cancel_event.is_set():
                    logger.debug(
                        "Playwright scrape cancelled before browser launch for url=%s headless=%s",
                        url,
                        headless,
                    )
                    return None

                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(locale=self.language_setting)

                try:
                    # Check for cancellation after browser launch
                    if cancel_event is not None and cancel_event.is_set():
                        logger.debug(
                            "Playwright scrape cancelled after browser launch for url=%s headless=%s",
                            url,
                            headless,
                        )
                        return None

                    page = context.new_page()

                    try:
                        # Navigate and wait for network to be idle
                        page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=self.playwright_timeout,
                        )

                        # Check for cancellation after page load
                        if cancel_event is not None and cancel_event.is_set():
                            logger.debug(
                                "Playwright scrape cancelled after page load for url=%s headless=%s",
                                url,
                                headless,
                            )
                            return None

                        # Additional wait for lazy-loaded content with cancellation checks
                        if self.playwright_wait_after_load > 0:
                            wait_interval = 0.5  # Check every 0.5 seconds
                            elapsed = 0.0
                            while elapsed < self.playwright_wait_after_load:
                                if cancel_event is not None and cancel_event.is_set():
                                    logger.debug(
                                        "Playwright scrape cancelled during wait for url=%s headless=%s",
                                        url,
                                        headless,
                                    )
                                    return None
                                sleep_time = min(
                                    wait_interval,
                                    self.playwright_wait_after_load - elapsed,
                                )
                                time.sleep(sleep_time)
                                elapsed += sleep_time

                        # Final cancellation check before extracting content
                        if cancel_event is not None and cancel_event.is_set():
                            logger.debug(
                                "Playwright scrape cancelled before content extraction for url=%s headless=%s",
                                url,
                                headless,
                            )
                            return None

                        html = page.content()

                        # Verify we got actual content
                        if self._is_content_sufficient(html, javascript_check=False):
                            return html
                        else:
                            logger.debug(
                                "Insufficient content from Playwright for url=%s headless=%s",
                                url,
                                headless,
                            )
                            return None

                    except Exception as e:
                        logger.error("Playwright error for url=%s: %s", url, e)
                        return None
                    finally:
                        page.close()
                finally:
                    context.close()
                    browser.close()

        except Exception as e:
            logger.error("Playwright initialization failed for url=%s: %s", url, e)
            return None

    def scrape(self, url: str) -> Tag:
        # Try simple request first (fast path)
        html = self._scrape_simple(url)
        logger.debug("Simple scrape returned HTML=%s for url=%s", html is not None, url)

        if html is not None:
            main_content = self.get_main_content_area(html)
            if main_content is not None:
                return main_content
            logger.debug("Main content not found in simple scrape for url=%s", url)

        # Fallback: run both Playwright modes in parallel, use first success
        html = self._scrape_playwright_parallel(url)

        if html is not None:
            main_content = self.get_main_content_area(html)
            if main_content is not None:
                return main_content
            logger.debug("Main content not found in Playwright scrape for url=%s", url)

        logger.error("Failed to scrape content from url=%s", url)
        if html is None:
            raise NoHTML()

        raise NoMainContent()

    def _scrape_playwright_parallel(self, url: str) -> str | None:
        """
        Run headless and non-headless Playwright scraping in parallel.
        Returns the first successful result and signals cancellation to the other thread.
        """
        strategies = [
            ("headless", True),
            ("non-headless", False),
        ]

        # Shared cancellation event to signal other threads to stop
        cancel_event = threading.Event()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_mode = {
                executor.submit(
                    self._scrape_playwright, url, headless, cancel_event
                ): mode
                for mode, headless in strategies
            }

            for future in as_completed(future_to_mode):
                mode = future_to_mode[future]
                try:
                    result = future.result()
                    if result is not None:
                        logger.debug(
                            "Playwright (%s) scrape succeeded for url=%s", mode, url
                        )
                        # Signal cancellation to remaining threads
                        cancel_event.set()
                        # Cancel futures that haven't started yet
                        for f in future_to_mode:
                            f.cancel()
                        return result
                    logger.debug(
                        "Playwright (%s) scrape returned no content for url=%s",
                        mode,
                        url,
                    )
                except Exception as e:
                    logger.debug(
                        "Playwright (%s) scrape failed for url=%s: %s", mode, url, e
                    )

        return None
