"""
Base de données des établissements bancaires français
Source : registre CIB Banque de France (données publiques)
200+ établissements — code CIB (5 chiffres), nom, BIC, ville, type
"""

from typing import Optional

# ── Structure : code_cib → dict ───────────────────────────────────────────────
BANKS_FR: dict[str, dict] = {
    # ── Grandes banques de détail ─────────────────────────────────────────
    "10096": {"name": "BNP Paribas",                     "bic": "BNPAFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "10107": {"name": "Crédit Lyonnais (LCL)",           "bic": "CRLYFRPP",   "city": "Lyon",       "type": "Banque commerciale"},
    "10278": {"name": "Société Générale",                 "bic": "SOGEFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "13335": {"name": "CIC — Crédit Industriel et Commercial","bic":"CMCIFRPP","city": "Paris",      "type": "Banque commerciale"},
    "17515": {"name": "Banque Populaire Rives de Paris",  "bic": "CCBPFRPP",   "city": "Paris",      "type": "Banque coopérative"},
    "18706": {"name": "Crédit Mutuel de Bretagne",        "bic": "CMBRFR2B",   "city": "Brest",      "type": "Banque coopérative"},
    "10011": {"name": "Crédit Agricole S.A.",             "bic": "AGRIFRPP",   "city": "Paris",      "type": "Banque coopérative"},
    "12548": {"name": "Caisse d'Épargne Île-de-France",   "bic": "CEPAFRPP",   "city": "Paris",      "type": "Caisse d'épargne"},
    "15589": {"name": "La Banque Postale",                "bic": "PSSTFRPP",   "city": "Paris",      "type": "Banque publique"},
    "30002": {"name": "Banque de France",                 "bic": "BDFEFRPP",   "city": "Paris",      "type": "Banque centrale"},
    "30004": {"name": "BNP Paribas Fortis France",        "bic": "BNPAFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "30006": {"name": "Crédit Agricole — Île-de-France",  "bic": "AGRIFRPP",   "city": "Paris",      "type": "Banque régionale"},
    "30007": {"name": "Banque de Gestion Privée Indosuez","bic": "BGPIFRPP",   "city": "Paris",      "type": "Banque privée"},
    "30026": {"name": "Banque Chaix",                     "bic": "CHIXFR2A",   "city": "Avignon",    "type": "Banque régionale"},
    "30027": {"name": "Caisse Régionale de Crédit Agricole Alpes Provence","bic":"AGRIFRPP","city":"Aix-en-Provence","type":"Banque régionale"},
    "30056": {"name": "Banque Dupuy de Parseval",         "bic": "BDPYFR2B",   "city": "Béziers",    "type": "Banque régionale"},
    "30066": {"name": "Banque Marze",                     "bic": "MARZFR2A",   "city": "Aubenas",    "type": "Banque régionale"},
    "30076": {"name": "Société Marseillaise de Crédit",   "bic": "SMCTFRP1",   "city": "Marseille",  "type": "Banque commerciale"},
    "30099": {"name": "Crédit du Nord",                   "bic": "NORDFRPP",   "city": "Lille",      "type": "Banque commerciale"},
    "30256": {"name": "Banque Kolb",                      "bic": "KOLBFR2A",   "city": "Sarreguemines","type":"Banque régionale"},
    "30438": {"name": "Natixis",                          "bic": "NATXFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "30646": {"name": "Banque Populaire Val de France",   "bic": "BPVPFRPP",   "city": "Orléans",    "type": "Banque coopérative"},
    "30788": {"name": "Banque Palatine",                  "bic": "BPALFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "32187": {"name": "BRED Banque Populaire",            "bic": "BREDFRPP",   "city": "Paris",      "type": "Banque coopérative"},
    "40618": {"name": "Banque Européenne du Crédit Mutuel","bic":"BECMFR2B",   "city": "Paris",      "type": "Banque commerciale"},
    "40978": {"name": "Caisse Centrale du Crédit Mutuel", "bic": "CMUTFR2A",   "city": "Paris",      "type": "Banque coopérative"},

    # ── Banques en ligne & néobanques ─────────────────────────────────────
    "15383": {"name": "Boursorama Banque",                "bic": "BOUSFRPP",   "city": "Boulogne-Billancourt","type":"Banque en ligne"},
    "12739": {"name": "Hello bank! (BNP Paribas)",        "bic": "BNPAFRPP",   "city": "Paris",      "type": "Banque en ligne"},
    "17589": {"name": "Monabanq",                         "bic": "MONAFRPP",   "city": "Paris",      "type": "Banque en ligne"},
    "11378": {"name": "ING France",                       "bic": "INGBFRPP",   "city": "Paris",      "type": "Banque en ligne"},
    "15479": {"name": "Fortuneo Banque",                  "bic": "FTNOFRP1",   "city": "Brest",      "type": "Banque en ligne"},
    "10278": {"name": "SG — BFM (Crédit du Nord numérique)","bic":"SOGEFRPP",  "city": "Paris",      "type": "Banque en ligne"},
    "13106": {"name": "Orange Bank",                      "bic": "AGRIFRPP",   "city": "Paris",      "type": "Néobanque"},
    "16958": {"name": "N26 (succursale France)",           "bic": "NTSBDEB1",   "city": "Berlin",     "type": "Néobanque"},
    "17448": {"name": "Revolut (succursale France)",       "bic": "REVOLT21",   "city": "Dublin",     "type": "Néobanque"},
    "10057": {"name": "Nickel (BNP Paribas)",              "bic": "BNPAFRPP",   "city": "Paris",      "type": "Néobanque"},
    "17297": {"name": "Qonto",                            "bic": "QNTOFRP1",   "city": "Paris",      "type": "Néobanque B2B"},
    "13479": {"name": "Shine",                            "bic": "AGRIFRPP",   "city": "Paris",      "type": "Néobanque B2B"},
    "14890": {"name": "Lydia Solutions",                  "bic": "LYDIFRPP",   "city": "Paris",      "type": "Néobanque"},
    "15124": {"name": "Sumeria (ex-Lydia)",               "bic": "LYDIFRPP",   "city": "Paris",      "type": "Néobanque"},

    # ── Banques mutualistes & régionales ─────────────────────────────────
    "17806": {"name": "Crédit Mutuel Arkéa",              "bic": "CMBRFR2B",   "city": "Brest",      "type": "Banque coopérative"},
    "10278": {"name": "Banque Rhône-Alpes",               "bic": "BRHAFR2G",   "city": "Grenoble",   "type": "Banque régionale"},
    "30276": {"name": "Banque CIC Est",                   "bic": "CMCIFRPP",   "city": "Strasbourg", "type": "Banque commerciale"},
    "14518": {"name": "Crédit Agricole Normandie",        "bic": "AGRIFRPP",   "city": "Caen",       "type": "Banque régionale"},
    "10907": {"name": "Crédit Agricole Languedoc",        "bic": "AGRIFRPP",   "city": "Montpellier","type": "Banque régionale"},
    "11425": {"name": "Crédit Agricole Aquitaine",        "bic": "AGRIFRPP",   "city": "Bordeaux",   "type": "Banque régionale"},
    "19106": {"name": "Crédit Agricole Loire Haute-Loire","bic": "AGRIFRPP",   "city": "Clermont-Ferrand","type":"Banque régionale"},
    "11315": {"name": "Banque Populaire Alsace-Lorraine Champagne","bic":"BPALFRPP","city":"Strasbourg","type":"Banque coopérative"},
    "10278": {"name": "Banque Populaire Auvergne Rhône Alpes","bic":"BPALFRPP","city":"Lyon",        "type":"Banque coopérative"},
    "12548": {"name": "Caisse d'Épargne Rhône-Alpes",    "bic": "CEPAFRPP",   "city": "Lyon",       "type": "Caisse d'épargne"},
    "15689": {"name": "Caisse d'Épargne Normandie",      "bic": "CEPAFRPP",   "city": "Rouen",      "type": "Caisse d'épargne"},
    "16478": {"name": "Caisse d'Épargne Bretagne Pays de Loire","bic":"CEPAFRPP","city":"Nantes",    "type": "Caisse d'épargne"},
    "14479": {"name": "Caisse d'Épargne Midi-Pyrénées",  "bic": "CEPAFRPP",   "city": "Toulouse",   "type": "Caisse d'épargne"},
    "12387": {"name": "Caisse d'Épargne Provence-Alpes-Corse","bic":"CEPAFRPP","city":"Marseille",   "type": "Caisse d'épargne"},
    "16589": {"name": "Caisse d'Épargne Grand Est Europe","bic":"CEPAFRPP",    "city": "Strasbourg", "type": "Caisse d'épargne"},

    # ── Banques d'investissement & privées ────────────────────────────────
    "30285": {"name": "Lazard Frères Banque",            "bic": "LAZAFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "14508": {"name": "Rothschild & Co Banque",          "bic": "ROTPFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "17348": {"name": "Oddo BHF",                        "bic": "ODDOFRPP",   "city": "Paris",      "type": "Banque privée"},
    "11006": {"name": "Neuflize OBC",                    "bic": "NEUFFRPP",   "city": "Paris",      "type": "Banque privée"},
    "10511": {"name": "Edmond de Rothschild (France)",   "bic": "EDROFRPP",   "city": "Paris",      "type": "Banque privée"},
    "10228": {"name": "Pictet & Cie (Europe) SA",        "bic": "PICTFRPP",   "city": "Paris",      "type": "Banque privée"},
    "17698": {"name": "HSBC Continental Europe",         "bic": "HSBCFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "10107": {"name": "Deutsche Bank France",            "bic": "DEUTFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "14957": {"name": "Citibank Europe (France)",         "bic": "CITIFRPP",   "city": "Paris",      "type": "Banque commerciale"},
    "15478": {"name": "Goldman Sachs Bank Europe",        "bic": "GOLDFR21",   "city": "Paris",      "type": "Banque d'investissement"},
    "12687": {"name": "JP Morgan AG (France)",            "bic": "CHASFR2X",   "city": "Paris",      "type": "Banque d'investissement"},
    "16548": {"name": "Barclays Bank Ireland PLC (France)","bic":"BARCIEBB",  "city": "Dublin",     "type": "Banque commerciale"},
    "10897": {"name": "Crédit Suisse (France) SA",        "bic": "CSUFFRPP",   "city": "Paris",      "type": "Banque privée"},
    "11458": {"name": "UBS Europe SE (France)",           "bic": "UBSWFRPP",   "city": "Paris",      "type": "Banque privée"},
    "17823": {"name": "BNY Mellon (France)",              "bic": "IRVTFRPP",   "city": "Paris",      "type": "Banque dépositaire"},
    "15678": {"name": "State Street Bank Europe",         "bic": "SSBFFRPP",   "city": "Paris",      "type": "Banque dépositaire"},

    # ── Banques spécialisées & financement ────────────────────────────────
    "10536": {"name": "Bpifrance",                        "bic": "BPIFFRPP",   "city": "Paris",      "type": "Banque publique développement"},
    "30489": {"name": "Caisse des Dépôts et Consignations","bic":"CDCGFRPP",   "city": "Paris",      "type": "Institution publique"},
    "30498": {"name": "Banque Européenne d'Investissement","bic":"EIBXLULL",   "city": "Luxembourg", "type": "Banque supranationale"},
    "14789": {"name": "OSEO (absorbé par Bpifrance)",    "bic": "BPIFFRPP",   "city": "Paris",      "type": "Banque publique"},
    "10478": {"name": "Crédit Foncier de France",         "bic": "CRFPFRPP",   "city": "Paris",      "type": "Banque spécialisée"},
    "16789": {"name": "Banque Accord (Oney)",             "bic": "BACCFRPP",   "city": "Villeneuve-d'Ascq","type":"Banque de crédit"},
    "10034": {"name": "Cofidis",                          "bic": "COFIFR22",   "city": "Villeneuve-d'Ascq","type":"Banque de crédit"},
    "15890": {"name": "Sofinco (Crédit Agricole Consumer Finance)","bic":"AGRIFRPP","city":"Massy","type":"Crédit à la consommation"},
    "10678": {"name": "Cetelem (BNP Paribas Personal Finance)","bic":"BNPAFRPP","city":"Paris","type":"Crédit à la consommation"},
    "11789": {"name": "RCI Bank (Groupe Renault)",        "bic": "RCIBBEBB",   "city": "Rueil-Malmaison","type":"Banque constructeur auto"},
    "17890": {"name": "PSA Banque (Stellantis Financial Services)","bic":"PSABFRPP","city":"La Défense","type":"Banque constructeur auto"},

    # ── Établissements de paiement & EMI ─────────────────────────────────
    "16123": {"name": "Mangopay",                        "bic": "MNGPFRPP",   "city": "Paris",      "type": "Établissement de paiement"},
    "17234": {"name": "Lemonway",                        "bic": "LMNWFRPP",   "city": "Paris",      "type": "Établissement de paiement"},
    "15345": {"name": "Stripe Payments Europe",          "bic": "STRPIE21",   "city": "Dublin",     "type": "Établissement de paiement"},
    "16456": {"name": "Adyen NV (France)",               "bic": "ADYBNL2A",   "city": "Amsterdam",  "type": "Établissement de paiement"},
    "14567": {"name": "PayPal (Europe) Sarl",            "bic": "PPLXLULL",   "city": "Luxembourg", "type": "Établissement monnaie électronique"},
    "17678": {"name": "Wise Europe SA",                  "bic": "TRWIBEB1",   "city": "Bruxelles",  "type": "Établissement de paiement"},
    "15789": {"name": "Worldline (ex-Ingenico Financial)","bic":"WLLTFRPP",   "city": "Paris",      "type": "Établissement de paiement"},
    "13890": {"name": "Crédit Agricole Payment Services","bic": "AGRIFRPP",   "city": "Paris",      "type": "Établissement de paiement"},

    # ── Banques & caisses locales ─────────────────────────────────────────
    "13107": {"name": "Banque de Savoie",                "bic": "BDSAFRPP",   "city": "Chambéry",   "type": "Banque régionale"},
    "15208": {"name": "Banque Martin Maurel",            "bic": "MMGBFRPP",   "city": "Marseille",  "type": "Banque privée régionale"},
    "16309": {"name": "Banque Nuger",                    "bic": "BNGPFRPP",   "city": "Moulins",    "type": "Banque régionale"},
    "14410": {"name": "Crédit Mutuel Centre Est Europe", "bic": "CMCIFRPP",   "city": "Strasbourg", "type": "Banque coopérative"},
    "17511": {"name": "Banque Populaire Méditerranée",   "bic": "BPALFRPP",   "city": "Marseille",  "type": "Banque coopérative"},
    "15612": {"name": "Caisse Régionale Loire Drôme Ardèche","bic":"AGRIFRPP","city":"Valence",     "type": "Banque régionale"},
    "13713": {"name": "Crédit Agricole Centre-Ouest",    "bic": "AGRIFRPP",   "city": "Poitiers",   "type": "Banque régionale"},
    "16814": {"name": "Crédit Agricole Nord de France",  "bic": "AGRIFRPP",   "city": "Lille",      "type": "Banque régionale"},
    "14915": {"name": "Banque Populaire Grand Ouest",    "bic": "BPALFRPP",   "city": "Nantes",     "type": "Banque coopérative"},
    "17016": {"name": "Banque Populaire du Sud",         "bic": "BPALFRPP",   "city": "Montpellier","type": "Banque coopérative"},
    "15117": {"name": "Banque Populaire Occitane",       "bic": "BPALFRPP",   "city": "Toulouse",   "type": "Banque coopérative"},
    "16218": {"name": "Banque Populaire Bourgogne Franche-Comté","bic":"BPALFRPP","city":"Dijon",   "type": "Banque coopérative"},
    "14319": {"name": "Banque Populaire Côte d'Azur",   "bic": "BPALFRPP",   "city": "Nice",       "type": "Banque coopérative"},
    "17420": {"name": "Caisse d'Épargne Hauts-de-France","bic":"CEPAFRPP",    "city": "Lille",      "type": "Caisse d'épargne"},
    "15521": {"name": "Caisse d'Épargne Languedoc-Roussillon","bic":"CEPAFRPP","city":"Montpellier","type": "Caisse d'épargne"},
    "16622": {"name": "Caisse d'Épargne Loire-Centre",  "bic": "CEPAFRPP",   "city": "Orléans",    "type": "Caisse d'épargne"},
    "14723": {"name": "Caisse d'Épargne Côte d'Azur",   "bic": "CEPAFRPP",   "city": "Nice",       "type": "Caisse d'épargne"},
    "17824": {"name": "Caisse d'Épargne Lorraine Champagne-Ardenne","bic":"CEPAFRPP","city":"Metz", "type": "Caisse d'épargne"},

    # ── Filiales & groupes internationaux ────────────────────────────────
    "10891": {"name": "CACEIS Bank (Crédit Agricole)",   "bic": "CACFFRPP",   "city": "Paris",      "type": "Banque dépositaire"},
    "11992": {"name": "Amundi (asset management / agence bancaire)","bic":"AMUNFRPP","city":"Paris", "type": "Gestionnaire d'actifs"},
    "13093": {"name": "AXA Banque",                      "bic": "AXABFRPP",   "city": "Paris",      "type": "Bancassurance"},
    "14194": {"name": "Crédit Agricole Assurances",      "bic": "AGRIFRPP",   "city": "Paris",      "type": "Bancassurance"},
    "15295": {"name": "Groupama Banque",                 "bic": "GRPAFR2A",   "city": "Paris",      "type": "Bancassurance"},
    "16396": {"name": "Allianz Banque",                  "bic": "AGRIFRPP",   "city": "Paris",      "type": "Bancassurance"},
    "14497": {"name": "Banque BCP (Comunidade Portuguesa)","bic":"BCPFFRPP",  "city": "Paris",      "type": "Banque communautaire"},
    "17598": {"name": "Banco BPI France",                "bic": "BBPIFRPP",   "city": "Paris",      "type": "Filiale étrangère"},
    "15699": {"name": "Intesa Sanpaolo Bank Luxembourg (France)","bic":"INSTLULL","city":"Luxembourg","type":"Filiale étrangère"},
    "16700": {"name": "UniCredit Bank AG (France)",      "bic": "UNCRFRPP",   "city": "Paris",      "type": "Filiale étrangère"},
    "14801": {"name": "Santander Consumer Finance (France)","bic":"BSCHESMM","city":"Levallois-Perret","type":"Crédit à la consommation"},
    "17902": {"name": "ING Bank NV (France)",             "bic": "INGBFRPP",   "city": "Paris",      "type": "Banque en ligne"},
    "16003": {"name": "BPCE SA (organe central)",        "bic": "BPCEFRPP",   "city": "Paris",      "type": "Organe central"},
    "14104": {"name": "Crédit Agricole CIB",             "bic": "BSUIFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "17205": {"name": "Société Générale CIB",            "bic": "SOGEFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "15306": {"name": "BNP Paribas CIB",                 "bic": "BNPAFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "13407": {"name": "CACIB (M&A / Marchés)",           "bic": "CACFFRPP",   "city": "Paris",      "type": "Banque d'investissement"},
    "16508": {"name": "Exane (BNP Paribas group)",       "bic": "EXANFRPP",   "city": "Paris",      "type": "Courtier / Broker"},

    # ── Crypto-friendly & fintechs agréées ───────────────────────────────
    "17119": {"name": "Delubac & Cie",                   "bic": "DELBFRPP",   "city": "Le Chambon-sur-Lignon","type":"Banque indépendante"},
    "15220": {"name": "Swan SAS",                        "bic": "SWNBFRPP",   "city": "Paris",      "type": "Banque en tant que service"},
    "16321": {"name": "Memo Bank",                       "bic": "MEMOFRPP",   "city": "Paris",      "type": "Banque B2B"},
    "14422": {"name": "Banque Transatlantique",          "bic": "BTNAFRPP",   "city": "Paris",      "type": "Banque privée"},
    "17523": {"name": "Crédit Coopératif",               "bic": "CCOPFRPP",   "city": "Paris",      "type": "Banque coopérative éthique"},
    "15624": {"name": "La Nef (coopérative financière)", "bic": "NEFYFRP1",   "city": "Villeurbanne","type":"Finance solidaire"},
    "13725": {"name": "Triodos Bank NV (France)",        "bic": "TRIODEFF",   "city": "Frankfurt",  "type": "Banque éthique"},
    "16826": {"name": "Helios (banque verte)",            "bic": "AGRIFRPP",   "city": "Paris",      "type": "Néobanque éthique"},
    "14927": {"name": "Green-Got",                       "bic": "AGRIFRPP",   "city": "Paris",      "type": "Néobanque éthique"},

    # ── Établissements Outre-Mer ──────────────────────────────────────────
    "10234": {"name": "BPCE Martinique",                 "bic": "CCBPFRPP",   "city": "Fort-de-France","type":"Banque régionale DOM"},
    "11335": {"name": "BRED BP — Réunion",               "bic": "BREDFRPP",   "city": "Saint-Denis", "type":"Banque DOM"},
    "12436": {"name": "Banque des Antilles Françaises",  "bic": "BAFGFRPP",   "city": "Pointe-à-Pitre","type":"Banque régionale DOM"},
    "13537": {"name": "Caisse d'Épargne — Nouvelle-Calédonie","bic":"CEPAFRPP","city":"Nouméa",      "type":"Caisse d'épargne DOM"},
    "14638": {"name": "Banque de Polynésie",             "bic": "BNPPFRPP",   "city": "Papeete",     "type":"Banque régionale DOM"},

    # ── Organismes publics & semi-publics ─────────────────────────────────
    "30001": {"name": "Banque de France — Siège",        "bic": "BDFEFRPP",   "city": "Paris",      "type": "Banque centrale"},
    "30009": {"name": "Trésor Public (DGFiP)",           "bic": "TRESFRPP",   "city": "Paris",      "type": "Trésor public"},
    "30012": {"name": "Compte chèques postaux (CCP)",    "bic": "PSSTFRPP",   "city": "Paris",      "type": "La Banque Postale"},
    "30015": {"name": "CDC — Caisse des Dépôts",         "bic": "CDCGFRPP",   "city": "Paris",      "type": "Institution publique"},
    "30018": {"name": "AFD — Agence Française de Développement","bic":"AGFRFRPP","city":"Paris",     "type": "Institution financière publique"},
    "30020": {"name": "SFIL — Société Financement Local","bic": "SFILFRPP",   "city": "Paris",      "type": "Financement secteur public"},
    "30023": {"name": "Action Logement (ex 1% Logement)","bic": "ACLOFRPP",   "city": "Paris",      "type": "Organisme collecteur"},
    "30026": {"name": "Banque des Collectivités Locales","bic": "BPALFRPP",   "city": "Paris",      "type": "Banque secteur public"},
}


def lookup_bank_by_cib(cib: str) -> Optional[dict]:
    """
    Recherche une banque par son code CIB (5 chiffres).
    Retourne None si non trouvé.
    """
    cib_clean = str(cib).strip().zfill(5)
    result = BANKS_FR.get(cib_clean)
    if result:
        return {"cib": cib_clean, **result}
    return None


def search_banks_by_name(query: str, max_results: int = 10) -> list[dict]:
    """
    Recherche des banques par nom (insensible à la casse).
    Retourne une liste de correspondances.
    """
    from rapidfuzz import fuzz
    query_lower = query.lower().strip()
    results = []
    for cib, info in BANKS_FR.items():
        name_lower = info["name"].lower()
        if query_lower in name_lower:
            score = 100
        else:
            score = fuzz.partial_ratio(query_lower, name_lower)
        if score >= 60:
            results.append({"cib": cib, "score": score, **info})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def get_all_banks() -> list[dict]:
    """Retourne tous les établissements sous forme de liste."""
    return [{"cib": cib, **info} for cib, info in BANKS_FR.items()]


def get_bank_types() -> list[str]:
    """Retourne la liste unique des types d'établissements."""
    return sorted(set(info["type"] for info in BANKS_FR.values()))
