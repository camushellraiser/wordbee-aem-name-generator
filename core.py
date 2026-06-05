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
    text = re.sub(r'\s+', ' ', record_text.replace('\t', ' ')).strip()

    ref_match = REFERENCE_RE.search(text)
    if ref_match:
        return ParsedRecord(
            raw_text=record_text,
            reference=ref_match.group(0),
            title_raw=ref_match.group('title').strip(),
            owner_name=_extract_owner(text),
        )

    title = _extract_title(text)
    owner = _extract_owner(text)
    return ParsedRecord(raw_text=record_text, reference=None, title_raw=title, owner_name=owner)


def _extract_title(text: str) -> str:
    # Prefer content before the order id or before "View document(s)"
    patterns = [
        r'^(?P<title>.+?)\s+\d{5,}\s+View document\(s\)',
        r'^(?P<title>.+?)\s+\d{5,}\s+Corporation\s+Thermo\s+Fisher',
        r'^(?P<title>.+?)\s+\d{5,}\s+',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group('title').strip()

    # Fallback: use the leading chunk before common separators.
    cut_tokens = [' View document(s) ', ' Thermo Fisher ', ' Corporation Thermo Fisher ']
    for token in cut_tokens:
        if token in text:
            text = text.split(token, 1)[0].strip()
    if ' ' in text:
        first_line = text.split(' ', 1)[0].strip()
        if first_line:
            return first_line
    return text.strip()


def _extract_owner(text: str) -> str:
    # Prefer the bit after the last "Thermo Fisher" marker.
    m = re.search(r'Thermo\s+Fisher\s+(?P<owner>[A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+)+)\s*$', text)
    if m:
        return m.group('owner').strip()

    m = re.search(r'Thermo\s+Fisher\s+(?P<owner>[A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+)+)', text)
    if m:
        return m.group('owner').strip()

    # Last resort: last two tokens.
    tokens = [t for t in re.split(r'\s+', text) if t]
    if len(tokens) >= 2:
        return f'{tokens[-2]} {tokens[-1]}'
    if tokens:
        return tokens[-1]
    return ''
