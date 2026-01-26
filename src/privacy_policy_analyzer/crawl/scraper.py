import gzip
import re
import ssl
import time
import zlib
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


HEADERS_EN: dict[str, str] = {
    "Accept-Language": "en-US,en;q=0.5",
}


class WebScraper:
    request_timeout: int
    playwright_timeout: int
    min_content_length: int
    playwright_wait_after_load: float

    headers: dict[str, str]
    opener: request.OpenerDirector

    def __init__(
        self,
        request_timeout: int = 10,
        playwright_timeout: int = 15000,
        min_content_length: int = 400,
        playwright_wait_after_load: float = 8.0,
    ):
        self.request_timeout = request_timeout
        self.playwright_timeout = playwright_timeout
        self.min_content_length = min_content_length
        self.playwright_wait_after_load = playwright_wait_after_load

        # Default headers to mimic a real browser
        self.headers = HEADERS
        self.headers.update(HEADERS_EN)

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
        content = soup.find(id=re.compile(r"main", re.IGNORECASE))
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

    def _scrape_playwright(self, url: str, headless: bool) -> str | None:
        """
        Scrape using Playwright (JavaScript execution).
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)

                page = browser.new_page()

                try:
                    # Navigate and wait for network to be idle
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.playwright_timeout,
                    )

                    # Additional wait for lazy-loaded content
                    if self.playwright_wait_after_load > 0:
                        time.sleep(self.playwright_wait_after_load)

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
                    browser.close()

        except Exception as e:
            logger.error("Playwright initialization failed for url=%s: %s", url, e)
            return None

    def scrape(self, url: str) -> Tag:
        # Try simple request first
        html = self._scrape_simple(url)
        logger.debug("Simple scrape returned HTML=%s for url=%s", html is not None, url)

        if html is not None:
            main_content = self.get_main_content_area(html)
            if main_content is not None:
                return main_content

            logger.debug("Main content not found in simple scrape for url=%s", url)

        # Fallback to Playwright in headless mode
        html = self._scrape_playwright(url, headless=True)
        logger.debug(
            "Playwright scrape returned HTML=%s for url=%s", html is not None, url
        )
        if html is not None:
            main_content = self.get_main_content_area(html)
            if main_content is not None:
                return main_content
            logger.debug("Main content not found in Playwright scrape for url=%s", url)

        # Final attempt with Playwright in non-headless mode
        html = self._scrape_playwright(url, headless=False)
        logger.debug(
            "Playwright (non-headless) scrape returned HTML=%s for url=%s",
            html is not None,
            url,
        )
        if html is not None:
            main_content = self.get_main_content_area(html)
            if main_content is not None:
                return main_content

            logger.debug(
                "Main content not found in Playwright (non-headless) scrape for url=%s",
                url,
            )

        logger.error("Failed to scrape content from url=%s", url)
        if html is None:
            raise NoHTML()

        raise NoMainContent()
