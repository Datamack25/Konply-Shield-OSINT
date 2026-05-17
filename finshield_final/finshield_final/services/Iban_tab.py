"""
FinShield — Onglet Vérification IBAN
"""
import streamlit as st
from iban_service import analyze_iban, format_iban_display
from pdf_service import generate_iban_pdf


def render_iban_tab():
    st.header("🏦 Vérification IBAN")
    st.caption("Validation MOD97, identification bancaire, niveau de confiance")

    with st.form("iban_form"):
        iban_input = st.text_input(
            "IBAN *",
            placeholder="Ex : FR76 3000 6000 0112 3456 7890 189  ou  LB62 0008 0000 0001 0019 0122 9114",
            help="Saisir avec ou sans espaces",
        )
        col1, col2 = st.columns([1, 2])
        with col1:
            submitted = st.form_submit_button("🔍 Analyser", use_container_width=True, type="primary")

    if not submitted or not iban_input.strip():
        st.divider()
        st.subheader("📚 Exemples d'IBAN")
        examples = {
            "🇫🇷 France (BNP Paribas)":  "FR76 3000 6000 0112 3456 7890 189",
            "🇱🇧 Liban (BLOM Bank)":      "LB62 0008 0000 0001 0019 0122 9114",
            "🇩🇪 Allemagne":              "DE89 3704 0044 0532 0130 00",
            "🇬🇧 Royaume-Uni":            "GB29 NWBK 6016 1331 9268 19",
            "🇨🇭 Suisse":                 "CH93 0076 2011 6238 5295 7",
            "🇧🇪 Belgique":               "BE68 5390 0754 7034",
            "🇸🇦 Arabie saoudite":        "SA03 8000 0000 6080 1016 7519",
        }
        cols = st.columns(2)
        for i, (label, iban) in enumerate(examples.items()):
            with cols[i % 2]:
                st.code(f"{label}\n{iban}")
        return

    with st.spinner("Analyse IBAN en cours..."):
        result = analyze_iban(iban_input.strip())

    st.divider()

    if result.valid:
        st.success(f"✅ **IBAN valide** — {format_iban_display(result.iban_normalized)}")
    else:
        st.error(f"❌ **IBAN invalide** — {format_iban_display(result.iban_normalized) if result.iban_normalized else iban_input}")
        for err in result.errors:
            st.warning(f"⚠️ {err}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pays", f"{result.country_name} ({result.country_code})" if result.country_code else "—")
    c2.metric("Banque", (result.bank_name[:22] + "…") if len(result.bank_name) > 22 else result.bank_name or "—")
    c3.metric("BIC/SWIFT", result.bic or "—")
    c4.metric("Confiance", result.confidence.replace("_", " ").title())

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔢 Structure IBAN")
        data = {
            "IBAN normalisé":    result.iban_normalized or result.iban_raw,
            "IBAN formaté":      format_iban_display(result.iban_normalized) if result.iban_normalized else "—",
            "Pays":              f"{result.country_name} ({result.country_code})",
            "Chiffres contrôle": result.check_digits or "—",
            "BBAN":              result.bban or "—",
            "Code banque":       result.bank_code or "—",
            "Code succursale":   result.branch_code or "—",
            "Numéro de compte":  result.account_number or "—",
        }
        for k, v in data.items():
            st.markdown(f"**{k} :** `{v}`")

    with col2:
        st.subheader("🏛️ Établissement bancaire")
        st.markdown(f"**Banque :** {result.bank_name or '—'}")
        st.markdown(f"**Succursale :** {result.branch_name or '—'}")
        st.markdown(f"**BIC/SWIFT :** `{result.bic or '—'}`")
        st.markdown(f"**Ville :** {result.city or '—'}")
        if result.address:
            st.markdown(f"**Adresse :** {result.address}")
        st.divider()
        st.markdown(f"**{result.confidence_label}**")
        st.markdown(f"**Indicateur risque :** {result.risk_flag}")
        if result.source:
            st.caption(f"📁 Source : {result.source}")

    if result.warnings:
        st.divider()
        st.subheader("⚠️ Avertissements")
        for w in result.warnings:
            st.warning(w)

    st.divider()
    col_pdf, col_txt = st.columns(2)
    with col_pdf:
        if st.button("📄 Générer rapport PDF", use_container_width=True):
            with st.spinner("Génération PDF..."):
                pdf_bytes = generate_iban_pdf(result)
            st.download_button(
                "⬇️ Télécharger le PDF",
                pdf_bytes,
                file_name=f"iban_{result.iban_normalized or 'rapport'}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    with col_txt:
        summary = (
            f"IBAN: {result.iban_normalized}\n"
            f"Pays: {result.country_name}\n"
            f"Banque: {result.bank_name or '—'}\n"
            f"BIC: {result.bic or '—'}\n"
            f"Valide: {'Oui' if result.valid else 'Non'}\n"
            f"Confiance: {result.confidence}"
        )
        st.download_button(
            "📋 Exporter résumé TXT",
            summary.encode("utf-8"),
            file_name="iban_resume.txt",
            mime="text/plain",
            use_container_width=True,
        )
