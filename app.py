from __future__ import annotations

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

st.set_page_config(page_title='Wordbee Name', page_icon='🏷️', layout='wide', initial_sidebar_state='collapsed')


def hard_refresh() -> None:
    st.session_state.clear()
    st.rerun()


def style() -> None:
    st.markdown(
        '''
        <style>
            .stApp { background: linear-gradient(180deg, #f7fbff 0%, #eef4fb 100%); }
            [data-testid="stHeader"] { background: transparent; }
            .hero {
                padding: 1.25rem 1.35rem;
                border-radius: 24px;
                background: rgba(255,255,255,0.92);
                border: 1px solid rgba(148,163,184,0.25);
                box-shadow: 0 16px 48px rgba(15,23,42,0.08);
                margin-bottom: 1rem;
            }
            .hero h1 { margin: 0; font-size: 2rem; font-weight: 900; }
            .hero p { margin: .45rem 0 0 0; color: #475569; }
            .section { padding: 1rem; border-radius: 20px; background: rgba(255,255,255,.95); border: 1px solid rgba(148,163,184,.22); margin-bottom: .9rem; }
            .section-title { font-size: 1.02rem; font-weight: 900; margin-bottom: .5rem; }
            .helper { color: #64748b; margin-bottom: .75rem; }
            .card { padding: .9rem; border-radius: 16px; background: #fff; border: 1px solid #dbe4f0; margin: .65rem 0; }
            .label { font-size: .78rem; text-transform: uppercase; color: #64748b; font-weight: 800; margin-bottom: .35rem; }
            .value { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e2e8f0; padding: .75rem .85rem; border-radius: 12px; }
            .copy-btn { margin-top: .5rem; border: none; border-radius: 999px; padding: .5rem .85rem; font-weight: 800; background: linear-gradient(90deg, #2563eb, #4f46e5); color: white; cursor: pointer; }
            .copy-btn.secondary { background: linear-gradient(90deg, #0f766e, #059669); }
            div[data-testid="stTextArea"] textarea { min-height: 220px !important; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
            div[data-testid="stButton"] > button { border-radius: 999px; font-weight: 800; }
        </style>
        ''', unsafe_allow_html=True,
    )


def copy_card(label: str, value: str, secondary: bool = False) -> None:
    safe_value = json.dumps(value)
    label_html = html.escape(label)
    value_html = html.escape(value)
    secondary_class = ' secondary' if secondary else ''
    components.html(
        f'''
        <div class="card">
          <div class="label">{label_html}</div>
          <div class="value">{value_html}</div>
          <button class="copy-btn{secondary_class}" onclick="navigator.clipboard.writeText({safe_value}).then(()=>this.textContent='Copied!');">Copy</button>
        </div>
        ''',
        height=190,
    )


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

    with st.form('generator_form'):
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">1. Paste copied AEM row(s)</div>', unsafe_allow_html=True)
        st.markdown('<div class="helper">Paste the copied text from AEM. Tabs, wrapped lines, and multiple rows are supported.</div>', unsafe_allow_html=True)
        pasted_text = st.text_area('Paste copied AEM content', label_visibility='collapsed', placeholder='Paste AEM text here...')

        gtsid = st.text_input('GTS ID', placeholder='GTS260059')
        request_types = st.multiselect('Request type', ['Marketing', 'Product'], default=['Marketing', 'Product'])
        marketing_selected = 'Marketing' in request_types
        product_selected = 'Product' in request_types
        country_labels: List[str] = []
        if marketing_selected:
            country_labels = st.multiselect('AEM countries', [f'{flag} {code}' for flag, code, _ in COUNTRIES])

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
    for idx, item in enumerate(parsed, start=1):
        st.markdown(f'<div class="helper"><b>Entry {idx}:</b> {html.escape(item.title_raw)}</div>', unsafe_allow_html=True)
        if item.reference:
            st.caption(item.reference)
        st.caption(f'Owner detected: {item.owner_name}')
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">3. Wordbee Name</div>', unsafe_allow_html=True)
    all_wordbee: List[str] = []
    for item in parsed:
        if marketing_selected:
            wb = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'AEM')
            all_wordbee.append(wb)
            copy_card(f'Wordbee Name — {item.title_raw} (Marketing)', wb)
        if product_selected:
            wb = build_wordbee_name(gtsid, item.owner_name, item.title_raw, 'IRIS')
            all_wordbee.append(wb)
            copy_card(f'Wordbee Name — {item.title_raw} (Product)', wb)
    if all_wordbee:
        copy_card('Copy all Wordbee names', '\n'.join(all_wordbee), secondary=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if marketing_selected:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">4. AEM Name + URL</div>', unsafe_allow_html=True)
        if not country_labels:
            st.info('Select one or more countries to generate AEM Names and URLs.')
        else:
            all_names: List[str] = []
            all_urls: List[str] = []
            for item in parsed:
                for label in country_labels:
                    suffix = COUNTRY_TO_SUFFIX[label]
                    aem_name = build_aem_name(gtsid, item.owner_name, item.title_raw, suffix)
                    aem_url = build_aem_url(aem_name)
                    all_names.append(aem_name)
                    all_urls.append(aem_url)
                    st.markdown(f'**{label}**', unsafe_allow_html=False)
                    copy_card('AEM Name', aem_name, secondary=True)
                    copy_card('AEM URL', aem_url)
            if len(all_names) > 1:
                copy_card('Copy all AEM names', '\n'.join(all_names), secondary=True)
                copy_card('Copy all AEM URLs', '\n'.join(all_urls))
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
