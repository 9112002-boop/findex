import asyncio
import random
import logging
import json
import time
from urllib.parse import urlparse, urlunparse, urljoin
from urllib.robotparser import RobotFileParser
import httpx
from selectolax.lexbor import LexborHTMLParser

# Налаштування логування у файл
logger = logging.getLogger("findex.crawler")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler("crawl.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RobotsCache:
    def __init__(self) -> None:
        self.cache: dict[str, RobotFileParser | None] = {}
        self.lock = asyncio.Lock()

    async def is_allowed(self, client: httpx.AsyncClient, url: str) -> bool:
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"

        async with self.lock:
            if host not in self.cache:
                try:
                    resp = await client.get(f"{host}/robots.txt", timeout=5.0)
                    if resp.status_code == 200:
                        rp = RobotFileParser()
                        rp.parse(resp.text.splitlines())
                        self.cache[host] = rp
                    else:
                        self.cache[host] = None
                except Exception:
                    self.cache[host] = None

        rp = self.cache[host]
        if rp is None:
            return True
        return rp.can_fetch("FindexBot/1.0 (+http://example.com/bot)", url)


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    scheme = parsed.scheme.lower()
    path = parsed.path
    # Видаляємо фрагмент (#)
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))


def is_html_url(url: str) -> bool:
    """Перевіряє, чи URL веде на HTML-сторінку, а не на файл."""
    path = urlparse(url).path.lower()
    # Ігноруємо файли з розширеннями
    ignore_exts = ('.pdf', '.zip', '.tar.gz', '.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.txt')
    return not path.endswith(ignore_exts)


async def fetch_with_retry(client: httpx.AsyncClient, url: str, max_retries: int = 3) -> httpx.Response | None:
    for attempt in range(max_retries):
        try:
            async with asyncio.timeout(10.0):
                resp = await client.get(url)

            # Якщо це 404 або інший 4xx (крім 429), ми НЕ повторюємо
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                logger.error(f"Client error {resp.status_code} for {url}. Skipping retries.")
                return None

            # Обробка Retry-After для 429 або 5xx
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    await asyncio.sleep(float(retry_after))
                else:
                    raise httpx.HTTPStatusError(f"Status {resp.status_code}", request=resp.request, response=resp)
            else:
                resp.raise_for_status()
                return resp

        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed {url} after {max_retries} attempts: {e}")
                return None
            delay = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Retrying {url} in {delay:.2f}s due to {e}")
            await asyncio.sleep(delay)
    return None


async def crawl(start_url: str, max_pages: int, concurrency: int, output_file: str) -> None:
    start_time = time.perf_counter()

    global_semaphore = asyncio.Semaphore(concurrency)
    host_semaphore = asyncio.Semaphore(min(concurrency, 2))

    robots_cache = RobotsCache()
    seen: set[str] = set()
    queue: asyncio.Queue[str] = asyncio.Queue()

    stats = {
        "pages": 0,
        "errors": 0,
        "bytes": 0,
        "start_time": start_time,
    }

    canonical_start = canonicalize_url(start_url)
    seen.add(canonical_start)
    await queue.put(canonical_start)

    with open(output_file, "w", encoding="utf-8") as f_out:

        async with httpx.AsyncClient(
                headers={"User-Agent": "FindexBot/1.0 (+http://example.com/bot)"},
                follow_redirects=True
        ) as client:

            async def worker() -> None:
                while True:
                    try:
                        url = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return

                    if not await robots_cache.is_allowed(client, url):
                        logger.info(f"Blocked by robots.txt: {url}")
                        queue.task_done()
                        continue

                    async with host_semaphore:
                        async with global_semaphore:
                            resp = await fetch_with_retry(client, url)

                            if resp is None:
                                stats["errors"] += 1
                                queue.task_done()
                                continue

                            stats["pages"] += 1
                            stats["bytes"] += len(resp.content)

                            try:
                                tree = LexborHTMLParser(resp.text)
                                title = tree.css_first("title").text() if tree.css_first("title") else ""
                                text = tree.body.text(separator=" ", strip=True) if tree.body else ""

                                record = {
                                    "url": url,
                                    "status": resp.status_code,
                                    "title": title,
                                    "text": text[:1000],
                                    "timestamp": time.time()
                                }
                                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                                f_out.flush()

                                if stats["pages"] < max_pages:
                                    for a in tree.css("a"):
                                        href = a.attributes.get("href")
                                        if href:
                                            abs_url = urljoin(url, href)
                                            canonical_url = canonicalize_url(abs_url)

                                            # Фільтруємо: тільки той самий хост, тільки HTML, тільки нові
                                            if urlparse(canonical_url).netloc == urlparse(start_url).netloc:
                                                if is_html_url(canonical_url) and canonical_url not in seen:
                                                    seen.add(canonical_url)
                                                    await queue.put(canonical_url)

                            except Exception as e:
                                logger.error(f"Parse error {url}: {e}")
                                stats["errors"] += 1

                    queue.task_done()

                    if stats["pages"] >= max_pages:
                        return

            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(worker()) for _ in range(concurrency)]
                for task in tasks:
                    await task

    elapsed = time.perf_counter() - start_time
    pages_per_sec = stats["pages"] / elapsed if elapsed > 0 else 0

    logger.info(
        f"Crawl finished: {stats['pages']} pages, {stats['errors']} errors, {elapsed:.2f}s, {pages_per_sec:.2f} pages/sec")