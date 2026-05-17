"""
FinShield — Service IBAN
Validation MOD97, parsing BBAN, lookup banque/succursale, niveau de confiance
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional

from banks_fr import lookup_bank_by_cib


# ── Registre IBAN par pays ────────────────────────────────────────────────────
# Structure : country_code → {iban_length, bank_len, branch_len, account_len}
IBAN_REGISTRY: dict[str, dict] = {
    "AD": {"length": 24, "bank": 4, "branch": 4, "account": 12, "name": "Andorre"},
    "AE": {"length": 23, "bank": 3, "branch": 0, "account": 16, "name": "Émirats arabes unis"},
    "AL": {"length": 28, "bank": 3, "branch": 4, "account": 16, "name": "Albanie"},
    "AT": {"length": 20, "bank": 5, "branch": 0, "account": 11, "name": "Autriche"},
    "AZ": {"length": 28, "bank": 4, "branch": 0, "account": 20, "name": "Azerbaïdjan"},
    "BA": {"length": 20, "bank": 3, "branch": 3, "account": 10, "name": "Bosnie-Herzégovine"},
    "BE": {"length": 16, "bank": 3, "branch": 0, "account": 9,  "name": "Belgique"},
    "BG": {"length": 22, "bank": 4, "branch": 4, "account": 10, "name": "Bulgarie"},
    "BH": {"length": 22, "bank": 4, "branch": 0, "account": 14, "name": "Bahreïn"},
    "BR": {"length": 29, "bank": 8, "branch": 5, "account": 12, "name": "Brésil"},
    "BY": {"length": 28, "bank": 4, "branch": 4, "account": 16, "name": "Biélorussie"},
    "CH": {"length": 21, "bank": 5, "branch": 0, "account": 12, "name": "Suisse"},
    "CR": {"length": 22, "bank": 4, "branch": 0, "account": 14, "name": "Costa Rica"},
    "CY": {"length": 28, "bank": 3, "branch": 5, "account": 16, "name": "Chypre"},
    "CZ": {"length": 24, "bank": 4, "branch": 6, "account": 10, "name": "République tchèque"},
    "DE": {"length": 22, "bank": 8, "branch": 0, "account": 10, "name": "Allemagne"},
    "DJ": {"length": 27, "bank": 5, "branch": 5, "account": 14, "name": "Djibouti"},
    "DK": {"length": 18, "bank": 4, "branch": 0, "account": 10, "name": "Danemark"},
    "DO": {"length": 28, "bank": 4, "branch": 0, "account": 20, "name": "République dominicaine"},
    "EE": {"length": 20, "bank": 2, "branch": 2, "account": 14, "name": "Estonie"},
    "EG": {"length": 29, "bank": 4, "branch": 4, "account": 17, "name": "Égypte"},
    "ES": {"length": 24, "bank": 4, "branch": 4, "account": 12, "name": "Espagne"},
    "FI": {"length": 18, "bank": 3, "branch": 0, "account": 11, "name": "Finlande"},
    "FK": {"length": 18, "bank": 2, "branch": 0, "account": 12, "name": "Îles Malouines"},
    "FR": {"length": 27, "bank": 5, "branch": 5, "account": 13, "name": "France"},
    "GB": {"length": 22, "bank": 4, "branch": 6, "account": 8,  "name": "Royaume-Uni"},
    "GE": {"length": 22, "bank": 2, "branch": 0, "account": 16, "name": "Géorgie"},
    "GI": {"length": 23, "bank": 4, "branch": 0, "account": 15, "name": "Gibraltar"},
    "GL": {"length": 18, "bank": 4, "branch": 0, "account": 10, "name": "Groenland"},
    "GR": {"length": 27, "bank": 3, "branch": 4, "account": 16, "name": "Grèce"},
    "GT": {"length": 28, "bank": 4, "branch": 0, "account": 20, "name": "Guatemala"},
    "HR": {"length": 21, "bank": 7, "branch": 0, "account": 10, "name": "Croatie"},
    "HU": {"length": 28, "bank": 3, "branch": 4, "account": 17, "name": "Hongrie"},
    "IE": {"length": 22, "bank": 4, "branch": 6, "account": 8,  "name": "Irlande"},
    "IL": {"length": 23, "bank": 3, "branch": 3, "account": 13, "name": "Israël"},
    "IQ": {"length": 23, "bank": 4, "branch": 3, "account": 12, "name": "Irak"},
    "IS": {"length": 26, "bank": 4, "branch": 2, "account": 16, "name": "Islande"},
    "IT": {"length": 27, "bank": 5, "branch": 5, "account": 13, "name": "Italie"},
    "JO": {"length": 30, "bank": 4, "branch": 4, "account": 18, "name": "Jordanie"},
    "KW": {"length": 30, "bank": 4, "branch": 0, "account": 22, "name": "Koweït"},
    "KZ": {"length": 20, "bank": 3, "branch": 0, "account": 13, "name": "Kazakhstan"},
    "LB": {"length": 28, "bank": 4, "branch": 3, "account": 17, "name": "Liban"},
    "LC": {"length": 32, "bank": 4, "branch": 0, "account": 24, "name": "Sainte-Lucie"},
    "LI": {"length": 21, "bank": 5, "branch": 0, "account": 12, "name": "Liechtenstein"},
    "LT": {"length": 20, "bank": 5, "branch": 0, "account": 11, "name": "Lituanie"},
    "LU": {"length": 20, "bank": 3, "branch": 0, "account": 13, "name": "Luxembourg"},
    "LV": {"length": 21, "bank": 4, "branch": 0, "account": 13, "name": "Lettonie"},
    "LY": {"length": 25, "bank": 3, "branch": 3, "account": 15, "name": "Libye"},
    "MA": {"length": 28, "bank": 5, "branch": 5, "account": 14, "name": "Maroc"},
    "MC": {"length": 27, "bank": 5, "branch": 5, "account": 13, "name": "Monaco"},
    "MD": {"length": 24, "bank": 2, "branch": 0, "account": 18, "name": "Moldavie"},
    "ME": {"length": 22, "bank": 3, "branch": 0, "account": 15, "name": "Monténégro"},
    "MK": {"length": 19, "bank": 3, "branch": 0, "account": 12, "name": "Macédoine du Nord"},
    "MR": {"length": 27, "bank": 5, "branch": 5, "account": 13, "name": "Mauritanie"},
    "MT": {"length": 31, "bank": 4, "branch": 5, "account": 18, "name": "Malte"},
    "MU": {"length": 30, "bank": 6, "branch": 2, "account": 18, "name": "Maurice"},
    "NL": {"length": 18, "bank": 4, "branch": 0, "account": 10, "name": "Pays-Bas"},
    "NO": {"length": 15, "bank": 4, "branch": 0, "account": 7,  "name": "Norvège"},
    "PK": {"length": 24, "bank": 4, "branch": 0, "account": 16, "name": "Pakistan"},
    "PL": {"length": 28, "bank": 3, "branch": 4, "account": 16, "name": "Pologne"},
    "PS": {"length": 29, "bank": 4, "branch": 0, "account": 21, "name": "Palestine"},
    "PT": {"length": 25, "bank": 4, "branch": 4, "account": 13, "name": "Portugal"},
    "QA": {"length": 29, "bank": 4, "branch": 0, "account": 21, "name": "Qatar"},
    "RO": {"length": 24, "bank": 4, "branch": 0, "account": 16, "name": "Roumanie"},
    "RS": {"length": 22, "bank": 3, "branch": 0, "account": 15, "name": "Serbie"},
    "RU": {"length": 33, "bank": 9, "branch": 0, "account": 20, "name": "Russie"},
    "SA": {"length": 24, "bank": 2, "branch": 0, "account": 18, "name": "Arabie saoudite"},
    "SC": {"length": 31, "bank": 6, "branch": 2, "account": 19, "name": "Seychelles"},
    "SD": {"length": 18, "bank": 2, "branch": 0, "account": 12, "name": "Soudan"},
    "SE": {"length": 24, "bank": 3, "branch": 0, "account": 17, "name": "Suède"},
    "SI": {"length": 19, "bank": 5, "branch": 0, "account": 10, "name": "Slovénie"},
    "SK": {"length": 24, "bank": 4, "branch": 6, "account": 10, "name": "Slovaquie"},
    "SM": {"length": 27, "bank": 5, "branch": 5, "account": 13, "name": "Saint-Marin"},
    "SN": {"length": 28, "bank": 2, "branch": 5, "account": 17, "name": "Sénégal"},
    "SO": {"length": 23, "bank": 4, "branch": 4, "account": 11, "name": "Somalie"},
    "ST": {"length": 25, "bank": 4, "branch": 4, "account": 13, "name": "São Tomé-et-Príncipe"},
    "SV": {"length": 28, "bank": 4, "branch": 0, "account": 20, "name": "Salvador"},
    "TL": {"length": 23, "bank": 3, "branch": 3, "account": 13, "name": "Timor oriental"},
    "TN": {"length": 24, "bank": 2, "branch": 3, "account": 15, "name": "Tunisie"},
    "TR": {"length": 26, "bank": 5, "branch": 1, "account": 16, "name": "Turquie"},
    "UA": {"length": 29, "bank": 6, "branch": 0, "account": 19, "name": "Ukraine"},
    "VA": {"length": 22, "bank": 3, "branch": 0, "account": 15, "name": "Vatican"},
    "VG": {"length": 24, "bank": 4, "branch": 0, "account": 16, "name": "Îles Vierges britanniques"},
    "XK": {"length": 20, "bank": 2, "branch": 2, "account": 12, "name": "Kosovo"},
}

# Banques libanaises (BDL registry — données publiques)
LB_BANKS: dict[str, dict] = {
    "0001": {"name": "Banque du Liban (BDL)", "bic": "BDLBBBBX", "city": "Beyrouth",
             "address": "Rue Masraf Lubnan, Beyrouth 2012 8807"},
    "0002": {"name": "Bank Audi SAL",          "bic": "AUDBLBBE", "city": "Beyrouth",
             "address": "Bank Audi Plaza, Omar Daouk St., Beyrouth 2021 1310"},
    "0008": {"name": "BLOM Bank SAL",          "bic": "BLOMBBBB", "city": "Beyrouth",
             "address": "BLOM Building, Verdun Street, Beyrouth 2033 7301"},
    "0011": {"name": "Byblos Bank SAL",        "bic": "BYBALBBE", "city": "Antélias",
             "address": "Elias Hrawi Road, Antélias, Mont-Liban"},
    "0013": {"name": "Fransabank SAL",         "bic": "FNSALBBB", "city": "Beyrouth",
             "address": "Fransabank Center, Hamra, Beyrouth 2020 5001"},
    "0014": {"name": "SGBL (Société Générale)","bic": "SGLBBBBX", "city": "Beyrouth",
             "address": "Mar Elias, Beyrouth 1102 2034"},
    "0015": {"name": "BLC Bank SAL",           "bic": "BLCBBBBE", "city": "Beyrouth",
             "address": "Minet el-Hosn, Furn El Hayek Street, Beyrouth"},
    "0019": {"name": "Crédit Libanais SAL",    "bic": "CRLBBBBE", "city": "Beyrouth",
             "address": "Adlieh, Beyrouth"},
    "0020": {"name": "Banque Libano-Française","bic": "BLFLBBBB", "city": "Beyrouth",
             "address": "Furn El Hayek Street, Ashrafieh, Beyrouth"},
    "0025": {"name": "First National Bank",    "bic": "FNBALBBB", "city": "Beyrouth",
             "address": "Dora Highway, Beyrouth"},
    "0028": {"name": "Lebanese Swiss Bank",    "bic": "LSBLBBBB", "city": "Beyrouth",
             "address": "Achrafieh, Sursock Street, Beyrouth"},
    "0032": {"name": "BBAC — Bank of Beirut and the Arab Countries","bic":"BOACLBBE","city":"Beyrouth",
             "address": "Hamra Street, Beyrouth"},
    "0035": {"name": "IBL Bank",               "bic": "IBLLLBBE", "city": "Beyrouth",
             "address": "Sodeco Square, Beyrouth"},
    "0038": {"name": "Bank of Beirut SAL",     "bic": "BKBBLBBE", "city": "Beyrouth",
             "address": "Riad El Solh, Beyrouth"},
    "0042": {"name": "Bankmed SAL",            "bic": "BKMDLBBE", "city": "Beyrouth",
             "address": "Nahr Ibrahim Street, Beyrouth"},
    "0045": {"name": "CSC — Crédit Social du Clergé","bic":"CSCLLBBE","city":"Jdeideh",
             "address": "Jdeideh, Mont-Liban"},
    "0052": {"name": "Lebanon & Gulf Bank",    "bic": "LGBLLBBE", "city": "Beyrouth",
             "address": "Hamra, Beyrouth"},
    "0055": {"name": "Intercontinental Bank of Lebanon","bic":"INCOLBBE","city":"Beyrouth",
             "address": "Verdun, Beyrouth"},
    "0099": {"name": "Arab Bank PLC (Lebanon)","bic": "ARABLBBE", "city": "Beyrouth",
             "address": "Riad El Solh Street, Beyrouth"},
    "0104": {"name": "Standard Chartered Bank (Lebanon)","bic":"SCBLLBBE","city":"Beyrouth",
             "address": "Gefinor Center, Clemenceau, Beyrouth"},
    "0115": {"name": "HSBC Bank Middle East (Lebanon)","bic":"HSBCLBBE","city":"Beyrouth",
             "address": "Verdun Street, Beyrouth"},
}


# ── Dataclass résultat ────────────────────────────────────────────────────────
@dataclass
class IBANResult:
    """Résultat complet d'une analyse IBAN."""
    iban_raw: str
    iban_normalized: str = ""
    valid: bool = False
    country_code: str = ""
    country_name: str = ""
    check_digits: str = ""
    bban: str = ""
    bank_code: str = ""
    branch_code: str = ""
    account_number: str = ""

    # Informations bancaires
    bank_name: str = ""
    branch_name: str = ""
    bic: str = ""
    address: str = ""
    city: str = ""

    # Niveau de confiance
    confidence: str = "unknown"  # exact_branch | bank_level | registry_only | unknown

    # Sources & métadonnées
    source: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def confidence_label(self) -> str:
        labels = {
            "exact_branch":   "🟢 Succursale identifiée",
            "bank_level":     "🟡 Banque identifiée (succursale inconnue)",
            "registry_only":  "🟠 Registre uniquement (structure validée)",
            "unknown":        "🔴 Inconnu",
        }
        return labels.get(self.confidence, "⚪ N/D")

    @property
    def risk_flag(self) -> str:
        """Retourne un indicateur de risque IBAN basique."""
        high_risk_countries = {"IR", "KP", "SY", "CU", "SD", "RU", "BY"}
        if self.country_code in high_risk_countries:
            return "🔴 Pays à risque élevé"
        if self.confidence == "unknown":
            return "🟠 Structure non vérifiable"
        return "🟢 Aucun indicateur"


# ── Fonctions utilitaires ─────────────────────────────────────────────────────

def normalize_iban(iban: str) -> str:
    """Supprime les espaces et met en majuscules."""
    return re.sub(r"\s+", "", iban).upper()


def validate_mod97(iban: str) -> bool:
    """Validation MOD97 (ISO 13616)."""
    iban = normalize_iban(iban)
    if len(iban) < 5:
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        elif ch.isalpha():
            numeric += str(ord(ch) - 55)
        else:
            return False
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def format_iban_display(iban: str) -> str:
    """Formate l'IBAN en groupes de 4 pour l'affichage."""
    iban = normalize_iban(iban)
    return " ".join(iban[i:i+4] for i in range(0, len(iban), 4))


# ── Moteur principal de lookup ────────────────────────────────────────────────

def analyze_iban(iban_raw: str) -> IBANResult:
    """
    Analyse complète d'un IBAN :
    1. Normalisation
    2. Validation format (longueur + pays)
    3. Validation checksum MOD97
    4. Parsing BBAN (code banque, succursale, compte)
    5. Lookup banque (FR via CIB, LB via BDL, autres via registre)
    """
    result = IBANResult(iban_raw=iban_raw)

    # ── 1. Normalisation ──
    iban = normalize_iban(iban_raw)
    result.iban_normalized = iban

    if len(iban) < 4:
        result.errors.append("IBAN trop court.")
        return result

    # ── 2. Pays ──
    country_code = iban[:2]
    result.country_code = country_code
    result.check_digits = iban[2:4]
    result.bban = iban[4:]

    reg = IBAN_REGISTRY.get(country_code)
    if not reg:
        result.errors.append(f"Pays '{country_code}' non reconnu dans le registre IBAN.")
        result.confidence = "unknown"
        return result

    result.country_name = reg.get("name", country_code)

    # ── 3. Longueur ──
    expected = reg["length"]
    if len(iban) != expected:
        result.errors.append(
            f"Longueur incorrecte : reçu {len(iban)}, attendu {expected} pour {country_code}."
        )
    else:
        result.valid = True

    # ── 4. MOD97 ──
    if not validate_mod97(iban):
        result.errors.append("Checksum MOD97 invalide.")
        result.valid = False

    # ── 5. Parsing BBAN ──
    bban = result.bban
    bank_len   = reg.get("bank", 0)
    branch_len = reg.get("branch", 0)

    result.bank_code    = bban[:bank_len]
    result.branch_code  = bban[bank_len:bank_len + branch_len] if branch_len else ""
    result.account_number = bban[bank_len + branch_len:]

    # ── 6. Lookup selon pays ──
    if country_code == "FR":
        _lookup_fr(result)
    elif country_code == "LB":
        _lookup_lb(result)
    else:
        _lookup_generic(result)

    return result


def _lookup_fr(result: IBANResult) -> None:
    """Résolution France via code CIB (5 chiffres = bank_code)."""
    cib = result.bank_code  # 5 chiffres
    bank = lookup_bank_by_cib(cib)
    if bank:
        result.bank_name  = bank["name"]
        result.bic        = bank["bic"]
        result.city       = bank["city"]
        result.source     = "Base CIB Banque de France (données publiques)"
        result.confidence = "bank_level"
        # Succursale : code guichet (branch_code) — non résolu sans répertoire tiers
        if result.branch_code:
            result.branch_name = f"Guichet {result.branch_code}"
            result.warnings.append(
                "Le code guichet est extrait mais l'adresse exacte n'est pas disponible "
                "sans accès à un répertoire complet (ex. BIC+ SWIFT)."
            )
    else:
        result.confidence = "registry_only"
        result.source     = "Registre IBAN FR (structure validée, banque non trouvée)"
        result.warnings.append(f"Code CIB '{result.bank_code}' non trouvé dans la base locale.")


def _lookup_lb(result: IBANResult) -> None:
    """Résolution Liban via répertoire BDL (code banque 4 chiffres)."""
    bank_code = result.bank_code  # 4 chiffres pour LB
    bank = LB_BANKS.get(bank_code)
    if bank:
        result.bank_name  = bank["name"]
        result.bic        = bank["bic"]
        result.city       = bank["city"]
        result.address    = bank["address"]
        result.source     = "Répertoire Banque du Liban (BDL) — données publiques"
        result.confidence = "bank_level"
        if result.branch_code:
            result.branch_name = f"Succursale {result.branch_code}"
    else:
        result.confidence = "registry_only"
        result.source     = "Registre IBAN LB (structure validée, banque non trouvée)"
        result.warnings.append(f"Code banque LB '{bank_code}' non trouvé dans le répertoire BDL.")


def _lookup_generic(result: IBANResult) -> None:
    """Résolution générique pour les autres pays — structure validée uniquement."""
    result.confidence = "registry_only"
    result.source     = f"Registre IBAN {result.country_code} (structure validée)"
    result.warnings.append(
        f"Identification de l'établissement non disponible pour {result.country_name}. "
        "Consultez le répertoire BIC/SWIFT de votre pays."
    )
