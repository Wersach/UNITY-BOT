import re
import random
import logging
import requests
import base64
from config import GITHUB_TOKEN, GITHUB_MIN_STARS, GITHUB_MAX_STARS, GITHUB_MIN_YEAR

logger = logging.getLogger(__name__)

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _get(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[GitHub] Ошибка запроса {url}: {e}")
        return None


def _get_readme(owner, repo):
    data = _get(f"https://api.github.com/repos/{owner}/{repo}/readme")
    if not data:
        return ""
    try:
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _find_itch_url(readme):
    m = re.search(r"https?://[a-z0-9\-]+\.itch\.io/[^\s\)\"']+", readme, re.IGNORECASE)
    return m.group(0) if m else ""


def _find_screenshots(readme, owner, repo, max_count=5):
    found = []
    seen = set()
    skip = ["badge", "shield", "icon", "logo", "travis", "codecov", "appveyor", "workflow", "license"]

    for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+\.(?:png|jpg|jpeg|gif|webp))[^)]*\)", readme, re.IGNORECASE):
        path = m.group(1).strip()
        if not path.startswith("http"):
            path = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path.lstrip('./')}"
        if path not in seen and not any(s in path.lower() for s in skip):
            found.append(path)
            seen.add(path)
        if len(found) >= max_count:
            return found

    for m in re.finditer(r"https://(?:user-images\.githubusercontent\.com|raw\.githubusercontent\.com)/\S+", readme, re.IGNORECASE):
        url = m.group(0).rstrip(".,)\"'")
        if url not in seen and not any(s in url.lower() for s in skip):
            found.append(url)
            seen.add(url)
        if len(found) >= max_count:
            return found

    for m in re.finditer(r"https?://\S+\.(?:png|jpg|jpeg|gif|webp)", readme, re.IGNORECASE):
        url = m.group(0).rstrip(".,)\"'")
        if url not in seen and not any(s in url.lower() for s in skip):
            found.append(url)
            seen.add(url)
        if len(found) >= max_count:
            return found

    return found


def search_unity_repos():
    results = []
    page = random.randint(1, 10)

    query = (
        f"topic:unity topic:game stars:{GITHUB_MIN_STARS}..{GITHUB_MAX_STARS} "
        f"created:>{GITHUB_MIN_YEAR}-01-01 language:C#"
    )

    data = _get(
        "https://api.github.com/search/repositories",
        params={
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": 10,
            "page": page,
        },
    )

    if not data or "items" not in data:
        logger.error("[GitHub] Не удалось получить список репозиториев")
        return []

    items = data["items"]
    random.shuffle(items)

    for item in items:
        owner = item["owner"]["login"]
        repo = item["name"]
        readme = _get_readme(owner, repo)
        itch_url = _find_itch_url(readme)
        screenshots = _find_screenshots(readme, owner, repo, max_count=5)
        created = item.get("created_at", "")[:10]

        results.append({
            "url": item["html_url"],
            "repo_name": f"{owner}/{repo}",
            "description": item.get("description") or "Описание отсутствует",
            "language": item.get("language") or "C#",
            "stars": item.get("stargazers_count", 0),
            "created_at": created,
            "readme": readme,
            "itch_url": itch_url,
            "screenshots": screenshots,
        })

    logger.info(f"[GitHub] Найдено репозиториев: {len(results)} (страница {page})")
    return results
