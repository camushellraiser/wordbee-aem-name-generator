from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

BASE_URL = (
    "https://author-prod-use1.aemprod.thermofisher.net/"
    "projects/details.html/content/projects/"
)

# First column copied from AEM usually contains the reference.
# We accept optional trailing source suffixes such as _PDP after AEM.
REFERENCE_RE = re.compile(
    r"(?P<gtsid>GTS\d+)_Web_(?P<owner_token>[A-Za-z][A-Za-z0-9]+)_(?P<title>.+?)_(?P<system>AEM|IRIS)(?P<suffixes>(?:_[A-Za-z0-9-]+)*)$",
    re.IGNORECASE,
)

SPLIT_RE = re.compile(r"\t+|\s{2,}|\s*\|\s*")


@dataclass(frozen=True)
class ParsedProject:
    reference: str
    gtsid: str
    owner_token: str
    title_raw: str
    source_system: str
    source_suffixes: str = ""
    source_row: str = ""


def normalize_title_for_output(title: str) -> str:
    title = title.strip()
    title = re.sub(r"\s+", "-", title)
    title = re.sub(r"[^A-Za-z0-9_-]", "", title)
    title = re.sub(r"-{2,}", "-", title)
    title = re.sub(r"_{2,}", "_", title)
    return title.strip("-_")


def slugify_for_url(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9_-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = re.sub(r"_{2,}", "_", slug)
    return slug.strip("-_")


def derive_owner_token(owner_name: str) -> str:
    """Convert a visible owner name into the Wordbee token.

    Examples:
      Pratyusha Mantha -> PMantha
      Ivy Cao -> ICao
    """
    tokens = re.findall(r"[A-Za-z]+", owner_name)
    if len(tokens) >= 2:
        first = tokens[-2]
        last = tokens[-1]
    elif len(tokens) == 1:
        first = tokens[0]
        last = ""
    else:
        raise ValueError("Could not derive owner token from the pasted text.")

    first_initial = first[0].upper()
    remainder = last[:1].upper() + last[1:] if last else ""
    return f"{first_initial}{remainder}"


def normalize_owner_token(owner_token: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", owner_token.strip())
    if not cleaned:
        raise ValueError("Owner token could not be parsed.")
    return cleaned[0].upper() + cleaned[1:]


def build_wordbee_name(gtsid: str, owner_token: str, title: str, system: str) -> str:
    title_part = normalize_title_for_output(title)
    return f"{gtsid.strip()}_Web_{normalize_owner_token(owner_token)}_{title_part}_{system}"


def build_aem_name(gtsid: str, owner_token: str, title: str, country_suffix: str) -> str:
    title_part = normalize_title_for_output(title)
    return f"{gtsid.strip()}_Web_{normalize_owner_token(owner_token)}_{title_part}_{country_suffix}"


def build_aem_url(aem_name: str) -> str:
    return f"{BASE_URL}{slugify_for_url(aem_name)}"


def _split_row(row: str) -> List[str]:
    return [piece.strip() for piece in SPLIT_RE.split(row) if piece.strip()]


def _match_reference(text: str) -> Optional[re.Match[str]]:
    text = text.strip()
    if not text:
        return None
    return REFERENCE_RE.search(text)


def _guess_owner_name_from_row(row: str, pieces: List[str]) -> Optional[str]:
    # Prefer the last cell that looks like a person's full name.
    candidates = [piece.strip() for piece in pieces if piece.strip()]
    for candidate in reversed(candidates):
        if len(re.findall(r"[A-Za-z]+", candidate)) >= 2 and "thermo fisher" not in candidate.lower():
            return candidate

    # Fallback: use the last two word-like tokens in the row.
    tokens = re.findall(r"[A-Za-z]+", row)
    if len(tokens) >= 2:
        return f"{tokens[-2]} {tokens[-1]}"
    return None


def parse_projects(pasted_text: str) -> List[ParsedProject]:
    """Parse one or more rows copied from AEM.

    Works with text copied as:
      - tab separated cells
      - pipe separated cells
      - wrapped row text with line breaks
      - multiple selected rows pasted together
    """
    text = pasted_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    row_candidates = [line.strip() for line in text.split("\n") if line.strip()]
    projects: List[ParsedProject] = []
    seen_refs: set[str] = set()

    for row in row_candidates:
        pieces = _split_row(row)
        # First try the first visible cell, since copied AEM rows generally put the reference first.
        first_cell = pieces[0] if pieces else row
        reference_match = _match_reference(first_cell)
        if not reference_match:
            reference_match = _match_reference(row)
        if not reference_match:
            continue

        gtsid = reference_match.group("gtsid")
        owner_token = reference_match.group("owner_token")
        title_raw = reference_match.group("title")
        source_system = reference_match.group("system").upper()
        source_suffixes = reference_match.group("suffixes") or ""

        if not owner_token or owner_token.lower() in {"web", "aem", "iris"}:
            owner_name = _guess_owner_name_from_row(row, pieces)
            if owner_name:
                owner_token = derive_owner_token(owner_name)

        reference = reference_match.group(0).strip()
        if reference in seen_refs:
            continue
        seen_refs.add(reference)

        projects.append(
            ParsedProject(
                reference=reference,
                gtsid=gtsid,
                owner_token=normalize_owner_token(owner_token),
                title_raw=title_raw.strip(),
                source_system=source_system,
                source_suffixes=source_suffixes,
                source_row=row,
            )
        )

    return projects
