from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

BASE_URL = (
    "https://author-prod-use1.aemprod.thermofisher.net/"
    "projects/details.html/content/projects/"
)

SPLIT_RE = re.compile(r"\t+|\s{2,}|\s*\|\s*")

GENERIC_TOKENS = {
    "view",
    "document",
    "documents",
    "document(s)",
    "corporation",
    "thermo",
    "fisher",
    "thermo fisher",
    "thermo fisher inc",
    "thermo fisher scientific",
    "n/a",
    "na",
}


@dataclass(frozen=True)
class ParsedProject:
    reference: str
    gtsid: str
    owner_token: str
    title_raw: str
    source_system: str = "AEM"
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


def _clean_cell(cell: str) -> str:
    cell = re.sub(r"\s+", " ", cell).strip()
    return cell


def _looks_like_person_name(text: str) -> bool:
    text = _clean_cell(text)
    if not text:
        return False
    lower = text.lower()
    if lower in GENERIC_TOKENS:
        return False
    if any(token in lower for token in ["thermo fisher", "view document", "order id", "reference"]):
        return False
    parts = re.findall(r"[A-Za-z]+", text)
    return len(parts) >= 2 and len(parts) <= 4


def _guess_title_from_cells(cells: Sequence[str]) -> str:
    for cell in cells:
        cleaned = _clean_cell(cell)
        if not cleaned:
            continue
        lower = cleaned.lower()
        if lower in GENERIC_TOKENS:
            continue
        if lower.startswith("view document"):
            continue
        if lower.startswith("corporation"):
            continue
        if lower.startswith("thermo fisher"):
            continue
        if re.fullmatch(r"\d+", cleaned):
            continue
        return cleaned
    return _clean_cell(cells[0]) if cells else ""


def _guess_owner_name_from_row(row: str, cells: Sequence[str]) -> Optional[str]:
    candidates = [
        _clean_cell(cell)
        for cell in cells
        if _looks_like_person_name(cell)
    ]
    if candidates:
        return candidates[-1]

    # Try the end of the row; this works well when the company name is followed by the person name.
    trailing_patterns = [
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$",
        r"([A-Z][A-Za-z'-]+\s+[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+)?)\s*$",
    ]
    for pattern in trailing_patterns:
        matches = re.findall(pattern, row)
        if matches:
            return _clean_cell(matches[-1])

    tokens = re.findall(r"[A-Za-z]+", row)
    if len(tokens) >= 2:
        return f"{tokens[-2]} {tokens[-1]}"
    return None


def _split_into_rows(pasted_text: str) -> List[str]:
    text = pasted_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    raw_lines = [line.rstrip() for line in text.split("\n")]
    rows: List[str] = []
    buffer: List[str] = []

    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                rows.append(" ".join(buffer).strip())
                buffer = []
            continue
        # Keep likely wrapped lines together.
        if buffer and _looks_like_person_name(stripped):
            buffer.append(stripped)
            rows.append(" ".join(buffer).strip())
            buffer = []
        else:
            if buffer and re.search(r"\d{4,}", stripped) and not _looks_like_person_name(stripped):
                buffer.append(stripped)
            elif buffer and len(buffer) == 1 and len(stripped.split()) <= 4 and not re.search(r"\d{4,}", stripped):
                buffer.append(stripped)
                rows.append(" ".join(buffer).strip())
                buffer = []
            else:
                if buffer:
                    rows.append(" ".join(buffer).strip())
                    buffer = []
                buffer.append(stripped)

    if buffer:
        rows.append(" ".join(buffer).strip())

    # If the heuristic split produced only one row, use it as-is.
    return [row for row in rows if row]


def parse_projects(pasted_text: str, gtsid: str) -> List[ParsedProject]:
    """Parse one or more rows copied from AEM.

    This version does not require a reference in the pasted text.
    It uses the user-entered GTS ID and extracts the title from the first
    meaningful cell while taking the owner from the last person-like cell.
    """
    gtsid_clean = gtsid.strip()
    if not gtsid_clean:
        return []

    rows = _split_into_rows(pasted_text)
    if not rows:
        return []

    projects: List[ParsedProject] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        cells = _split_row(row)
        if not cells:
            continue

        title = _guess_title_from_cells(cells)
        owner_name = _guess_owner_name_from_row(row, cells)
        if not title or not owner_name:
            continue

        owner_token = normalize_owner_token(derive_owner_token(owner_name))
        key = (title.lower(), owner_token.lower())
        if key in seen:
            continue
        seen.add(key)

        projects.append(
            ParsedProject(
                reference=title,
                gtsid=gtsid_clean,
                owner_token=owner_token,
                title_raw=title,
                source_system="AEM",
                source_row=row,
            )
        )

    return projects
