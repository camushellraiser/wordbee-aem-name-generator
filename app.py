from __future__ import annotations

import csv
import html
import io
import json
import re
from pathlib import Path
from typing import Iterable

import streamlit as st
import streamlit.components.v1 as components

from core import build_aem_name, build_aem_url, build_wordbee_name, parse_record, split_records

COUNTRIES: list[tuple[str, str, str]] = [
    ('🇩🇪', 'de-DE', 'DE'),
    ('🇪🇸', 'es-ES', 'ES'),
    ('🇫🇷', 'fr-FR', 'FR'),
    ('🇯🇵', 'ja-JP', 'JP'),
    ('🇰🇷', 'ko-KR', 'KR'),
    ('🇨🇳', 'zh-CN', 'CN'),
    ('🇧🇷', 'pt-BR', 'BR'),
    ('🇹🇼', 'zh-TW', 'TW'),
]
COUNTRY_OPTIONS = [f'{flag} {code}' for flag, code, _ in COUNTRIES]
COUNTRY_TO_SUFFIX = {f'{flag} {code}': suffix for flag, code, suffix in COUNTRIES}
COUNTRY_TO_FLAG = {f'{flag} {code}': flag for flag, code, suffix in COUNTRIES}
COUNTRY_TO_CODE = {f'{flag} {code}': code for flag, code, suffix in COUNTRIES}

st.set_page_config(
    page_title='Wordbee Name',
    page_icon='🏷️',
    layout='wide',
    initial_sidebar_state='collapsed',
)


# ---------- Styling ----------

def apply_style() -> None:
    st.markdown(
        '''
        <style>
        :root {
            --bg: #f6f8fc;
            --card: rgba(255,255,255,0.95);
            --border: rgba(148,163,184,0.24);
            --text: #0f172a;
            --muted: #5b667a;
            --accent: #4f46e5;
            --accent2: #0ea5e9;
            --soft: #eef2ff;
            --shadow: 0 18px 48px rgba(15,23,42,.08);
            --shadow2: 0 8px 24px rgba(15,23,42,.06);
        }

        html, body, [class*="st"], p, div, span, label, input, textarea, button, select {
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
        }

        .stApp {
            background: radial-gradient(circle at top left, #ffffff 0%, #f6f8fc 40%, #ecf4fb 100%);
            color: var(--text);
        }

        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { right: 1rem; }

        .hero {
            padding: 1.35rem 1.45rem 1.1rem;
            border: 1px solid var(--border);
            border-radius: 28px;
            background: var(--card);
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.05;
            letter-spacing: -0.04em;
            font-weight: 900;
        }
        .hero p {
            margin: .45rem 0 0;
            color: var(--muted);
            font-size: .98rem;
        }
        .pills { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:.95rem; }
        .pill {
            display:inline-flex; align-items:center; gap:.45rem;
            padding:.46rem .8rem; border-radius:999px;
            background: linear-gradient(180deg, #fff, #f8faff);
            border: 1px solid rgba(79,70,229,.18);
            color:#3730a3; font-weight:800; font-size:.86rem;
        }

        .section-card {
            margin-top: .95rem;
            padding: 1rem 1rem 1.05rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: var(--shadow2);
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 900;
            letter-spacing: -0.02em;
            margin-bottom: .45rem;
        }
        .subtle { color: var(--muted); margin-bottom: .75rem; }

        div[data-testid="stTextArea"] textarea {
            min-height: 240px !important;
            border-radius: 18px !important;
            border-color: rgba(148,163,184,.28) !important;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
            font-size: .95rem !important;
            line-height: 1.48 !important;
        }
        div[data-testid="stTextInput"] input {
            border-radius: 14px !important;
            font-size: .98rem !important;
        }
        div[data-testid="stMultiSelect"] > div {
            border-radius: 14px !important;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 999px !important;
            font-weight: 800 !important;
        }
        div[data-testid="stFormSubmitButton"] > button {
            width: 100%;
            background: linear-gradient(90deg, var(--accent), #4338ca) !important;
            color: white !important;
            border: none !important;
            padding: .72rem 1rem !important;
            box-shadow: 0 10px 24px rgba(79,70,229,.22);
        }

        .hint {
            color: var(--muted);
            font-size: .9rem;
            margin: .15rem 0 .6rem;
        }

        .empty-box {
            padding: 1rem 1.05rem;
            border-radius: 16px;
            border: 1px dashed #cbd5e1;
            background: #f8fafc;
            color: #475569;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
            gap: 14px;
        }
        .entry-card {
            border: 1px solid #dbe4f0;
            border-radius: 20px;
            background: linear-gradient(180deg, #fff, #fbfcff);
            box-shadow: 0 10px 24px rgba(15,23,42,.05);
            padding: 14px 14px 12px;
        }
        .entry-head {
            display:flex; justify-content:space-between; align-items:flex-start; gap: .75rem;
            margin-bottom: .65rem;
        }
        .entry-title {
            font-size: 1rem;
            font-weight: 900;
            letter-spacing: -0.02em;
        }
        .entry-meta {
            color: #64748b;
            font-size: .82rem;
            font-weight: 700;
            margin-top: .12rem;
        }
        .badge {
            display:inline-flex; align-items:center; gap:.35rem;
            padding: .36rem .64rem;
            border-radius: 999px;
            background: #eef2ff;
            color: #4338ca;
            font-size: .79rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .block {
            margin-top: .55rem;
            padding: .8rem .85rem;
            border-radius: 14px;
            background: #0f172a;
            color: #e2e8f0;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
            font-size: .9rem;
            line-height: 1.45;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .block.light {
            background: #f8fafc;
            color: #0f172a;
            border: 1px solid #e2e8f0;
        }
        .copy-row {
            display:flex; justify-content:flex-end; margin-top:.55rem;
        }
        .copy-btn {
            border: none;
            padding: .46rem .78rem;
            border-radius: 999px;
            background: linear-gradient(90deg, #2563eb, #4f46e5);
            color: white;
            font-size: .82rem;
            font-weight: 800;
            cursor: pointer;
        }
        .copy-btn.ok { background: linear-gradient(90deg, #0f766e, #059669); }

        .csv-note {
            margin-top: .45rem;
            font-size: .9rem;
            color: #64748b;
        }
        </style>
        ''',
        unsafe_allow_html=True,
    )


def hard_refresh() -> None:
    st.session_state.clear()
    st.rerun()


# ---------- HTML helpers ----------

def esc(value: str) -> str:
    return html.escape(value, quote=True)


def render_results(title: str, items: list[dict[str, str]]) -> None:
    if not items:
        return

    html_parts: list[str] = [f'<div class="section-title">{esc(title)}</div>', '<div class="grid">']

    for item in items:
        badge = item.get('badge', '')
        head = item.get('head', '')
        meta = item.get('meta', '')
        value = item.get('value', '')
        copy_value = item.get('copy_value', value)
        kind = item.get('kind', 'dark')
        block_class = 'block light' if kind == 'light' else 'block'
        button_class = 'copy-btn ok' if kind == 'light' else 'copy-btn'
        encoded = json.dumps(copy_value)

        html_parts.append(
            f'''
            <div class="entry-card">
                <div class="entry-head">
                    <div>
                        <div class="entry-title">{esc(head)}</div>
                        {f'<div class="entry-meta">{esc(meta)}</div>' if meta else ''}
                    </div>
                    {f'<div class="badge">{esc(badge)}</div>' if badge else ''}
                </div>
                <div class="{block_class}" data-copy-value={encoded}>{esc(value)}</div>
                <div class="copy-row">
                    <button class="{button_class}" type="button" data-copy-target={encoded}>Copy</button>
                </div>
            </div>
            '''
        )

    html_parts.append('</div>')
    html_parts.append(
        '''
        <script>
        (function() {
            const buttons = document.querySelectorAll('[data-copy-target]');
            buttons.forEach((btn) => {
                btn.addEventListener('click', async () => {
                    const value = btn.getAttribute('data-copy-target') || '';
                    try {
                        await navigator.clipboard.writeText(JSON.parse(value));
                        const original = btn.textContent;
                        btn.textContent = 'Copied!';
                        setTimeout(() => { btn.textContent = original; }, 900);
                    } catch (e) {
                        console.warn('Clipboard failed', e);
                    }
                });
            });
        })();
        </script>
        '''
    )

    components.html('\n'.join(html_parts), height=280 * len(items) + 20, scrolling=True)


# ---------- CSV ----------

def build_csv(rows: Iterable[dict[str, str]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=['entry', 'request_type', 'country', 'wordbee_name', 'aem_name', 'aem_url'],
        lineterminator='\n',
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


# ---------- Main app ----------

def main() -> None:
    apply_style()

    st.markdown(
        '''
        <div class="hero">
            <h1>🏷️ Wordbee Name</h1>
            <p>Paste copied AEM row(s), enter the GTS ID, then generate Wordbee names, AEM names, URLs, and CSV output.</p>
            <div class="pills">
                <span class="pill">Marketing → AEM + countries</span>
                <span class="pill">Product → Wordbee only</span>
                <span class="pill">Multi-row paste</span>
                <span class="pill">CSV export</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="display:flex; justify-content:flex-end; margin-bottom: .85rem;">',
        unsafe_allow_html=True,
    )
    if st.button('Reset / Refresh', use_container_width=False):
        hard_refresh()
    st.markdown('</div>', unsafe_allow_html=True)

    with st.form('generator_form', clear_on_submit=False):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">1. Paste copied AEM row(s)</div>', unsafe_allow_html=True)
        pasted_text = st.text_area(
            'Paste copied AEM data',
            label_visibility='collapsed',
            placeholder='Paste the copied AEM row(s) here...',
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">2. Inputs</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([0.45, 0.55], vertical_alignment='top')
        with c1:
            gtsid = st.text_input('GTS ID', placeholder='GTS260059')
        with c2:
            request_types = st.multiselect('Request type', ['Marketing', 'Product'], default=['Marketing', 'Product'])
        marketing_selected = 'Marketing' in request_types
        product_selected = 'Product' in request_types

        country_labels: list[str] = []
        if marketing_selected:
            st.markdown('<div class="hint">Select one or more countries. Each selected country creates a separate AEM Name and AEM URL.</div>', unsafe_allow_html=True)
            country_labels = st.multiselect('AEM countries', COUNTRY_OPTIONS, default=['🇯🇵 ja-JP', '🇰🇷 ko-KR'])
        st.markdown('</div>', unsafe_allow_html=True)

        generate = st.form_submit_button('Generate', use_container_width=True)

    if not generate:
        return

    if not gtsid.strip():
        st.error('GTS ID is required.')
        return
    if not pasted_text.strip():
        st.error('Paste copied AEM row(s) first.')
        return
    if not request_types:
        st.error('Select Marketing, Product, or both.')
        return

    records = split_records(pasted_text)
    parsed = [parse_record(r) for r in records]

    for idx, item in enumerate(parsed, start=1):
        if not item.title_raw.strip():
            st.error(f'Could not detect a title in entry {idx}.')
            return
        if not item.owner_name.strip():
            st.error(f'Could not detect an owner name in entry {idx}.')
            return

    csv_rows: list[dict[str, str]] = []

    # Wordbee section
    wb_items: list[dict[str, str]] = []
    for idx, item in enumerate(parsed, start=1):
        if marketing_selected:
            wordbee = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'AEM')
            wb_items.append(
                {
                    'badge': 'Marketing',
                    'head': f'Entry {idx}: Wordbee Name',
                    'meta': f'{item.title_raw} · {item.owner_name}',
                    'value': wordbee,
                    'copy_value': wordbee,
                    'kind': 'light',
                }
            )
            csv_rows.append(
                {
                    'entry': str(idx),
                    'request_type': 'Marketing',
                    'country': '',
                    'wordbee_name': wordbee,
                    'aem_name': '',
                    'aem_url': '',
                }
            )
        if product_selected:
            wordbee = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'IRIS')
            wb_items.append(
                {
                    'badge': 'Product',
                    'head': f'Entry {idx}: Wordbee Name',
                    'meta': f'{item.title_raw} · {item.owner_name}',
                    'value': wordbee,
                    'copy_value': wordbee,
                    'kind': 'light',
                }
            )
            csv_rows.append(
                {
                    'entry': str(idx),
                    'request_type': 'Product',
                    'country': '',
                    'wordbee_name': wordbee,
                    'aem_name': '',
                    'aem_url': '',
                }
            )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    render_results('3. Wordbee names', wb_items)
    st.markdown('</div>', unsafe_allow_html=True)

    # Marketing section
    if marketing_selected:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        if not country_labels:
            st.markdown('<div class="section-title">4. AEM names + URLs</div>', unsafe_allow_html=True)
            st.markdown('<div class="empty-box">Select one or more countries to generate AEM names and URLs.</div>', unsafe_allow_html=True)
        else:
            for idx, item in enumerate(parsed, start=1):
                st.markdown(f'<div class="section-title">4. Entry {idx}: AEM names + URLs</div>', unsafe_allow_html=True)
                aem_items: list[dict[str, str]] = []
                url_items: list[dict[str, str]] = []
                for label in country_labels:
                    suffix = COUNTRY_TO_SUFFIX[label]
                    code = COUNTRY_TO_CODE[label]
                    flag = COUNTRY_TO_FLAG[label]
                    aem_name = build_aem_name(gtsid, item.owner_name, item.title_raw, suffix)
                    aem_url = build_aem_url(aem_name)
                    aem_items.append(
                        {
                            'badge': f'{flag} {code}',
                            'head': 'AEM Name',
                            'meta': item.title_raw,
                            'value': aem_name,
                            'copy_value': aem_name,
                            'kind': 'light',
                        }
                    )
                    url_items.append(
                        {
                            'badge': f'{flag} {code}',
                            'head': 'AEM URL',
                            'meta': item.title_raw,
                            'value': aem_url,
                            'copy_value': aem_url,
                            'kind': 'dark',
                        }
                    )
                    csv_rows.append(
                        {
                            'entry': str(idx),
                            'request_type': 'Marketing',
                            'country': code,
                            'wordbee_name': build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'AEM'),
                            'aem_name': aem_name,
                            'aem_url': aem_url,
                        }
                    )

                render_results('AEM Names', aem_items)
                render_results('AEM URLs', url_items)
        st.markdown('</div>', unsafe_allow_html=True)

    # CSV section
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">5. CSV export</div>', unsafe_allow_html=True)
    csv_data = build_csv(csv_rows)
    st.download_button(
        'Download CSV',
        data=csv_data.encode('utf-8'),
        file_name='wordbee_names.csv',
        mime='text/csv',
        use_container_width=False,
    )
    st.markdown(
        '<div class="csv-note">The CSV includes Wordbee names for Product and Marketing. Marketing rows also include country, AEM name, and AEM URL.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
