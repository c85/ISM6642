#!/usr/bin/env python3
"""Collect official LA Fitness advertised rates for Florida clubs.

The LA Fitness site exposes club-specific membership rates through its public
signup flow.  This collector follows that flow and stores the advertised
recurring monthly dues, initiation fees, annual fees, plan amounts, source URL,
and retrieval timestamp.  It does not create a synthetic price target.

The collector uses only the public website and a conservative request delay.
Prices are advertised offers, not member transaction prices, and may change
without notice.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOCATION_PATH = DATA_DIR / "gym_locations.csv"
OUTPUT_PATH = DATA_DIR / "la_fitness_pricing.csv"
SIGNUP_URL = "https://www.lafitness.com/Pages/MembershipSignUpSearch.aspx"
USER_AGENT = "ISM6642-course-analysis/1.0 (public-data collection)"


def clean_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value).replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_amounts(pattern: str, text: str) -> list[float]:
    values: list[float] = []
    for raw in re.findall(pattern, text, flags=re.IGNORECASE):
        value = float(raw.replace(",", ""))
        if value not in values:
            values.append(value)
    return values


def parse_cards(page: str) -> list[dict[str, str]]:
    chunks = re.findall(
        r'<div class="location-card".*?(?=<div class="location-card"|</form>)',
        page,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cards: list[dict[str, str]] = []
    for chunk in chunks:
        club_match = re.search(r'data-clubid="(\d+)"', chunk, flags=re.IGNORECASE)
        title_match = re.search(
            r'class="[^"]*title-text[^"]*">(.*?)</span>',
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        address_match = re.search(
            r'class="[^"]*address[^"]*">(.*?)</span>',
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        hidden_match = re.search(
            r'name="([^"]*HiddenClubId)"[^>]*value="(\d+)"',
            chunk,
            flags=re.IGNORECASE,
        )
        if not (club_match and title_match and address_match and hidden_match):
            continue
        club_id = club_match.group(1)
        hidden_id = hidden_match.group(2)
        if club_id != hidden_id:
            continue
        hidden_name = hidden_match.group(1)
        event_target = hidden_name.rsplit("$", 1)[0] + "$btnJoinNow"
        address = clean_html(address_match.group(1))
        if not re.search(r"\bFL\b", address, flags=re.IGNORECASE):
            continue
        cards.append(
            {
                "ClubID": club_id,
                "OfficialClubName": clean_html(title_match.group(1)),
                "OfficialAddress": address,
                "EventTarget": event_target,
            }
        )
    return cards


def hidden_form_fields(page: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for tag in re.findall(r"<input\b[^>]*>", page, flags=re.IGNORECASE):
        if not re.search(r'type\s*=\s*["\']hidden["\']', tag, flags=re.IGNORECASE):
            continue
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
        value_match = re.search(r'value\s*=\s*["\']([^"\']*)["\']', tag, flags=re.IGNORECASE)
        if name_match:
            fields[html.unescape(name_match.group(1))] = html.unescape(
                value_match.group(1) if value_match else ""
            )
    return fields


def fetch(opener: Any, url: str, data: bytes | None = None) -> tuple[str, str]:
    request = Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, "Referer": SIGNUP_URL},
    )
    with opener.open(request, timeout=45) as response:
        body = response.read().decode("utf-8", "ignore")
        return response.geturl(), body


def get_rate_page(
    opener: Any, card: dict[str, str], signup_page: str | None = None
) -> tuple[str, str]:
    if signup_page is None:
        _, signup_page = fetch(opener, SIGNUP_URL)
    fields = hidden_form_fields(signup_page)
    fields["__EVENTTARGET"] = card["EventTarget"]
    fields["__EVENTARGUMENT"] = ""
    fields.setdefault("__LASTFOCUS", "")
    payload = urlencode(fields).encode("utf-8")
    return fetch(opener, SIGNUP_URL, data=payload)


def amount_in_plan(block: str, code: str, field: str) -> float | None:
    match = re.search(
        rf'id="[^"]*lbl{code}{field}"[^>]*>.*?\$([0-9][0-9,]*\.\d{{2}})',
        block,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return float(match.group(1).replace(",", "")) if match else None


def parse_plan_cards(page: str) -> list[dict[str, Any]]:
    """Parse each LA Fitness plan card without confusing totals for fees."""
    starts = list(
        re.finditer(
            r'<div\b[^>]*\bid="[^"]*div(?P<code>Standard|Classic|Premier|Signature)Rate"[^>]*>',
            page,
            flags=re.IGNORECASE,
        )
    )
    plan_names = {
        "standard": "Basic",
        "classic": "Classic",
        "premier": "Classic",
        "signature": "Signature",
    }
    access_labels = (
        "Club of Enrollment",
        "Multi Club",
        "State of Enrollment",
        "Nationwide Access",
    )
    plans: list[dict[str, Any]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(page)
        block = page[start.start() : end]
        code = start.group("code")
        monthly = amount_in_plan(block, code, "Rate")
        if monthly is None:
            continue
        initiation = amount_in_plan(block, code, "InitiationFee")
        annual = amount_in_plan(block, code, "AnnualFee")
        visible = re.sub(r"<script.*?</script>|<style.*?</style>", " ", block, flags=re.I | re.S)
        visible = re.sub(r"\s+", " ", clean_html(visible))
        access = "; ".join(
            label for label in access_labels if re.search(re.escape(label), visible, re.I)
        )
        first_year_cost = (
            (12 * monthly + initiation + annual) / 12
            if initiation is not None and annual is not None
            else None
        )
        plans.append(
            {
                "plan_id": code,
                "plan": plan_names[code.casefold()],
                "access": access,
                "monthly_dues": monthly,
                "initiation_fee": initiation,
                "annual_fee": annual,
                "effective_monthly_cost": first_year_cost,
            }
        )
    return plans


def parse_rates(page: str) -> dict[str, Any]:
    plans = parse_plan_cards(page)

    def unique_amounts(field: str) -> list[float]:
        values = []
        for plan in plans:
            value = plan[field]
            if value is not None and value not in values:
                values.append(value)
        return values

    monthly = unique_amounts("monthly_dues")
    initiation = unique_amounts("initiation_fee")
    annual = unique_amounts("annual_fee")
    basic = next((plan for plan in plans if plan["plan_id"].casefold() == "standard"), None)
    return {
        "MonthlyDuesOptions": monthly,
        "InitiationFeeOptions": initiation,
        "AnnualFeeOptions": annual,
        "Plans": plans,
        # Some pages include a zero-dollar placeholder card for an add-on or
        # unavailable plan.  Do not let that placeholder become the base rate.
        "BaseMonthlyDues": min((value for value in monthly if value > 0), default=""),
        "BasicMonthlyDues": basic["monthly_dues"] if basic else "",
        "BasicInitiationFee": basic["initiation_fee"] if basic else "",
        "BasicAnnualFee": basic["annual_fee"] if basic else "",
        "BasicEffectiveMonthlyCost": basic["effective_monthly_cost"] if basic else "",
        "Status": "Observed" if monthly else "No rate found",
    }


def zip_code(value: str) -> str:
    match = re.search(r"\b(\d{5})(?:-\d{4})?\b", value)
    return match.group(1) if match else ""


def street_part(value: str) -> str:
    return value.split(",", 1)[0]


def street_signature(value: str) -> tuple[str, str]:
    street = street_part(value).lower()
    number_match = re.search(r"\b\d+\b", street)
    number = number_match.group(0) if number_match else ""
    tokens = re.findall(r"[a-z0-9]+", street)
    tokens = [token for token in tokens if token not in {"suite", "ste", "unit", "apt"}]
    return number, " ".join(tokens[:5])


def load_county_matches() -> list[dict[str, str]]:
    with LOCATION_PATH.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["GymChain"] == "LA Fitness"]
    return rows


def match_county(card: dict[str, str], current_rows: list[dict[str, str]]) -> tuple[str, str]:
    official_zip = zip_code(card["OfficialAddress"])
    official_number, official_sig = street_signature(card["OfficialAddress"])
    candidates = [row for row in current_rows if zip_code(row["Address"]) == official_zip]
    exact = [
        row
        for row in candidates
        if street_signature(row["Address"])[0] == official_number
        and (
            official_sig in street_signature(row["Address"])[1]
            or street_signature(row["Address"])[1] in official_sig
        )
    ]
    if len(exact) == 1:
        return exact[0]["CountyName"], "Google location address match"
    overrides = {
        "Valrico @ State Road 60 E": ("Hillsborough County", "city/address override"),
        "Hialeah-Palmetto Expy": ("Miami-Dade County", "city/address override"),
        "New Tampa": ("Hillsborough County", "city/address override"),
    }
    if card["OfficialClubName"] in overrides:
        return overrides[card["OfficialClubName"]]
    if len(candidates) == 1:
        return candidates[0]["CountyName"], "ZIP-only match"
    return "", "unmatched"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.6, help="Seconds between club requests")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=0, help="Collect only the first N clubs (for testing)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    opener = build_opener(HTTPCookieProcessor())
    _, initial_page = fetch(opener, SIGNUP_URL)
    cards = parse_cards(initial_page)
    if args.limit > 0:
        cards = cards[: args.limit]
    current_rows = load_county_matches()
    retrieved_at = datetime.now(timezone.utc).isoformat()
    output_rows: list[dict[str, Any]] = []

    print(f"Found {len(cards)} Florida clubs in the official signup directory.", flush=True)
    for index, card in enumerate(cards, start=1):
        county, match_method = match_county(card, current_rows)
        try:
            rate_url, rate_page = get_rate_page(opener, card, signup_page=initial_page)
            rates = parse_rates(rate_page)
            error = ""
        except Exception as exc:  # keep a row and continue if one club fails
            rate_url = ""
            rates = {
                "MonthlyDuesOptions": [],
                "InitiationFeeOptions": [],
                "AnnualFeeOptions": [],
                "Plans": [],
                "BaseMonthlyDues": "",
                "BasicMonthlyDues": "",
                "BasicInitiationFee": "",
                "BasicAnnualFee": "",
                "BasicEffectiveMonthlyCost": "",
                "Status": "Request failed",
            }
            error = f"{type(exc).__name__}: {exc}"
        output_rows.append(
            {
                "ClubID": card["ClubID"],
                "OfficialClubName": card["OfficialClubName"],
                "OfficialAddress": card["OfficialAddress"].replace("\n", ", "),
                "ZipCode": zip_code(card["OfficialAddress"]),
                "CountyName": county,
                "CountyMatchMethod": match_method,
                "BaseMonthlyDues": rates["BaseMonthlyDues"],
                "BasicMonthlyDues": rates["BasicMonthlyDues"],
                "BasicInitiationFee": rates["BasicInitiationFee"],
                "BasicAnnualFee": rates["BasicAnnualFee"],
                "BasicEffectiveMonthlyCost": rates["BasicEffectiveMonthlyCost"],
                "MonthlyDuesOptions": json.dumps(rates["MonthlyDuesOptions"]),
                "InitiationFeeOptions": json.dumps(rates["InitiationFeeOptions"]),
                "AnnualFeeOptions": json.dumps(rates["AnnualFeeOptions"]),
                "Plans": json.dumps(rates["Plans"]),
                "Status": rates["Status"],
                "SourceURL": rate_url,
                "RetrievedAtUTC": retrieved_at,
                "Error": error,
            }
        )
        print(
            f"[{index}/{len(cards)}] {card['OfficialClubName']}: "
            f"{rates['Status']} {rates['BaseMonthlyDues']}",
            flush=True,
        )
        if index < len(cards):
            time.sleep(max(0.0, args.delay))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0].keys()) if output_rows else []
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    unmatched = sum(not row["CountyName"] for row in output_rows)
    observed = sum(row["Status"] == "Observed" for row in output_rows)
    print(
        f"Wrote {len(output_rows)} rows to {args.output}. "
        f"Observed rates: {observed}; unmatched counties: {unmatched}.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
