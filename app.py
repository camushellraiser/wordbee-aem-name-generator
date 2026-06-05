from __future__ import annotations

import base64
import html
import json
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
            .stApp {
                background: linear-gradient(180deg, #f7fbff 0%, #eef4fb 100%);
            }
            [data-testid="stHeader"] {
                background: transparent;
            }
            .hero {
                padding: 1.25rem 1.35rem;
                border-radius: 24px;
                background: rgba(255,255,255,0.92);
                border: 1px solid rgba(148,163,184,0.25);
                box-shadow: 0 16px 48px rgba(15,23,42,0.08);
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 2rem;
                font-weight: 900;
            }
            .hero p {
                margin: .45rem 0 0 0;
                color: #475569;
            }
            .section {
                padding: 1rem;
                border-radius: 20px;
                background: rgba(255,255,255,.95);
                border: 1px solid rgba(148,163,184,.22);
                margin-bottom: .9rem;
            }
            .section-title {
                font-size: 1.02rem;
                font-weight: 900;
                margin-bottom: .35rem;
            }
            .helper {
                color: #64748b;
                margin-bottom: .75rem;
            }
            .result-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
                gap: 14px;
            }
            .result-card {
                padding: 14px 14px 12px 14px;
                border-radius: 18px;
                background: #fff;
                border: 1px solid #dbe4f0;
                box-shadow: 0 10px 28px rgba(15,23,42,0.06);
            }
            .result-card.compact {
                padding-bottom: 10px;
            }
            .label {
                font-size: .78rem;
                text-transform: uppercase;
                color: #64748b;
                font-weight: 800;
                margin-bottom: .45rem;
                letter-spacing: .03em;
            }
            .subhead {
                font-size: .86rem;
                color: #475569;
                margin-bottom: .5rem;
                font-weight: 700;
            }
            .value {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                white-space: pre-wrap;
                word-break: break-word;
                background: #0f172a;
                color: #e2e8f0;
                padding: .78rem .9rem;
                border-radius: 12px;
                line-height: 1.35;
            }
            .copy-btn {
                margin-top: .55rem;
                border: none;
                border-radius: 999px;
                padding: .48rem .9rem;
                font-weight: 800;
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
                min-height: 240px !important;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            }
            div[data-testid="stButton"] > button {
                border-radius: 999px;
                font-weight: 800;
            }
            .empty-box {
                padding: 1rem 1.1rem;
                border-radius: 14px;
                background: #f8fafc;
                border: 1px dashed #cbd5e1;
                color: #475569;
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
        <div class="result-card compact">
          <div class="label">{label_html}</div>
          {sublabel_html}
          <div class="value">{value_html}</div>
          <button class="copy-btn{secondary_class}" data-copy-b64="{encoded}" onclick="navigator.clipboard.writeText(atob(this.dataset.copyB64)).then(() => {{ const old = this.textContent; this.textContent = 'Copied!'; setTimeout(() => this.textContent = old, 900); }});">Copy</button>
        </div>
        ''',
        height=168,
    )


def render_group(title: str, cards: List[Tuple[str, str, bool, str | None]]) -> None:
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="result-grid">', unsafe_allow_html=True)
    for label, value, secondary, sublabel in cards:
        copy_card(label, value, secondary=secondary, sublabel=sublabel)
    st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    style()

    st.markdown(
        '''
        <div class="hero">
            <h1>🏷️ Wordbee Name</h1>
            <p>Paste copied AEM row(s), enter the GTS ID, then generate Wordbee names, AEM names, and URLs.</p>
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
    st.markdown('<div class="helper">Copy the row or rows from AEM and paste here. Tabs, wrapped lines, and multiple rows are all supported.</div>', unsafe_allow_html=True)

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
        title = f'Entry {idx}: {item.title_raw}'
        details = f'Owner detected: {item.owner_name}'
        if item.reference:
            details = f'{details}\nReference: {item.reference}'
        copy_card('Parsed row', item.raw_text.strip(), secondary=True, sublabel=f'{title} | {details}')
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    wordbee_cards: List[Tuple[str, str, bool, str | None]] = []
    for item in parsed:
        if marketing_selected:
            wb = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'AEM')
            wordbee_cards.append((f'Wordbee Name — {item.title_raw}', wb, False, 'Marketing / AEM'))
        if product_selected:
            wb = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'IRIS')
            wordbee_cards.append((f'Wordbee Name — {item.title_raw}', wb, False, 'Product / IRIS'))

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
            for item in parsed:
                for label in country_labels:
                    suffix = COUNTRY_TO_SUFFIX[label]
                    aem_name = build_aem_name(gtsid, item.owner_name, item.title_raw, suffix)
                    aem_url = build_aem_url(aem_name)
                    aem_cards.append((f'AEM Name — {label}', aem_name, True, item.title_raw))
                    url_cards.append((f'AEM URL — {label}', aem_url, True, item.title_raw))
            render_group('AEM Names', aem_cards)
            render_group('AEM URLs', url_cards)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
