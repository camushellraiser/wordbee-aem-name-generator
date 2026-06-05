from __future__ import annotations

import html
import json
from typing import List, Sequence, Tuple

import streamlit as st
import streamlit.components.v1 as components

from core import build_aem_name, build_aem_url, build_wordbee_name, parse_projects

COUNTRIES: List[Tuple[str, str, str]] = [
    ("🇩🇪", "de-DE", "DE"),
    ("🇪🇸", "es-ES", "ES"),
    ("🇫🇷", "fr-FR", "FR"),
    ("🇯🇵", "ja-JP", "JP"),
    ("🇰🇷", "ko-KR", "KR"),
    ("🇨🇳", "zh-CN", "CN"),
    ("🇧🇷", "pt-BR", "BR"),
    ("🇹🇼", "zh-TW", "TW"),
]
COUNTRY_LABEL_TO_SUFFIX = {f"{flag} {code}": suffix for flag, code, suffix in COUNTRIES}

st.set_page_config(
    page_title="Wordbee Name",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def hard_refresh() -> None:
    st.session_state.clear()
    st.session_state["__refresh__"] = True
    st.rerun()


def style() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(99,102,241,0.16), transparent 26%),
                    radial-gradient(circle at top right, rgba(16,185,129,0.14), transparent 24%),
                    linear-gradient(180deg, #f7fbff 0%, #f3f6fb 100%);
            }
            [data-testid="stHeader"] { background: transparent; }
            .hero {
                padding: 1.3rem 1.4rem 1rem 1.4rem;
                border: 1px solid rgba(148,163,184,0.25);
                border-radius: 26px;
                background: rgba(255,255,255,0.84);
                box-shadow: 0 18px 60px rgba(15, 23, 42, 0.08);
                backdrop-filter: blur(12px);
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 2.15rem;
                line-height: 1.05;
                font-weight: 900;
                color: #0f172a;
            }
            .hero p {
                margin: 0.5rem 0 0 0;
                color: #475569;
                font-size: 1rem;
            }
            .pill-row { display:flex; flex-wrap:wrap; gap:0.45rem; margin-top:0.85rem; }
            .pill {
                display:inline-flex; align-items:center; gap:0.4rem;
                padding:0.35rem 0.72rem; border-radius:999px;
                background:#eef2ff; border:1px solid #c7d2fe;
                color:#3730a3; font-size:0.88rem; font-weight:700;
            }
            .section-card {
                padding: 1rem 1rem 0.95rem 1rem;
                border-radius: 22px;
                border: 1px solid rgba(148,163,184,0.24);
                background: rgba(255,255,255,0.92);
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
                margin-bottom: 0.9rem;
            }
            .section-title {
                display:flex; align-items:center; gap:0.55rem;
                font-size: 1.06rem; font-weight: 900; margin-bottom: 0.55rem; color: #0f172a;
            }
            .helper { color:#64748b; font-size:0.94rem; margin-top:-0.15rem; margin-bottom:0.7rem; }
            .copy-wrap {
                padding: 0.95rem; border-radius: 16px; border: 1px solid rgba(148,163,184,0.22);
                background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%); margin: 0.7rem 0;
            }
            .copy-label {
                font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase;
                color: #64748b; margin-bottom: 0.42rem; font-weight: 800;
            }
            .copy-value {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
                font-size: 0.95rem; word-break: break-word; padding: 0.78rem 0.85rem;
                background: #0f172a; color: #e2e8f0; border-radius: 12px; margin-bottom: 0.55rem; white-space: pre-wrap;
            }
            .copy-btn {
                appearance: none; border: none; border-radius: 999px;
                background: linear-gradient(90deg, #2563eb 0%, #4f46e5 100%);
                color: white; padding: 0.6rem 0.95rem; font-weight: 800; cursor: pointer;
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
            }
            .copy-btn.secondary { background: linear-gradient(90deg, #0f766e 0%, #059669 100%); }
            .chip-row { display:flex; flex-wrap:wrap; gap:0.35rem; margin: 0.35rem 0 0.15rem 0; }
            .chip {
                display:inline-flex; align-items:center; gap:0.35rem; border-radius:999px;
                padding:0.3rem 0.65rem; border:1px solid #dbe4f0; background:#f8fbff;
                color:#334155; font-size:0.82rem; font-weight:700;
            }
            .muted-box {
                padding: 1rem 1rem; border-radius: 16px; border: 1px dashed #cbd5e1;
                background: rgba(255,255,255,0.72); color: #475569;
            }
            .record-card {
                border-radius: 18px; border: 1px solid rgba(148,163,184,0.25);
                background: rgba(255,255,255,0.88); box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
                padding: 0.9rem 0.95rem; margin-bottom: 0.9rem;
            }
            .record-title {
                display:flex; flex-wrap:wrap; align-items:center; gap:0.5rem;
                margin-bottom:0.2rem; font-weight:800; color:#0f172a;
            }
            div[data-testid="stButton"] > button {
                border-radius: 999px; font-weight: 800; padding: 0.55rem 0.9rem;
            }
            div[data-testid="stTextArea"] textarea {
                min-height: 280px !important;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
                font-size: 0.94rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def copy_card(label: str, value: str, secondary: bool = False) -> None:
    label_html = html.escape(label)
    value_html = html.escape(value)
    value_safe = json.dumps(value)
    secondary_class = " secondary" if secondary else ""
    components.html(
        f"""
        <div class="copy-wrap">
          <div class="copy-label">{label_html}</div>
          <div class="copy-value">{value_html}</div>
          <button class="copy-btn{secondary_class}" onclick="navigator.clipboard.writeText({value_safe}).then(() => this.innerText='Copied!');">
            Copy
          </button>
        </div>
        """,
        height=175,
    )


def copy_all_card(label: str, values: Sequence[str]) -> None:
    joined = "\n".join(values)
    label_html = html.escape(label)
    joined_html = html.escape(joined)
    values_safe = json.dumps(joined)
    components.html(
        f"""
        <div class="copy-wrap">
          <div class="copy-label">{label_html}</div>
          <div class="copy-value" style="white-space:pre-wrap;">{joined_html}</div>
          <button class="copy-btn secondary" onclick="navigator.clipboard.writeText({values_safe}).then(() => this.innerText='Copied all!');">
            Copy all
          </button>
        </div>
        """,
        height=max(170, 120 + 28 * max(1, len(values))),
    )


def render_flags(selected_labels: Sequence[str]) -> str:
    return " ".join(selected_labels)


def main() -> None:
    style()

    if st.session_state.get("__refresh__"):
        st.session_state["__refresh__"] = False
        components.html("<script>window.top.location.reload();</script>", height=0)
        st.stop()

    st.markdown(
        """
        <div class="hero">
            <h1>🏷️ Wordbee Name</h1>
            <p>Paste copied AEM rows once, then generate Wordbee names, AEM names, and AEM URLs in one clean Streamlit workflow.</p>
            <div class="pill-row">
                <span class="pill">Paste copied AEM rows</span>
                <span class="pill">Marketing → AEM + URLs</span>
                <span class="pill">Product → Wordbee only</span>
                <span class="pill">Multiple rows at once</span>
                <span class="pill">Hard refresh reset</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, top_right = st.columns([0.82, 0.18], vertical_alignment="center")
    with top_right:
        if st.button("Reset / Refresh", use_container_width=True):
            hard_refresh()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">1. Paste copied AEM row(s)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Copy the whole selected row or rows from AEM and paste here. Tabs, wrapped lines, or multiple selected rows are all supported.</div>',
        unsafe_allow_html=True,
    )

    pasted_text = st.text_area(
        "Paste copied AEM content",
        placeholder=(
            "Example copied from AEM:\n"
            "GTS260059_Web_PMantha_VDS-Avizo-Geology_AEM\t229137\tThermo Fisher Pratyusha Mantha\n"
            "GTS260060_Web_ICao_Rainbow-NPI_AEM_PDP\t230815\tThermo Fisher Ivy Cao"
        ),
        label_visibility="collapsed",
        height=280,
        key="pasted_text",
    )

    request_types = st.multiselect(
        "Request type",
        options=["Marketing", "Product"],
        default=["Marketing"],
        help="Select one or both. Marketing enables country-based AEM outputs; Product generates Wordbee names only.",
    )

    marketing_selected = "Marketing" in request_types
    product_selected = "Product" in request_types

    country_labels: List[str] = []
    if marketing_selected:
        st.markdown(
            '<div class="helper">Choose one or more countries. Each selected country creates a separate AEM Name and AEM URL.</div>',
            unsafe_allow_html=True,
        )
        country_labels = st.multiselect(
            "AEM countries",
            options=[f"{flag} {code}" for flag, code, _ in COUNTRIES],
            default=[],
            help="Multi-select supported.",
        )

    st.markdown('</div>', unsafe_allow_html=True)

    parsed_projects = parse_projects(pasted_text)

    if not pasted_text.strip():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">2. Ready to parse</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="muted-box">Paste one or more copied AEM rows above. The tool will detect the reference automatically and use the copied row data to generate the naming outputs.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if not parsed_projects:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">2. No reference detected</div>', unsafe_allow_html=True)
        st.warning(
            "I could not find a project reference in the pasted text. Paste the row that contains something like GTS260059_Web_PMantha_VDS-Avizo-Geology_AEM."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">2. Parsed entries</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="helper">Detected {len(parsed_projects)} reference' + ("s" if len(parsed_projects) != 1 else "") + ' from your paste.</div>',
        unsafe_allow_html=True,
    )
    for idx, project in enumerate(parsed_projects, start=1):
        with st.expander(f"Entry {idx}: {project.reference}", expanded=(len(parsed_projects) == 1)):
            st.markdown(
                f"""
                <div class="chip-row">
                    <span class="chip">GTS ID: {html.escape(project.gtsid)}</span>
                    <span class="chip">Owner token: {html.escape(project.owner_token)}</span>
                    <span class="chip">Title: {html.escape(project.title_raw)}</span>
                    <span class="chip">Source system: {html.escape(project.source_system)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            copy_card("Detected reference", project.reference, secondary=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">3. Wordbee Name</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Marketing generates the AEM-suffixed Wordbee Name. Product generates the IRIS-suffixed Wordbee Name. If both are selected, both versions are shown.</div>',
        unsafe_allow_html=True,
    )

    all_wordbee_names: List[str] = []
    for idx, project in enumerate(parsed_projects, start=1):
        st.markdown(
            f'<div class="record-card"><div class="record-title">{html.escape(project.reference)}</div>',
            unsafe_allow_html=True,
        )
        if marketing_selected:
            marketing_name = build_wordbee_name(project.gtsid, project.owner_token, project.title_raw, "AEM")
            all_wordbee_names.append(marketing_name)
            copy_card(f"Wordbee Name — Marketing #{idx}", marketing_name)
        if product_selected:
            product_name = build_wordbee_name(project.gtsid, project.owner_token, project.title_raw, "IRIS")
            all_wordbee_names.append(product_name)
            copy_card(f"Wordbee Name — Product #{idx}", product_name)
        st.markdown('</div>', unsafe_allow_html=True)

    if all_wordbee_names:
        copy_all_card("Copy all Wordbee names", all_wordbee_names)
    st.markdown('</div>', unsafe_allow_html=True)

    if marketing_selected:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">4. AEM Name</div>', unsafe_allow_html=True)
        if country_labels:
            st.markdown(
                f'<div class="helper">Countries selected: {render_flags(country_labels)}</div>',
                unsafe_allow_html=True,
            )
            all_aem_names: List[str] = []
            all_aem_urls: List[str] = []

            for idx, project in enumerate(parsed_projects, start=1):
                with st.expander(f"Generate AEM outputs for entry {idx}", expanded=(len(parsed_projects) == 1)):
                    st.markdown(
                        f'<div class="record-card"><div class="record-title">{html.escape(project.reference)}</div>',
                        unsafe_allow_html=True,
                    )
                    per_entry_names: List[str] = []
                    per_entry_urls: List[str] = []
                    for label in country_labels:
                        suffix = COUNTRY_LABEL_TO_SUFFIX[label]
                        aem_name = build_aem_name(project.gtsid, project.owner_token, project.title_raw, suffix)
                        aem_url = build_aem_url(aem_name)
                        per_entry_names.append(aem_name)
                        per_entry_urls.append(aem_url)
                        all_aem_names.append(aem_name)
                        all_aem_urls.append(aem_url)

                        st.markdown(f'<div class="chip-row"><span class="chip">{html.escape(label)}</span></div>', unsafe_allow_html=True)
                        copy_card(f"AEM Name — {label}", aem_name, secondary=True)
                        copy_card(f"AEM URL — {label}", aem_url)

                    if len(country_labels) > 1:
                        copy_all_card(f"Copy all AEM names for entry {idx}", per_entry_names)
                        copy_all_card(f"Copy all AEM URLs for entry {idx}", per_entry_urls)
                    st.markdown('</div>', unsafe_allow_html=True)

            if len(all_aem_names) > 1:
                copy_all_card("Copy all AEM names", all_aem_names)
                copy_all_card("Copy all AEM URLs", all_aem_urls)
        else:
            st.markdown(
                '<div class="muted-box">Select one or more countries to generate AEM Names and AEM URLs.</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    elif product_selected:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">4. AEM Name</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="muted-box">Product-only requests do not generate AEM Names or AEM URLs.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
