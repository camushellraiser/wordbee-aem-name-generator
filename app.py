import json
import re
from typing import Dict, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

BASE_URL = (
    "https://author-prod-use1.aemprod.thermofisher.net/"
    "projects/details.html/content/projects/"
)

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

COUNTRY_LABEL_TO_SUFFIX: Dict[str, str] = {
    f"{flag} {code}": suffix for flag, code, suffix in COUNTRIES
}

st.set_page_config(
    page_title="Wordbee Name",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def hard_reset() -> None:
    """Clear Streamlit state and trigger a browser reload."""
    for key in list(st.session_state.keys()):
        if key != "__hard_reset__":
            del st.session_state[key]
    st.session_state["__hard_reset__"] = True
    st.rerun()


def page_style() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(59,130,246,0.15), transparent 25%),
                    radial-gradient(circle at top right, rgba(16,185,129,0.14), transparent 22%),
                    linear-gradient(180deg, #f8fbff 0%, #f5f7fb 100%);
            }
            [data-testid="stHeader"] {
                background: transparent;
            }
            .hero {
                padding: 1.3rem 1.25rem 1rem 1.25rem;
                border: 1px solid rgba(148,163,184,0.25);
                border-radius: 24px;
                background: rgba(255,255,255,0.8);
                box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
                backdrop-filter: blur(10px);
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 2.15rem;
                line-height: 1.1;
            }
            .hero p {
                margin: 0.45rem 0 0 0;
                color: #475569;
                font-size: 1.02rem;
            }
            .pill-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                margin-top: 0.85rem;
            }
            .pill {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: #eef2ff;
                border: 1px solid #c7d2fe;
                color: #3730a3;
                font-size: 0.9rem;
                font-weight: 600;
            }
            .section-card {
                padding: 1rem 1rem 0.9rem 1rem;
                border-radius: 20px;
                border: 1px solid rgba(148,163,184,0.28);
                background: rgba(255,255,255,0.9);
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
                margin-bottom: 0.9rem;
            }
            .section-title {
                display:flex;
                align-items:center;
                gap:0.5rem;
                font-size: 1.1rem;
                font-weight: 800;
                margin-bottom: 0.7rem;
                color: #0f172a;
            }
            .helper {
                color: #64748b;
                font-size: 0.93rem;
                margin-top: -0.15rem;
                margin-bottom: 0.65rem;
            }
            .copy-wrap {
                padding: 0.95rem;
                border-radius: 16px;
                border: 1px solid rgba(148,163,184,0.22);
                background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
                margin: 0.65rem 0;
            }
            .copy-label {
                font-size: 0.82rem;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: #64748b;
                margin-bottom: 0.45rem;
                font-weight: 700;
            }
            .copy-value {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
                font-size: 0.95rem;
                word-break: break-word;
                padding: 0.75rem 0.8rem;
                background: #0f172a;
                color: #e2e8f0;
                border-radius: 12px;
                margin-bottom: 0.55rem;
                white-space: pre-wrap;
            }
            .copy-btn {
                appearance: none;
                border: none;
                border-radius: 999px;
                background: linear-gradient(90deg, #2563eb 0%, #4f46e5 100%);
                color: white;
                padding: 0.6rem 0.95rem;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
            }
            .copy-btn.secondary {
                background: linear-gradient(90deg, #0f766e 0%, #059669 100%);
            }
            .status-chip {
                display:inline-flex;
                padding:0.28rem 0.62rem;
                border-radius:999px;
                background:#ecfeff;
                border:1px solid #a5f3fc;
                color:#155e75;
                font-weight:700;
                font-size:0.82rem;
                margin-right:0.35rem;
            }
            .muted-box {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border: 1px dashed #cbd5e1;
                background: rgba(255,255,255,0.7);
                color: #475569;
            }
            div[data-testid="stButton"] > button {
                border-radius: 999px;
                font-weight: 700;
                padding: 0.55rem 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_owner(name: str) -> Tuple[str, str, str]:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if len(parts) < 2:
        raise ValueError("Owner name must include at least first name and last name.")
    first = parts[0]
    last = parts[-1]
    initial = re.sub(r"[^A-Za-z0-9]", "", first[:1]).upper()
    last_clean = re.sub(r"\s+", "", last).strip()
    if not last_clean:
        raise ValueError("Owner name last name is empty.")
    last_clean = last_clean[:1].upper() + last_clean[1:]
    return initial, last_clean, f"{initial}{last_clean}"


def build_wordbee_name(gtsid: str, owner_name: str, title: str, system: str) -> str:
    initial, last_name, owner_token = normalize_owner(owner_name)
    _ = initial, last_name  # keep helper explicit
    title = title.strip()
    return f"{gtsid.strip()}_Web_{owner_token}_{title}_{system}"


def build_aem_name(gtsid: str, owner_name: str, title: str, country_suffix: str) -> str:
    initial, last_name, owner_token = normalize_owner(owner_name)
    _ = initial, last_name
    title = title.strip()
    return f"{gtsid.strip()}_Web_{owner_token}_{title}_{country_suffix}"


def build_aem_url(aem_name: str) -> str:
    slug = aem_name.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9_-]", "", slug)
    return f"{BASE_URL}{slug}"


def copy_card(label: str, value: str, secondary: bool = False) -> None:
    label_safe = json.dumps(label)
    value_safe = json.dumps(value)
    secondary_class = " secondary" if secondary else ""
    components.html(
        f"""
        <div class="copy-wrap">
          <div class="copy-label">{label_safe}</div>
          <div class="copy-value" id="value">{value_safe[1:-1]}</div>
          <button class="copy-btn{secondary_class}" onclick="navigator.clipboard.writeText({value_safe}).then(() => this.innerText='Copied!');">
            Copy
          </button>
        </div>
        """,
        height=170,
    )


def copy_all_card(label: str, values: List[str]) -> None:
    joined = "\n".join(values)
    label_safe = json.dumps(label)
    values_safe = json.dumps(joined)
    components.html(
        f"""
        <div class="copy-wrap">
          <div class="copy-label">{label_safe}</div>
          <div class="copy-value" style="white-space:pre-wrap;">{joined}</div>
          <button class="copy-btn secondary" onclick="navigator.clipboard.writeText({values_safe}).then(() => this.innerText='Copied all!');">
            Copy all
          </button>
        </div>
        """,
        height=max(170, 120 + 30 * len(values)),
    )


def main() -> None:
    page_style()

    if st.session_state.get("__hard_reset__"):
        st.session_state["__hard_reset__"] = False
        components.html("<script>window.top.location.reload();</script>", height=0)
        st.stop()

    st.markdown(
        """
        <div class="hero">
            <h1>🏷️ Wordbee Name</h1>
            <p>Generate Wordbee names, AEM names, and AEM project URLs from one clean Streamlit workflow.</p>
            <div class="pill-row">
                <span class="pill">Marketing → AEM + country names</span>
                <span class="pill">Product → Wordbee only</span>
                <span class="pill">Multi-country selection</span>
                <span class="pill">Hard reset refresh</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([0.82, 0.18], vertical_alignment="center")
    with top_right:
        if st.button("Reset / Refresh", use_container_width=True):
            st.session_state["__hard_reset__"] = True
            st.rerun()

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>1. Input details</div>", unsafe_allow_html=True)
    st.markdown("<div class='helper'>Fill in the values coming from AEM or your source table.</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        gtsid = st.text_input("GTS ID", placeholder="GTS260059")
        owner_name = st.text_input("Owner name", placeholder="Pratyusha Mantha")
    with c2:
        title = st.text_input("Title", placeholder="VDS-Avizo-Geology")
        request_types = st.multiselect(
            "Request type",
            options=["Marketing", "Product"],
            default=["Marketing"],
            help="Select one or both. Marketing enables AEM names; Product skips AEM names.",
        )

    marketing_selected = "Marketing" in request_types
    product_selected = "Product" in request_types

    country_labels: List[str] = []
    if marketing_selected:
        st.markdown("<div class='helper'>Choose one or more countries for the AEM Name section.</div>", unsafe_allow_html=True)
        country_labels = st.multiselect(
            "AEM countries",
            options=[f"{flag} {code}" for flag, code, _ in COUNTRIES],
            default=[],
            help="Pick any number of country/localization codes.",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    valid = True
    errors: List[str] = []
    if not gtsid.strip():
        valid = False
        errors.append("GTS ID is required.")
    if not owner_name.strip():
        valid = False
        errors.append("Owner name is required.")
    if not title.strip():
        valid = False
        errors.append("Title is required.")
    if not request_types:
        valid = False
        errors.append("Select Marketing, Product, or both.")

    if not valid:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>2. Ready when input is complete</div>", unsafe_allow_html=True)
        st.info("\n".join(errors))
        st.markdown("</div>", unsafe_allow_html=True)
        return

    try:
        wordbee_outputs: List[Tuple[str, str]] = []
        if marketing_selected:
            wordbee_outputs.append(("Wordbee Name — Marketing", build_wordbee_name(gtsid, owner_name, title, "AEM")))
        if product_selected:
            wordbee_outputs.append(("Wordbee Name — Product", build_wordbee_name(gtsid, owner_name, title, "IRIS")))

        aem_outputs: List[str] = []
        if marketing_selected and country_labels:
            for label in country_labels:
                suffix = COUNTRY_LABEL_TO_SUFFIX[label]
                aem_outputs.append(build_aem_name(gtsid, owner_name, title, suffix))
        aem_urls: List[str] = [build_aem_url(name) for name in aem_outputs]
    except ValueError as exc:
        st.error(str(exc))
        return

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>2. Wordbee Name</div>", unsafe_allow_html=True)
    st.markdown("<div class='helper'>Generates one name for Marketing and one for Product when both are selected.</div>", unsafe_allow_html=True)
    for label, value in wordbee_outputs:
        copy_card(label, value)
    copy_all_card("Copy all Wordbee names", [value for _, value in wordbee_outputs])
    st.markdown("</div>", unsafe_allow_html=True)

    if marketing_selected:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>3. AEM Name</div>", unsafe_allow_html=True)
        if country_labels:
            st.markdown("<div class='helper'>One AEM Name is created per selected country.</div>", unsafe_allow_html=True)
            for name in aem_outputs:
                copy_card("AEM Name", name, secondary=True)
            copy_all_card("Copy all AEM names", aem_outputs)

            st.markdown("<div class='section-title' style='margin-top:1rem;'>4. AEM URL</div>", unsafe_allow_html=True)
            st.markdown("<div class='helper'>URL generated from each AEM Name using the Thermo Fisher projects path.</div>", unsafe_allow_html=True)
            for name, url in zip(aem_outputs, aem_urls):
                st.markdown("<div class='muted-box'>", unsafe_allow_html=True)
                st.markdown(f"**{name}**")
                copy_card("AEM URL", url)
                st.markdown("</div>", unsafe_allow_html=True)
            copy_all_card("Copy all AEM URLs", aem_urls)
        else:
            st.markdown("<div class='muted-box'>Select at least one country to generate AEM Names and URLs.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>3. AEM Name</div>", unsafe_allow_html=True)
        st.markdown("<div class='muted-box'>Product-only requests do not generate AEM Names or AEM URLs.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
