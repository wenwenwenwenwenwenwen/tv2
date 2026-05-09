#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
360 Quake search crawler.

This tool always fetches search results from the live Quake API:
    POST https://quake.360.net/api/search/query_string/quake_service

The Cookie captured from the browser is hardcoded below. The capture file is
optional and is used only to reuse other request headers/body fields. It is
never used as the result source.

Output format:
    ip:port<TAB>city
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import socket
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Any
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


API_URL = "https://quake.360.net/api/search/query_string/quake_service"
TVLIST_UPLOAD_URL = "http://api.ximiba.cn/proxy/iptv/uploadTvlist.php"
DEFAULT_QUERY = 'body:"http://www.slys99.com"'
HARDCODED_AUTHORIZATION = "233"
HARDCODED_COOKIE = (
    "cert_common=9e56a54c-ab45-40d3-bb87-ff03fd949e81; "
    "Qs_lvt_357693=1744888696%2C1744969268%2C1749459574%2C1778311264; "
    "__guid=73887506.3542549961087167500.1778311278556.5703; "
    "__quc_silent__=1; "
    "Q=u%3D360H2931642336%26n%3D%26le%3D%26m%3DZGt3WGWOWGWOWGWOWGWOWGWOAGZ3%26qid%3D2931642336%26im%3D1_t011655040b3ed000bf%26src%3Dpcw_quake%26t%3D1; "
    "__NS_Q=u%3D360H2931642336%26n%3D%26le%3D%26m%3DZGt3WGWOWGWOWGWOWGWOWGWOAGZ3%26qid%3D2931642336%26im%3D1_t011655040b3ed000bf%26src%3Dpcw_quake%26t%3D1; "
    "T=s%3Db83769237d3ff73b0c889bf57699b12f%26t%3D1778311396%26lm%3D0-1%26lf%3D2%26sk%3Dbce334b7c0083ba05b6cbc12b4cd85d9%26mt%3D1778311396%26rc%3D%26v%3D2.0%26a%3D1; "
    "__NS_T=s%3Db83769237d3ff73b0c889bf57699b12f%26t%3D1778311396%26lm%3D0-1%26lf%3D2%26sk%3Dbce334b7c0083ba05b6cbc12b4cd85d9%26mt%3D1778311396%26rc%3D%26v%3D2.0%26a%3D1; "
    "Qs_pv_357693=597084160631076400%2C2307276960280465400%2C365256175586685700%2C809127707400654200%2C4108715305003766300"
)


@dataclass(frozen=True)
class Target:
    ip: str
    port: int
    city: str

    @property
    def key(self) -> tuple[str, int]:
        return self.ip, self.port


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def default_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://quake.360.net",
        "Referer": "https://quake.360.net/quake/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36"
        ),
        "Authorization": HARDCODED_AUTHORIZATION,
        "Cookie": HARDCODED_COOKIE,
    }
    authorization = os.getenv("QUAKE_AUTHORIZATION")
    cookie = os.getenv("QUAKE_COOKIE")
    if authorization:
        headers["Authorization"] = authorization
    if cookie:
        headers["Cookie"] = cookie
    return headers


def default_body(query: str, page_size: int) -> dict[str, Any]:
    return {
        "latest": True,
        "ignore_cache": False,
        "shortcuts": [],
        "query": query,
        "start": 0,
        "size": page_size,
        "device": {
            "device_type": "PC",
            "os": "Windows",
            "os_version": "10.0",
            "language": "zh_CN",
            "network": "4g",
            "browser_info": "Chrome",
            "fingerprint": "82435bf0",
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
        },
    }


def parse_capture_request(capture_path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    """
    Parse request headers and request JSON from a raw HTTP capture.

    Important: this function intentionally ignores the response body in the
    capture. Search results must come from the live API request.
    """
    text = read_text_auto(capture_path)
    response_index = text.find("\nHTTP/1.1 ")
    request_part = text[:response_index] if response_index >= 0 else text

    headers: dict[str, str] = {}
    for line in request_part.splitlines()[1:]:
        if not line.strip():
            break
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        name = name.strip()
        value = value.strip()
        if name.lower() in {
            "host",
            "connection",
            "content-length",
            "accept-encoding",
            "sec-fetch-site",
            "sec-fetch-mode",
            "sec-fetch-dest",
        }:
            continue
        headers[name] = value

    body = None
    for match in re.finditer(r"(?m)^\s*(\{.*\})\s*$", request_part):
        candidate = match.group(1)
        if '"query"' not in candidate:
            continue
        try:
            body = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue

    if body is None:
        raise ValueError(f"Could not parse request JSON from capture: {capture_path}")

    merged_headers = default_headers()
    merged_headers.update(headers)
    return merged_headers, body


def load_request_template(args: argparse.Namespace) -> tuple[dict[str, str], dict[str, Any]]:
    if args.capture:
        headers, body = parse_capture_request(Path(args.capture).expanduser())
    else:
        headers = default_headers()
        body = default_body(args.query or DEFAULT_QUERY, args.page_size)

    if args.authorization:
        headers["Authorization"] = args.authorization
    if args.cookie:
        headers["Cookie"] = args.cookie
    if args.query:
        body["query"] = args.query

    body.setdefault("latest", True)
    body.setdefault("ignore_cache", False)
    body.setdefault("shortcuts", [])
    body["size"] = args.page_size
    return headers, body


def quake_query(headers: dict[str, str], body: dict[str, Any], timeout: float) -> dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    print(f"[api] POST {API_URL} start={body.get('start')} size={body.get('size')}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read()
            return json.loads(raw.decode(charset, errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Quake API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Quake API request failed: {exc}") from exc


def extract_targets(payload: dict[str, Any]) -> list[Target]:
    rows = payload.get("data") or []
    targets: list[Target] = []

    for row in rows:
        service = row.get("service") or {}
        http_service = service.get("http") or {}
        ip = normalize_host(http_service.get("host") or "")
        port = row.get("port")
        if not ip or port is None:
            continue
        try:
            port_int = int(port)
        except (TypeError, ValueError):
            continue

        location = row.get("location") or {}
        city = (
            location.get("city_cn")
            or location.get("city_en")
            or location.get("province_cn")
            or location.get("province_en")
            or location.get("country_cn")
            or location.get("country_en")
            or "-"
        )
        targets.append(
            Target(
                ip=ip,
                port=port_int,
                city=str(city).strip() or "-",
            )
        )

    return targets


def normalize_host(value: Any) -> str:
    host = str(value or "").strip()
    if "://" in host:
        host = urlparse(host).hostname or ""
    if "/" in host:
        host = host.split("/", 1)[0]
    if ":" in host:
        maybe_host, maybe_port = host.rsplit(":", 1)
        if maybe_port.isdigit():
            host = maybe_host
    return host.strip().strip(".").lower()


def merge_target(existing: Target, incoming: Target) -> Target:
    city = existing.city if existing.city != "-" else incoming.city
    return Target(ip=existing.ip, port=existing.port, city=city)


def get_pagination(payload: dict[str, Any]) -> dict[str, int]:
    pagination = ((payload.get("meta") or {}).get("pagination") or {})

    def to_int(name: str, default: int) -> int:
        try:
            return int(pagination.get(name, default))
        except (TypeError, ValueError):
            return default

    return {
        "count": to_int("count", 0),
        "page_index": to_int("page_index", 1),
        "page_size": to_int("page_size", 0),
        "total": to_int("total", 0),
    }


def fetch_targets(
    headers: dict[str, str],
    base_body: dict[str, Any],
    pages: int,
    page_size: int,
    request_timeout: float,
    delay: float,
) -> list[Target]:
    unique: dict[tuple[str, int], Target] = {}
    page_index = 0
    total_pages: int | None = pages if pages > 0 else None

    while total_pages is None or page_index < total_pages:
        body = dict(base_body)
        body["start"] = page_index * page_size
        body["size"] = page_size

        payload = quake_query(headers, body, request_timeout)
        if payload.get("code") != 0:
            raise RuntimeError(f"Quake API error: {payload.get('message') or payload}")

        batch = extract_targets(payload)
        pagination = get_pagination(payload)
        if total_pages is None:
            total = pagination["total"]
            actual_page_size = pagination["page_size"] or page_size
            total_pages = max(1, ceil(total / actual_page_size)) if total > 0 else 1
            print(f"[page] total={total} page_size={actual_page_size} total_pages={total_pages}")

        current_page = pagination["page_index"] or page_index + 1
        print(f"[fetch] page={current_page}/{total_pages} got={len(batch)}")
        for target in batch:
            if target.key in unique:
                unique[target.key] = merge_target(unique[target.key], target)
            else:
                unique[target.key] = target

        page_index += 1
        if not batch or len(batch) < page_size:
            break
        if delay > 0 and page_index < total_pages:
            time.sleep(delay)

    return list(unique.values())


def is_port_open(target: Target, timeout: float) -> bool:
    try:
        with socket.create_connection((target.ip, target.port), timeout=timeout):
            return True
    except OSError:
        return False


def filter_available(targets: list[Target], timeout: float, workers: int) -> list[Target]:
    if not targets:
        return []

    available: list[Target] = []
    max_workers = max(1, min(workers, len(targets)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(is_port_open, target, timeout): target for target in targets}
        for future in concurrent.futures.as_completed(future_map):
            target = future_map[future]
            ok = future.result()
            print(f"[check] {target.ip}:{target.port} city={target.city} {'OK' if ok else 'FAIL'}")
            if ok:
                available.append(target)

    available.sort(key=lambda item: (item.city, item.ip, item.port))
    return available


def write_output(path: Path, targets: list[Target]) -> None:
    lines = [f"{target.ip}:{target.port}\t{target.city}" for target in targets]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def upload_tvlist(file_path: Path) -> None:
    try:
        import requests

        with file_path.open("rb") as file_obj:
            files = {"fileToUpload": (file_path.name, file_obj)}
            response = requests.post(TVLIST_UPLOAD_URL, files=files, timeout=(5, 5))
        if response.status_code == 200:
            print("[upload] File uploaded successfully.")
        else:
            print(f"[upload] Error uploading file: {response.text}")
    except Exception as exc:
        print(f"[upload] 上传tvlist失败: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Quake API results and test ip:port availability.")
    parser.add_argument("--capture", help="Optional HTTP capture txt. Only request headers/body are reused.")
    parser.add_argument("--authorization", help="Override Authorization header. Also supports QUAKE_AUTHORIZATION env.")
    parser.add_argument("--cookie", help="Override Cookie header. Also supports QUAKE_COOKIE env.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Quake query string.")
    parser.add_argument("--pages", type=int, default=0, help="Max pages to fetch. 0 means auto fetch all pages by response total.")
    parser.add_argument("--page-size", type=int, default=10, help="Result count per page.")
    parser.add_argument("--request-timeout", type=float, default=15.0, help="Quake API request timeout seconds.")
    parser.add_argument("--check-timeout", type=float, default=10.0, help="TCP availability timeout seconds.")
    parser.add_argument("--workers", type=int, default=20, help="Concurrent TCP check workers.")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between API pages.")
    parser.add_argument("--output", default="available_ip_ports.txt", help="Output txt path.")
    parser.add_argument("--no-check", action="store_true", help="Write all fetched ip:port rows without TCP checking.")
    parser.add_argument("--no-upload", action="store_true", help="Do not upload the generated txt after writing it.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.pages < 0:
        raise SystemExit("--pages must be >= 0")
    if args.page_size < 1:
        raise SystemExit("--page-size must be >= 1")

    headers, request_body = load_request_template(args)
    targets = fetch_targets(
        headers=headers,
        base_body=request_body,
        pages=args.pages,
        page_size=args.page_size,
        request_timeout=args.request_timeout,
        delay=args.delay,
    )

    print(f"[target] unique={len(targets)}")
    result = targets if args.no_check else filter_available(targets, args.check_timeout, args.workers)

    output_path = Path(args.output).expanduser()
    write_output(output_path, result)
    print(f"[done] rows={len(result)} output={output_path.resolve()}")
    if not args.no_upload:
        upload_tvlist(output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
