"""
FinShield OSINT — Plateforme de conformité financière & due diligence
Point d'entrée principal Streamlit
"""

import streamlit as st
import sys
import os

# ── S'assurer que le dossier racine ET services/ sont dans sys.path ───────────
ROOT = os.path.dirname(os.path.abspath(__file__))
SERVICES = os.path.join(ROOT, "services")
DATA = os.path.join(ROOT, "data")

for p in [ROOT, SERVICES, DATA]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title="FinShield OSINT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/yourrepo/finshield-osint",
        "About": "FinShield OSINT v1.0 — Plateforme de conformité AML/KYC",
    },
)

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --primary:   #1A2B4A;
    --accent:    #E63946;
    --success:   #52B788;
    --warning:   #F4A261;
    --critical:  #6A0572;
    --bg-card:   #F8F9FA;
    --border:    #DEE2E6;
}
.sidebar-header {
    background: linear-gradient(135deg, #1A2B4A 0%, #2D4A7A 100%);
    color: white;
    padding: 1.2rem 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    text-align: center;
}
[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem;
}
.footer-note {
    font-size: 0.75rem;
    color: #888;
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div style="font-size:2rem;">🛡️</div>
        <div style="font-size:1.1rem; font-weight:700; margin-top:4px;">FinShield OSINT</div>
        <div style="font-size:0.75rem; opacity:0.8;">Conformité financière & Due Diligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🔑 Configuration API")

    api_key = ""
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        st.success("✅ Clé API chargée depuis les secrets")
    except Exception:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            st.success("✅ Clé API chargée depuis l'environnement")
        else:
            api_key = st.text_input(
                "Clé Anthropic API",
                type="password",
                placeholder="sk-ant-...",
                help="Obtenez votre clé sur console.anthropic.com",
            )
            if api_key:
                st.success("✅ Clé saisie manuellement")
            else:
                st.warning("⚠️ Clé API requise pour l'analyse OSINT")

    st.session_state["anthropic_api_key"] = api_key

    st.divider()
    st.subheader("📋 Navigation")
    st.markdown("""
    - 🏦 **IBAN** — Validation & lookup bancaire
    - 🔍 **OSINT** — Analyse due diligence
    - 📋 **Banques** — Recherche par CIB / nom
    - ⚙️ **Config** — Sources & documentation
    """)

    st.divider()
    st.markdown(f"""
    <small>
    🟢 Application opérationnelle<br>
    📦 Version : <b>1.0.0</b><br>
    🔑 API : {'✅ OK' if api_key else '❌ Manquante'}
    </small>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div class="footer-note">
    ⚠️ Usage professionnel uniquement.<br>
    Respectez le RGPD et les législations locales.<br>
    Les résultats sont informatifs uniquement.
    </div>
    """, unsafe_allow_html=True)

# ── Import des onglets depuis services/ ───────────────────────────────────────
from Iban_tab import render_iban_tab
from osint_tab import render_osint_tab
from bank_search_tab import render_bank_search_tab
from config_tab import render_config_tab

# ── Titre ─────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="margin-bottom:0;">🛡️ FinShield OSINT</h1>
<p style="color:#666; margin-top:4px;">
Plateforme de conformité financière & due diligence — AML/KYC
</p>
""", unsafe_allow_html=True)

# ── Onglets ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏦 Vérification IBAN",
    "🔍 Analyse OSINT",
    "📋 Recherche Banque",
    "⚙️ Sources & Config",
])

with tab1:
    render_iban_tab()

with tab2:
    render_osint_tab()

with tab3:
    render_bank_search_tab()

with tab4:
    render_config_tab()
