#!/usr/bin/env python3
"""Crawl HKUST(GZ) public faculty profiles by Hub and Thrust."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


BASE_URL = "https://facultyprofiles.hkust-gz.edu.cn"
PAGE_ENDPOINT = BASE_URL + "/api/itdcms-rpc/profile/page"
THRUST_ENDPOINT = BASE_URL + "/api/itdcms-rpc/profile/getOfficialThrustList"
PRIMARY_ENDPOINT = BASE_URL + "/api/itdcms-rpc/profile/primary/{person_id}"
INDEX_URL = BASE_URL + "/"

MAIN_HUB_KEYS = {"FUNCHUB", "INFOHUB", "SYSTHUB", "SOCIHUB"}

HUBS: List[Dict[str, Any]] = [
    {
        "code": "10011A10000000000H1W",
        "enName": "Function Hub",
        "enShortName": "FUNCTION",
        "key": "FUNCHUB",
        "children": [
            {"code": "10011A10000000000H1Y", "enName": "Advanced Materials", "key": "am"},
            {"code": "10011A10000000000H20", "enName": "Earth, Ocean and Atmospheric Sciences", "key": "eoas"},
            {"code": "10011A10000000000H22", "enName": "Microelectronics", "key": "micro"},
            {"code": "10011A10000000000H24", "enName": "Sustainable Energy and Environment", "key": "see"},
        ],
    },
    {
        "code": "10011A10000000000H26",
        "enName": "Information Hub",
        "enShortName": "INFORMATION",
        "key": "INFOHUB",
        "children": [
            {"code": "10011A10000000000H28", "enName": "Artificial Intelligence", "key": "Artificial-Intelligence"},
            {"code": "10011A10000000000H2A", "enName": "Computational Media and Arts", "key": "Computational-Media-and-Arts"},
            {"code": "10011A10000000000H2C", "enName": "Data Science and Analytics", "key": "Data-Science-and-Analytics"},
            {"code": "10011A10000000000H2E", "enName": "Internet of Things", "key": "Internet-of-Things"},
        ],
    },
    {
        "code": "10011A10000000000H2G",
        "enName": "Systems Hub",
        "enShortName": "SYSTEMS",
        "key": "SYSTHUB",
        "children": [
            {"code": "10011A10000000000H2I", "enName": "Bioscience and Biomedical Engineering", "key": "Bioscience-&-Biomedical-Engineering"},
            {"code": "10011A10000000000H2K", "enName": "Intelligent Transportation", "key": "Intelligent-Transportation"},
            {"code": "10011A10000000000H2M", "enName": "Robotics and Autonomous Systems", "key": "Robotics-&-Autonomous-Systems"},
            {"code": "10011A10000000000H2O", "enName": "Smart Manufacturing", "key": "Smart-Manufacturing"},
        ],
    },
    {
        "code": "10011A10000000000H2Q",
        "enName": "Society Hub",
        "enShortName": "SOCIETY",
        "key": "SOCIHUB",
        "children": [
            {"code": "10011A100000000259HQ", "enName": "Carbon Neutrality and Climate Change", "key": "Carbon-Neutrality-and-Climate-Change"},
            {"code": "10011A10000000000H2S", "enName": "Financial Technology", "key": "Financial-Technology"},
            {"code": "10011A10000000000H2U", "enName": "Innovation, Policy and Entrepreneurship", "key": "Innovation,-Policy,-and-Entrepreneurship"},
            {"code": "10011A10000000000H2Y", "enName": "Urban Governance and Design", "key": "Urban-Governance-and-Design"},
        ],
    },
    {
        "code": "10011A10000000013C52",
        "enName": "College of Education Sciences",
        "enShortName": "EDUCATION SCIENCES",
        "key": "CES",
        "children": [
            {"code": "10011A10000000023NJZ", "enName": "Pillar of General Education", "key": "Pillar-of-General-Education"},
            {"code": "10011A10000000023NKD", "enName": "Pillar of STEM Education", "key": "Pillar-of-STEM-Education"},
            {"code": "10011A10000000000H30", "enName": "Pillar of Language Education", "key": "Pillar-of-Language-Education"},
            {"code": "10011A10000000023NHU", "enName": "Pillar of Cognitive Sciences", "key": "Pillar-of-Cognitive-Sciences"},
        ],
    },
    {
        "code": "10011A10000000013C5D",
        "enName": "College of Future Technology",
        "enShortName": "FUTURE TECHNOLOGY",
        "key": "CFT",
        "children": [
            {"code": "10011A10000000013C86", "enName": "Base of Red Bird Mphil", "key": "Base-of-Red-Bird-Mphil"},
        ],
    },
    {
        "code": "10011A1000000001HVBH",
        "enName": "Ethics Education and Contemporary China Studies",
        "enShortName": "ETHICS EDUCATION AND CONTEMPORARY CHINA STUDIES",
        "key": "EECCS",
        "children": [],
    },
]


class CrawlError(RuntimeError):
    pass


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def split_terms(values: Optional[Sequence[str]]) -> List[str]:
    terms: List[str] = []
    for value in values or []:
        for part in value.split(","):
            part = part.strip()
            if part:
                terms.append(part)
    return terms


def hub_aliases(hub: Dict[str, Any]) -> List[str]:
    aliases = [hub["code"], hub["key"], hub["enName"], hub["enShortName"]]
    if hub["enName"].lower().endswith(" hub"):
        aliases.append(hub["enName"][:-4])
    return aliases


def thrust_aliases(thrust: Dict[str, Any]) -> List[str]:
    return [thrust["code"], thrust["key"], thrust["enName"], thrust["enName"].replace(" and ", " & ")]


def iter_thrusts(include_extra_units: bool = True) -> Iterable[Tuple[Dict[str, Any], Dict[str, Any]]]:
    for hub in HUBS:
        if not include_extra_units and hub["key"] not in MAIN_HUB_KEYS:
            continue
        for thrust in hub.get("children", []):
            if thrust.get("code"):
                yield hub, thrust


def resolve_hub(term: Optional[str], include_extra_units: bool = True) -> Optional[Dict[str, Any]]:
    if not term:
        return None
    target = norm(term)
    candidates = [hub for hub in HUBS if include_extra_units or hub["key"] in MAIN_HUB_KEYS]
    matches = [hub for hub in candidates if target in {norm(a) for a in hub_aliases(hub)}]
    if len(matches) == 1:
        return matches[0]
    fuzzy = [hub for hub in candidates if target and target in norm(hub["enName"])]
    if len(fuzzy) == 1:
        return fuzzy[0]
    if matches or fuzzy:
        names = ", ".join(h["enName"] for h in matches + fuzzy)
        raise CrawlError("Ambiguous hub {!r}; matches: {}".format(term, names))
    raise CrawlError("Unknown hub {!r}. Run list-thrusts to inspect supported names.".format(term))


def resolve_thrust(term: str, hub: Optional[Dict[str, Any]] = None, include_extra_units: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    target = norm(term)
    if not target:
        raise CrawlError("Empty thrust name/code.")
    pairs = list(iter_thrusts(include_extra_units=include_extra_units))
    if hub:
        pairs = [(h, t) for h, t in pairs if h["key"] == hub["key"]]
    exact = [(h, t) for h, t in pairs if target in {norm(a) for a in thrust_aliases(t)}]
    if len(exact) == 1:
        return exact[0]
    fuzzy = [(h, t) for h, t in pairs if target and target in norm(t["enName"])]
    if len(fuzzy) == 1:
        return fuzzy[0]
    matches = exact + [p for p in fuzzy if p not in exact]
    if matches:
        names = ", ".join("{} / {}".format(h["enName"], t["enName"]) for h, t in matches)
        raise CrawlError("Ambiguous thrust {!r}; matches: {}".format(term, names))
    scope = " under {}".format(hub["enName"]) if hub else ""
    raise CrawlError("Unknown thrust {!r}{}. Run list-thrusts to inspect supported names.".format(term, scope))


def parse_thrust_url(url: str, include_extra_units: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    code = (qs.get("code") or [""])[0]
    if not code:
        raise CrawlError("Thrust URL has no code= parameter: {}".format(url))
    return resolve_thrust(code, include_extra_units=include_extra_units)


def build_request_url(endpoint: str, params: Dict[str, Any]) -> str:
    clean = {key: value for key, value in params.items() if value is not None and value != ""}
    return endpoint + "?" + urllib.parse.urlencode(clean)


def get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "Codex HKUST-GZ faculty profile crawler/1.0",
            "Referer": BASE_URL + "/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise CrawlError("HTTP {} for {}: {}".format(exc.code, url, detail[:500])) from exc
    except urllib.error.URLError as exc:
        raise CrawlError("Network error for {}: {}".format(url, exc)) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise CrawlError("Invalid JSON from {}: {}".format(url, body[:300])) from exc


def get_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Codex HKUST-GZ faculty profile crawler/1.0",
            "Referer": BASE_URL + "/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise CrawlError("HTTP {} for {}: {}".format(exc.code, url, detail[:500])) from exc
    except urllib.error.URLError as exc:
        raise CrawlError("Network error for {}: {}".format(url, exc)) from exc


def ensure_success(payload: Dict[str, Any], url: str) -> Dict[str, Any]:
    if payload.get("code") not in (0, "0", None):
        raise CrawlError("API returned code {} for {}: {}".format(payload.get("code"), url, payload.get("msg") or payload))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise CrawlError("API response has no object data for {}".format(url))
    return data


def page_url(hub: Dict[str, Any], thrust: Dict[str, Any], size: int) -> str:
    return build_request_url(
        PAGE_ENDPOINT,
        {
            "current": 1,
            "size": size,
            "languageType": "en",
            "dataSourcesCodes": "OUTSIDE_NC",
            "facultyType": "GZ",
            "affiliatedUnits": hub["key"],
            "departmentPkCode": thrust["code"],
        },
    )


def official_url(hub: Dict[str, Any], thrust: Dict[str, Any]) -> str:
    return build_request_url(THRUST_ENDPOINT, {"affiliatedUnits": hub["key"], "departmentPkCode": thrust["code"]})


def profile_url(person: Dict[str, Any]) -> str:
    email = (person.get("email") or person.get("id") or "").split("@")[0] or str(person.get("id") or "")
    last = person.get("lastName") or ""
    first = (person.get("firstName") or "").replace(" ", "")
    if last or first:
        name = "{}-{}".format(last, first).strip("-")
    else:
        name = (person.get("enName") or "-").replace(" ", "")
    return BASE_URL + "/faculty-personal-page/{}/{}".format(urllib.parse.quote(name), urllib.parse.quote(email))


def first_photo(person: Dict[str, Any]) -> str:
    photos = person.get("photo") or []
    if isinstance(photos, list) and photos:
        first = photos[0] or {}
        return first.get("urlHost") or ""
    return ""


def identifiers(person: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for item in person.get("rsidentifier") or []:
        if not isinstance(item, dict):
            continue
        label = item.get("label") or item.get("id") or "identifier"
        out[str(label)] = {
            "id": str(item.get("id") or ""),
            "url": str(item.get("url") or ""),
        }
    return out


def matched_jobs(person: Dict[str, Any], thrust_code: str) -> List[Dict[str, Any]]:
    return [job for job in person.get("jobs") or [] if isinstance(job, dict) and job.get("departmentPkCode") == thrust_code]


def normalize_person(
    person: Dict[str, Any],
    hub: Dict[str, Any],
    thrust: Dict[str, Any],
    official_role: str,
    source: List[str],
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row = {
        "id": person.get("id") or "",
        "code": person.get("code") or "",
        "en_name": person.get("enName") or "",
        "zh_name": person.get("name") or "",
        "first_name": person.get("firstName") or "",
        "last_name": person.get("lastName") or "",
        "email": person.get("email") or "",
        "phone": person.get("phone") or "",
        "location": person.get("location") or "",
        "degree": person.get("degreeEnName") or person.get("degreeName") or "",
        "school": person.get("schoolName") or "",
        "end_date": person.get("endDate") or "",
        "major": person.get("majorEnName") or person.get("majorName") or "",
        "website": person.get("website") or "",
        "permalink": person.get("permaLink") or "",
        "profile_url": profile_url(person),
        "photo_url": first_photo(person),
        "selected_hub": hub["enName"],
        "selected_hub_key": hub["key"],
        "selected_thrust": thrust["enName"],
        "selected_thrust_code": thrust["code"],
        "official_role": official_role,
        "jobs": person.get("jobs") or [],
        "matched_jobs": matched_jobs(person, thrust["code"]),
        "identifiers": identifiers(person),
        "source": source,
    }
    if details is not None:
        row["details"] = details
    return row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def flatten_for_csv(row: Dict[str, Any]) -> Dict[str, Any]:
    flat_keys = [
        "id",
        "code",
        "en_name",
        "zh_name",
        "email",
        "phone",
        "location",
        "degree",
        "school",
        "end_date",
        "major",
        "website",
        "permalink",
        "profile_url",
        "photo_url",
        "selected_hub",
        "selected_hub_key",
        "selected_thrust",
        "selected_thrust_code",
        "official_role",
    ]
    out = {key: row.get(key, "") for key in flat_keys}
    out["google_scholar_id"] = (row.get("identifiers") or {}).get("GoogleScholarID", {}).get("id", "")
    out["orcid"] = (row.get("identifiers") or {}).get("ORCID", {}).get("id", "")
    out["scopus_id"] = (row.get("identifiers") or {}).get("ScopusID", {}).get("id", "")
    out["matched_job_titles"] = "; ".join(job.get("jobEnName") or "" for job in row.get("matched_jobs") or [])
    out["source"] = json.dumps(row.get("source") or [], ensure_ascii=False)
    return out


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flat_rows = [flatten_for_csv(row) for row in rows]
    fieldnames = list(flat_rows[0].keys()) if flat_rows else [
        "id",
        "en_name",
        "email",
        "selected_hub",
        "selected_thrust",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)


def fetch_page_people(hub: Dict[str, Any], thrust: Dict[str, Any], size: int, timeout: int) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    url = page_url(hub, thrust, size=size)
    payload = get_json(url, timeout=timeout)
    data = ensure_success(payload, url)
    people = data.get("list") or []
    if not isinstance(people, list):
        people = []
    return url, payload, people


def fetch_official_people(hub: Dict[str, Any], thrust: Dict[str, Any], timeout: int) -> Tuple[str, Dict[str, Any], List[Tuple[str, Dict[str, Any]]]]:
    url = official_url(hub, thrust)
    payload = get_json(url, timeout=timeout)
    data = ensure_success(payload, url)
    rows: List[Tuple[str, Dict[str, Any]]] = []
    acting_head = data.get("ACTING_HEAD")
    if isinstance(acting_head, dict) and (acting_head.get("id") or acting_head.get("enName")):
        rows.append(("ACTING_HEAD", acting_head))
    advisors = data.get("CURRENT_FACULTY_ADVISORS") or []
    if isinstance(advisors, list):
        rows.extend(("CURRENT_FACULTY_ADVISOR", item) for item in advisors if isinstance(item, dict))
    return url, payload, rows


def fetch_details(person_id: str, timeout: int) -> Optional[Dict[str, Any]]:
    if not person_id:
        return None
    url = PRIMARY_ENDPOINT.format(person_id=urllib.parse.quote(str(person_id)))
    payload = get_json(url, timeout=timeout)
    return ensure_success(payload, url)


def merge_person(base: Dict[str, Any], enrichment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not enrichment:
        return dict(base)
    merged = dict(enrichment)
    for key, value in base.items():
        if value not in (None, "", [], {}):
            merged[key] = value
    if not merged.get("rsidentifier") and enrichment.get("rsidentifier"):
        merged["rsidentifier"] = enrichment.get("rsidentifier")
    return merged


def dedupe_rows(rows: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    if mode == "none":
        return rows
    seen: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("id") or row.get("email") or row.get("en_name"))
        if not key:
            continue
        if key not in seen:
            row = dict(row)
            row["selected_thrusts"] = [row.get("selected_thrust")]
            seen[key] = row
        else:
            existing = seen[key]
            thrust = row.get("selected_thrust")
            if thrust and thrust not in existing.setdefault("selected_thrusts", []):
                existing["selected_thrusts"].append(thrust)
            existing["selected_thrust"] = "; ".join(existing.get("selected_thrusts") or [])
    return list(seen.values())


def selected_pairs(args: argparse.Namespace) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    include_extra = bool(args.include_extra_units)
    hub = resolve_hub(args.hub, include_extra_units=include_extra) if args.hub else None
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for url in args.thrust_url or []:
        pairs.append(parse_thrust_url(url, include_extra_units=include_extra))
    for term in split_terms(args.thrust):
        pairs.append(resolve_thrust(term, hub=hub, include_extra_units=include_extra))
    if args.all_thrusts:
        if not hub:
            raise CrawlError("--all-thrusts requires --hub.")
        pairs.extend((hub, thrust) for thrust in hub.get("children", []) if thrust.get("code"))
    if hub and not pairs:
        pairs.extend((hub, thrust) for thrust in hub.get("children", []) if thrust.get("code"))
    if not pairs:
        raise CrawlError("Specify --hub, --thrust, --thrust-url, or --all-thrusts.")
    unique: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    seen = set()
    for h, t in pairs:
        key = (h["key"], t["code"])
        if key not in seen:
            seen.add(key)
            unique.append((h, t))
    return unique


def cmd_list_thrusts(args: argparse.Namespace) -> int:
    hub = resolve_hub(args.hub, include_extra_units=args.include_extra_units) if args.hub else None
    hubs = [hub] if hub else [h for h in HUBS if args.include_extra_units or h["key"] in MAIN_HUB_KEYS]
    if args.json:
        print(json.dumps(hubs, ensure_ascii=False, indent=2))
        return 0
    for item in hubs:
        print("{} ({})".format(item["enName"], item["key"]))
        for thrust in item.get("children", []):
            print("  - {} | {} | {}".format(thrust["enName"], thrust["key"], thrust["code"]))
    return 0


def extract_hub_map_from_frontend(timeout: int = 30) -> Dict[str, Any]:
    index_html = get_text(INDEX_URL, timeout=timeout)
    scripts = re.findall(r'<script[^>]+src="([^"]+\.js)"', index_html)
    chunk_urls = [urllib.parse.urljoin(BASE_URL, src) for src in scripts if "chunk-52beea30" in src]
    if not chunk_urls:
        prefetches = re.findall(r'href="([^"]*chunk-52beea30[^"]+\.js)"', index_html)
        chunk_urls = [urllib.parse.urljoin(BASE_URL, src) for src in prefetches]
    if not chunk_urls:
        raise CrawlError("Cannot find the frontend chunk that contains the Hub/Thrust map.")

    js_url = chunk_urls[0]
    js_text = get_text(js_url, timeout=timeout)
    pairs: List[Dict[str, str]] = []
    for match in re.finditer(r'\{code:"([^"]+)",name:"[^"]*",enName:"([^"]+)",key:"([^"]+)"(?:,icon:"([^"]*)")?\}', js_text):
        code, en_name, key, icon = match.groups()
        if not code or key == "all":
            continue
        pairs.append({"code": code, "enName": en_name, "key": key, "icon": icon or ""})

    embedded = {thrust["code"]: {"hub": hub["enName"], "thrust": thrust["enName"]} for hub, thrust in iter_thrusts(include_extra_units=True)}
    discovered = {item["code"]: item for item in pairs}
    missing = sorted(set(embedded) - set(discovered))
    added = sorted(set(discovered) - set(embedded))
    return {
        "source_url": js_url,
        "discovered_count": len(pairs),
        "discovered_thrusts": pairs,
        "embedded_count": len(embedded),
        "missing_from_frontend": missing,
        "added_in_frontend": added,
    }


def cmd_discover_map(args: argparse.Namespace) -> int:
    result = extract_hub_map_from_frontend(timeout=args.timeout)
    if args.output:
        write_json(Path(args.output), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_crawl(args: argparse.Namespace) -> int:
    pairs = selected_pairs(args)
    if args.dry_run:
        payload = [
            {
                "hub": hub["enName"],
                "hub_key": hub["key"],
                "thrust": thrust["enName"],
                "thrust_code": thrust["code"],
                "page_url": page_url(hub, thrust, args.page_size),
                "official_url": official_url(hub, thrust),
            }
            for hub, thrust in pairs
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    out_dir = Path(args.output_dir)
    raw_dir = out_dir / "raw"
    rows: List[Dict[str, Any]] = []
    manifest: Dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "source": args.source,
        "include_details": bool(args.include_details),
        "selections": [],
    }

    for hub, thrust in pairs:
        slug = "{}_{}".format(norm(hub["key"]), norm(thrust["key"] or thrust["enName"]))
        selection_meta: Dict[str, Any] = {
            "hub": hub["enName"],
            "hub_key": hub["key"],
            "thrust": thrust["enName"],
            "thrust_code": thrust["code"],
            "counts": {},
            "urls": {},
        }

        page_people: List[Dict[str, Any]] = []
        page_by_id: Dict[str, Dict[str, Any]] = {}
        if args.source in ("page", "both"):
            url, payload, page_people = fetch_page_people(hub, thrust, args.page_size, args.timeout)
            write_json(raw_dir / "{}_page.json".format(slug), payload)
            selection_meta["urls"]["page"] = url
            selection_meta["counts"]["page"] = len(page_people)
            page_by_id = {str(person.get("id")): person for person in page_people if person.get("id")}
            if args.sleep:
                time.sleep(args.sleep)

        official_people: List[Tuple[str, Dict[str, Any]]] = []
        if args.source in ("official", "both"):
            url, payload, official_people = fetch_official_people(hub, thrust, args.timeout)
            write_json(raw_dir / "{}_official.json".format(slug), payload)
            selection_meta["urls"]["official"] = url
            selection_meta["counts"]["official"] = len(official_people)
            if args.sleep:
                time.sleep(args.sleep)

        source_rows: List[Tuple[str, Dict[str, Any], List[str]]]
        if args.source == "page":
            source_rows = [("PAGE_RESULT", person, ["page"]) for person in page_people]
        elif args.source == "official":
            source_rows = [(role, person, ["official"]) for role, person in official_people]
        else:
            source_rows = [(role, person, ["official", "page"]) for role, person in official_people]
            if not source_rows:
                source_rows = [("PAGE_RESULT", person, ["page"]) for person in page_people]

        if args.max_people is not None:
            source_rows = source_rows[: args.max_people]

        for role, person, source in source_rows:
            merged = merge_person(person, page_by_id.get(str(person.get("id"))))
            details = None
            if args.include_details:
                details = fetch_details(str(merged.get("id") or ""), args.timeout)
                if args.sleep:
                    time.sleep(args.sleep)
            rows.append(normalize_person(merged, hub, thrust, role, source, details=details))

        selection_meta["counts"]["normalized_rows"] = len(source_rows)
        manifest["selections"].append(selection_meta)

    rows = dedupe_rows(rows, args.dedupe)
    manifest["total_rows"] = len(rows)
    manifest["unique_people"] = len({str(row.get("id") or row.get("email")) for row in rows if row.get("id") or row.get("email")})
    write_json(out_dir / "hkust_gz_faculty_manifest.json", manifest)
    write_json(out_dir / "hkust_gz_faculty_profiles.json", rows)
    write_csv(out_dir / "hkust_gz_faculty_profiles.csv", rows)
    print(json.dumps({"output_dir": str(out_dir), "rows": len(rows), "unique_people": manifest["unique_people"]}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl HKUST(GZ) public faculty profiles by Hub and Thrust.")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list-thrusts", help="List supported Hub/Thrust codes and aliases.")
    list_p.add_argument("--hub", help="Filter by Hub name/key/code.")
    list_p.add_argument("--include-extra-units", action="store_true", help="Include non-main public units in the embedded map.")
    list_p.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    list_p.set_defaults(func=cmd_list_thrusts)

    discover_p = sub.add_parser("discover-map", help="Fetch the frontend bundle and compare discovered Thrust codes with the embedded map.")
    discover_p.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    discover_p.add_argument("--output", help="Optional JSON output path.")
    discover_p.set_defaults(func=cmd_discover_map)

    crawl_p = sub.add_parser("crawl", help="Crawl selected Hub/Thrust faculty profiles.")
    crawl_p.add_argument("--hub", help="Hub name/key/code, e.g. Information Hub or INFOHUB.")
    crawl_p.add_argument("--thrust", action="append", help="Thrust name/key/code. Repeat or comma-separate for several Thrusts.")
    crawl_p.add_argument("--thrust-url", action="append", help="Official thrust-faculties URL with code=...")
    crawl_p.add_argument("--all-thrusts", action="store_true", help="Crawl all Thrusts under --hub.")
    crawl_p.add_argument("--include-extra-units", action="store_true", help="Allow non-main public units from the embedded map.")
    crawl_p.add_argument("--source", choices=["page", "official", "both"], default="both", help="Public endpoint lane to use.")
    crawl_p.add_argument("--include-details", action="store_true", help="Fetch public profile/primary detail for each person.")
    crawl_p.add_argument("--output-dir", default="output/hkust_gz_faculty", help="Output directory.")
    crawl_p.add_argument("--page-size", type=int, default=10000, help="Page endpoint size; frontend uses a large value too.")
    crawl_p.add_argument("--max-people", type=int, help="Limit normalized people per selected Thrust; useful for smoke tests.")
    crawl_p.add_argument("--dedupe", choices=["none", "person"], default="none", help="Dedupe output rows across selected Thrusts.")
    crawl_p.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    crawl_p.add_argument("--sleep", type=float, default=0.0, help="Delay between endpoint calls.")
    crawl_p.add_argument("--dry-run", action="store_true", help="Print resolved selections and URLs without crawling.")
    crawl_p.set_defaults(func=cmd_crawl)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except CrawlError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
