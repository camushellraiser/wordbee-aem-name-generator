from __future__ import annotations

import base64
import csv
import html
import io
from typing import List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from core import build_aem_name, build_aem_url, build_wordbee_name, parse_record, split_records

COUNTRIES: List[Tuple[str, str, str]] = [
    ('🇩🇪', 'de-DE', 'DE'),
    ('🇪🇸', 'es-ES', 'ES'),
    ('🇫🇷', 'fr-FR', 'FR'),
    ('🇯🇵', 'ja-JP', 'JP'),
    ('🇰🇷', 'ko-KR', 'KR'),
    ('🇨🇳', 'zh-CN', 'CN'),
    ('🇧🇷', 'pt-BR', 'BR'),
    ('🇹🇼', 'zh-TW', 'TW'),
]
COUNTRY_TO_SUFFIX = {f'{flag} {code}': suffix for flag, code, suffix in COUNTRIES}
COUNTRY_OPTIONS = [f'{flag} {code}' for flag, code, _ in COUNTRIES]

st.set_page_config(
    page_title='Wordbee Name',
    page_icon='🏷️',
    layout='wide',
    initial_sidebar_state='collapsed',
)


def hard_refresh() -> None:
    st.session_state.clear()
    st.rerun()


def style() -> None:
    st.markdown(
        '''
        <style>
            :root {
                --bg0: #f6f8fc;
                --bg1: #eef3fb;
                --card: rgba(255,255,255,.92);
                --border: rgba(148,163,184,.22);
                --text: #0f172a;
                --muted: #55657a;
                --accent: #4f46e5;
                --accent2: #2563eb;
                --soft: #eff6ff;
            }

            html, body, [class*="st"], p, div, span, label, input, textarea, button, select {
                font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
            }

            .stApp {
                background: radial-gradient(circle at top left, #ffffff 0%, var(--bg0) 36%, var(--bg1) 100%);
                color: var(--text);
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            .hero {
                padding: 1.35rem 1.45rem 1.15rem;
                border-radius: 28px;
                background: var(--card);
                border: 1px solid var(--border);
                box-shadow: 0 18px 55px rgba(15,23,42,.08);
                margin-bottom: 1rem;
            }

            .hero h1 {
                margin: 0;
                font-size: 2rem;
                line-height: 1.05;
                font-weight: 900;
                letter-spacing: -0.03em;
            }

            .hero p {
                margin: .45rem 0 0;
                color: var(--muted);
                font-size: 1rem;
            }

            .pills {
                display: flex;
                gap: .55rem;
                flex-wrap: wrap;
                margin-top: .9rem;
            }

            .pill {
                padding: .48rem .78rem;
                border-radius: 999px;
                border: 1px solid rgba(99,102,241,.24);
                background: linear-gradient(180deg, #fff, #f8faff);
                color: #3730a3;
                font-size: .86rem;
                font-weight: 800;
            }

            .section {
                padding: 1rem 1rem 1.1rem;
                border-radius: 24px;
                background: var(--card);
                border: 1px solid var(--border);
                box-shadow: 0 12px 28px rgba(15,23,42,.05);
                margin-bottom: .95rem;
            }

            .section-title {
                font-size: 1.02rem;
                font-weight: 900;
                letter-spacing: -0.02em;
                margin-bottom: .55rem;
            }

            .subtle {
                color: var(--muted);
                margin-bottom: .7rem;
            }

            .result-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
                gap: 14px;
            }

            .result-card {
                padding: 14px 14px 12px;
                border-radius: 20px;
                background: linear-gradient(180deg, #fff, #fbfcff);
                border: 1px solid #dbe4f0;
                box-shadow: 0 10px 24px rgba(15,23,42,.05);
            }

            .label {
                font-size: .74rem;
                text-transform: uppercase;
                color: #64748b;
                font-weight: 900;
                letter-spacing: .05em;
                margin-bottom: .4rem;
            }

            .subhead {
                font-size: .88rem;
                color: #475569;
                margin-bottom: .55rem;
                font-weight: 700;
            }

            .value {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                white-space: pre-wrap;
                word-break: break-word;
                background: #0f172a;
                color: #e2e8f0;
                padding: .82rem .92rem;
                border-radius: 14px;
                line-height: 1.42;
                font-size: .92rem;
            }

            .copy-btn {
                margin-top: .58rem;
                border: none;
                border-radius: 999px;
                padding: .5rem .92rem;
                font-weight: 800;
                font-size: .84rem;
                background: linear-gradient(90deg, #2563eb, #4f46e5);
                color: white;
                cursor: pointer;
            }

            .copy-btn.secondary {
                background: linear-gradient(90deg, #0f766e, #059669);
            }

            .copy-btn:active {
                transform: translateY(1px);
            }

            div[data-testid="stTextArea"] textarea {
                min-height: 235px !important;
                border-radius: 18px !important;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
                font-size: .95rem !important;
                line-height: 1.45 !important;
            }

            div[data-testid="stButton"] > button,
            div[data-testid="stDownloadButton"] > button {
                border-radius: 999px;
                font-weight: 800;
            }

            .empty-box {
                padding: .95rem 1rem;
                border-radius: 16px;
                background: #f8fafc;
                border: 1px dashed #cbd5e1;
                color: #475569;
            }

            .csv-note {
                color: #64748b;
                font-size: .9rem;
                margin-top: .45rem;
            }
        </style>
        ''',
        unsafe_allow_html=True,
    )


def copy_card(label: str, value: str, secondary: bool = False, sublabel: str | None = None) -> None:
    encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')
    label_html = html.escape(label)
    sublabel_html = f'<div class="subhead">{html.escape(sublabel)}</div>' if sublabel else ''
    value_html = html.escape(value)
    secondary_class = ' secondary' if secondary else ''
    components.html(
        f'''
        <div class="result-card">
          <div class="label">{label_html}</div>
          {sublabel_html}
          <div class="value">{value_html}</div>
          <button class="copy-btn{secondary_class}" data-copy-b64="{encoded}" onclick="navigator.clipboard.writeText(atob(this.dataset.copyB64)).then(() => {{ const old = this.textContent; this.textContent = 'Copied!'; setTimeout(() => this.textContent = old, 900); }});">Copy</button>
        </div>
        ''',
        height=222,
    )


def render_group(title: str, cards: List[Tuple[str, str, bool, str | None]]) -> None:
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="result-grid">', unsafe_allow_html=True)
    for label, value, secondary, sublabel in cards:
        copy_card(label, value, secondary=secondary, sublabel=sublabel)
    st.markdown('</div>', unsafe_allow_html=True)


def build_csv(rows: List[dict[str, str]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=['entry', 'request_type', 'country', 'wordbee_name', 'aem_name', 'aem_url'],
        lineterminator='\n',
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def main() -> None:
    style()

    st.markdown(
        '''
        <div class="hero">
            <h1>🏷️ Wordbee Name</h1>
            <p>Paste copied AEM row(s), enter the GTS ID, then generate Wordbee names, AEM names, URLs, and CSV output.</p>
            <div class="pills">
                <span class="pill">Marketing → AEM + countries</span>
                <span class="pill">Product → Wordbee only</span>
                <span class="pill">Multi-country selection</span>
                <span class="pill">CSV export</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.78, 0.22], vertical_alignment='center')
    with right:
        if st.button('Reset / Refresh', use_container_width=True):
            hard_refresh()

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">1. Paste copied AEM row(s)</div>', unsafe_allow_html=True)

    with st.form('generator_form'):
        pasted_text = st.text_area('Paste copied AEM content', label_visibility='collapsed', placeholder='Paste AEM text here...')
        gtsid = st.text_input('GTS ID', placeholder='GTS260059')
        request_types = st.multiselect('Request type', ['Marketing', 'Product'], default=['Marketing', 'Product'])
        marketing_selected = 'Marketing' in request_types
        product_selected = 'Product' in request_types
        country_labels: List[str] = []
        if marketing_selected:
            country_labels = st.multiselect('AEM countries', COUNTRY_OPTIONS)
        generate = st.form_submit_button('Generate', use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not generate:
        return

    if not gtsid.strip():
        st.error('GTS ID is required.')
        return
    if not pasted_text.strip():
        st.error('Paste copied AEM row(s) first.')
        return

    records = split_records(pasted_text)
    parsed = [parse_record(r) for r in records]

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">2. Parsed entries</div>', unsafe_allow_html=True)
    st.markdown('<div class="result-grid">', unsafe_allow_html=True)
    for idx, item in enumerate(parsed, start=1):
        details = f'Owner detected: {item.owner_name}'
        if item.reference:
            details = f'{details}\nReference: {item.reference}'
        copy_card('Parsed row', item.raw_text.strip(), secondary=True, sublabel=f'Entry {idx}: {item.title_raw} | {details}')
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    csv_rows: List[dict[str, str]] = []

    wordbee_cards: List[Tuple[str, str, bool, str | None]] = []
    for entry_idx, item in enumerate(parsed, start=1):
        if marketing_selected:
            wb = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'AEM')
            wordbee_cards.append((f'Wordbee Name — {item.title_raw}', wb, False, 'Marketing / AEM'))
            csv_rows.append(
                {
                    'entry': str(entry_idx),
                    'request_type': 'Marketing',
                    'country': '',
                    'wordbee_name': wb,
                    'aem_name': '',
                    'aem_url': '',
                }
            )
        if product_selected:
            wb = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'IRIS')
            wordbee_cards.append((f'Wordbee Name — {item.title_raw}', wb, False, 'Product / IRIS'))
            csv_rows.append(
                {
                    'entry': str(entry_idx),
                    'request_type': 'Product',
                    'country': '',
                    'wordbee_name': wb,
                    'aem_name': '',
                    'aem_url': '',
                }
            )

    if wordbee_cards:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        render_group('3. Wordbee Name', wordbee_cards)
        st.markdown('</div>', unsafe_allow_html=True)

    if marketing_selected:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">4. AEM Name + URL</div>', unsafe_allow_html=True)
        if not country_labels:
            st.markdown('<div class="empty-box">Select one or more countries to generate AEM Names and URLs.</div>', unsafe_allow_html=True)
        else:
            aem_cards: List[Tuple[str, str, bool, str | None]] = []
            url_cards: List[Tuple[str, str, bool, str | None]] = []
            for entry_idx, item in enumerate(parsed, start=1):
                for label in country_labels:
                    suffix = COUNTRY_TO_SUFFIX[label]
                    aem_name = build_aem_name(gtsid, item.owner_name, item.title_raw, suffix)
                    aem_url = build_aem_url(aem_name)
                    aem_cards.append((f'AEM Name — {label}', aem_name, True, item.title_raw))
                    url_cards.append((f'AEM URL — {label}', aem_url, True, item.title_raw))
                    csv_rows.append(
                        {
                            'entry': str(entry_idx),
                            'request_type': 'Marketing',
                            'country': label,
                            'wordbee_name': build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'AEM'),
                            'aem_name': aem_name,
                            'aem_url': aem_url,
                        }
                    )
            render_group('AEM Names', aem_cards)
            render_group('AEM URLs', url_cards)
        st.markdown('</div>', unsafe_allow_html=True)

    if csv_rows:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">5. CSV export</div>', unsafe_allow_html=True)
        csv_text = build_csv(csv_rows)
        st.download_button(
            'Download CSV',
            data=csv_text.encode('utf-8'),
            file_name='wordbee_names.csv',
            mime='text/csv',
            use_container_width=False,
        )
        st.markdown('<div class="csv-note">Includes Wordbee names for Product and Marketing. Marketing rows also include country, AEM name, and AEM URL.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
