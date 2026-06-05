from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

BASE_URL = (
    'https://author-prod-use1.aemprod.thermofisher.net/'
    'projects/details.html/content/projects/'
)

REFERENCE_RE = re.compile(
    r'(?P<gtsid>GTS\d+)_Web_(?P<owner_token>[A-Za-z][A-Za-z0-9]+)_(?P<title>.+?)_(?P<system>AEM|IRIS)(?P<extras>(?:_[A-Za-z0-9-]+)*)',
    re.IGNORECASE,
)

OWNER_LINE_RE = re.compile(r'^[A-Z][A-Za-zÀ-ÿ\'.-]+(?:\s+[A-Z][A-Za-zÀ-ÿ\'.-]+)+$')
ORDER_RE = re.compile(r'\b\d{5,}\b')


@dataclass(frozen=True)
class ParsedRecord:
    raw_text: str
    reference: Optional[str]
    title_raw: str
    owner_name: str


def normalize_owner_token(owner_name: str) -> str:
    parts = [p for p in re.split(r'\s+', owner_name.strip()) if p]
    if not parts:
        raise ValueError('Owner name is required.')
    first = re.sub(r'[^A-Za-z0-9]', '', parts[0])
    last = re.sub(r'[^A-Za-z0-9]', '', parts[-1])
    if not first or not last:
        raise ValueError('Owner name could not be parsed.')
    return first[0].upper() + last


def normalize_title_for_output(title: str) -> str:
    title = title.strip()
    title = re.sub(r'\s+', '-', title)
    title = re.sub(r'[^A-Za-z0-9_-]', '', title)
    title = re.sub(r'-{2,}', '-', title)
    title = re.sub(r'_{2,}', '_', title)
    return title.strip('-_')


def slugify_for_url(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9_-]', '', slug)
    slug = re.sub(r'-{2,}', '-', slug)
    slug = re.sub(r'_{2,}', '_', slug)
    return slug.strip('-_')


def build_wordbee_name(gtsid: str, owner_name: str, title: str, system: str) -> str:
    return f'{gtsid.strip()}_Web_{normalize_owner_token(owner_name)}_{normalize_title_for_output(title)}_{system}'


def build_aem_name(gtsid: str, owner_name: str, title: str, country_suffix: str) -> str:
    return f'{gtsid.strip()}_Web_{normalize_owner_token(owner_name)}_{normalize_title_for_output(title)}_{country_suffix}'


def build_aem_url(aem_name: str) -> str:
    return f'{BASE_URL}{slugify_for_url(aem_name)}'


def split_records(pasted_text: str) -> List[str]:
    text = (pasted_text or '').replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        return []

    blocks = [b.strip() for b in re.split(r'\n\s*\n+', text) if b.strip()]
    if len(blocks) > 1:
        return blocks

    refs = list(REFERENCE_RE.finditer(text))
    if len(refs) > 1:
        return [m.group(0) for m in refs]

    return [text]


def parse_record(record_text: str) -> ParsedRecord:
    lines = [ln.strip() for ln in record_text.replace('\r\n', '\n').replace('\r', '\n').split('\n') if ln.strip()]
    normalized = ' '.join(lines)

    ref_match = REFERENCE_RE.search(normalized)
    if ref_match:
        return ParsedRecord(
            raw_text=record_text,
            reference=ref_match.group(0),
            title_raw=ref_match.group('title').strip(),
            owner_name=_extract_owner(lines, normalized),
        )

    title = _extract_title(lines, normalized)
    owner = _extract_owner(lines, normalized)
    return ParsedRecord(raw_text=record_text, reference=None, title_raw=title, owner_name=owner)


def _extract_title(lines: list[str], text: str) -> str:
    patterns = [
        r'^(?P<title>.+?)\s+\d{5,}\s+View document\(s\)',
        r'^(?P<title>.+?)\s+\d{5,}\s+Corporation\s+Thermo\s+Fisher',
        r'^(?P<title>.+?)\s+\d{5,}\s+',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group('title').strip()

    if lines:
        first = lines[0].strip()
        # If the first line is actually a generated reference, defer to the tokenized title part.
        ref = REFERENCE_RE.search(first)
        if ref:
            return ref.group('title').strip()
        return first

    return text.strip()


def _extract_owner(lines: list[str], text: str) -> str:
    # Prefer a line that looks like a person name and is closest to the bottom.
    for line in reversed(lines):
        if 'Thermo Fisher' in line:
            continue
        if OWNER_LINE_RE.match(line):
            return line.strip()

    # Prefer the bit after the last "Thermo Fisher" marker.
    m = re.search(r'Thermo\s+Fisher\s+(?P<owner>[A-Z][A-Za-zÀ-ÿ\'.-]+(?:\s+[A-Z][A-Za-zÀ-ÿ\'.-]+)+)\s*$', text)
    if m:
        return m.group('owner').strip()

    m = re.search(r'Thermo\s+Fisher\s+(?P<owner>[A-Z][A-Za-zÀ-ÿ\'.-]+(?:\s+[A-Z][A-Za-zÀ-ÿ\'.-]+)+)', text)
    if m:
        return m.group('owner').strip()

    # Last resort: last two alphabetic tokens.
    tokens = [t for t in re.split(r'\s+', text) if t]
    if len(tokens) >= 2:
        return f'{tokens[-2]} {tokens[-1]}'
    if tokens:
        return tokens[-1]
    return ''
