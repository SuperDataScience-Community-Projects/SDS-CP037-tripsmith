
from __future__ import annotations
import csv
import os
from typing import Dict, Tuple, Optional

import pycountry

    def _country_name(alpha2: str) -> str:
        if not alpha2:
            return ""
        c = pycountry.countries.get(alpha_2=alpha2)
        return c.name if c else alpha2
except Exception:

    _COUNTRY_OVERRIDES = {
        "AD": "Andorra",
        "AE": "United Arab Emirates",
        "AF": "Afghanistan",
        "AG": "Antigua and Barbuda",
        "AI": "Anguilla",
        "AL": "Albania",
        "AM": "Armenia",
        "AO": "Angola",
        "AQ": "Antarctica",
        "AR": "Argentina",
        "AS": "American Samoa",
        "AT": "Austria",
        "AU": "Australia",
        "AW": "Aruba",
        "AX": "Åland Islands",
        "AZ": "Azerbaijan",
        "BA": "Bosnia and Herzegovina",
        "BB": "Barbados",
        "BD": "Bangladesh",
        "BE": "Belgium",
        "BF": "Burkina Faso",
        "BG": "Bulgaria",
        "BH": "Bahrain",
        "BI": "Burundi",
        "BJ": "Benin",
        "BL": "Saint Barthélemy",
        "BM": "Bermuda",
        "BN": "Brunei Darussalam",
        "BO": "Bolivia (Plurinational State of)",
        "BQ": "Bonaire, Sint Eustatius and Saba",
        "BR": "Brazil",
        "BS": "Bahamas",
        "BT": "Bhutan",
        "BV": "Bouvet Island",
        "BW": "Botswana",
        "BY": "Belarus",
        "BZ": "Belize",
        "CA": "Canada",
        "CC": "Cocos (Keeling) Islands",
        "CD": "Congo, Democratic Republic of the",
        "CF": "Central African Republic",
        "CG": "Congo",
        "CH": "Switzerland",
        "CI": "Côte d’Ivoire",
        "CK": "Cook Islands",
        "CL": "Chile",
        "CM": "Cameroon",
        "CN": "China",
        "CO": "Colombia",
        "CR": "Costa Rica",
        "CU": "Cuba",
        "CV": "Cabo Verde",
        "CW": "Curaçao",
        "CX": "Christmas Island",
        "CY": "Cyprus",
        "CZ": "Czechia",
        "DE": "Germany",
        "DJ": "Djibouti",
        "DK": "Denmark",
        "DM": "Dominica",
        "DO": "Dominican Republic",
        "DZ": "Algeria",
        "EC": "Ecuador",
        "EE": "Estonia",
        "EG": "Egypt",
        "EH": "Western Sahara",
        "ER": "Eritrea",
        "ES": "Spain",
        "ET": "Ethiopia",
        "FI": "Finland",
        "FJ": "Fiji",
        "FK": "Falkland Islands (Malvinas)",
        "FM": "Micronesia (Federated States of)",
        "FO": "Faroe Islands",
        "FR": "France",
        "GA": "Gabon",
        "GB": "United Kingdom",
        "GD": "Grenada",
        "GE": "Georgia",
        "GF": "French Guiana",
        "GG": "Guernsey",
        "GH": "Ghana",
        "GI": "Gibraltar",
        "GL": "Greenland",
        "GM": "Gambia",
        "GN": "Guinea",
        "GP": "Guadeloupe",
        "GQ": "Equatorial Guinea",
        "GR": "Greece",
        "GS": "South Georgia and the South Sandwich Islands",
        "GT": "Guatemala",
        "GU": "Guam",
        "GW": "Guinea-Bissau",
        "GY": "Guyana",
        "HK": "Hong Kong",
        "HM": "Heard Island and McDonald Islands",
        "HN": "Honduras",
        "HR": "Croatia",
        "HT": "Haiti",
        "HU": "Hungary",
        "ID": "Indonesia",
        "IE": "Ireland",
        "IL": "Israel",
        "IM": "Isle of Man",
        "IN": "India",
        "IO": "British Indian Ocean Territory",
        "IQ": "Iraq",
        "IR": "Iran (Islamic Republic of)",
        "IS": "Iceland",
        "IT": "Italy",
        "JE": "Jersey",
        "JM": "Jamaica",
        "JO": "Jordan",
        "JP": "Japan",
        "KE": "Kenya",
        "KG": "Kyrgyzstan",
        "KH": "Cambodia",
        "KI": "Kiribati",
        "KM": "Comoros",
        "KN": "Saint Kitts and Nevis",
        "KP": "Korea (Democratic People’s Republic of)",
        "KR": "Korea, Republic of",
        "KW": "Kuwait",
        "KY": "Cayman Islands",
        "KZ": "Kazakhstan",
        "LA": "Lao People’s Democratic Republic",
        "LB": "Lebanon",
        "LC": "Saint Lucia",
        "LI": "Liechtenstein",
        "LK": "Sri Lanka",
        "LR": "Liberia",
        "LS": "Lesotho",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "LV": "Latvia",
        "LY": "Libya",
        "MA": "Morocco",
        "MC": "Monaco",
        "MD": "Moldova, Republic of",
        "ME": "Montenegro",
        "MF": "Saint Martin (French part)",
        "MG": "Madagascar",
        "MH": "Marshall Islands",
        "MK": "North Macedonia",
        "ML": "Mali",
        "MM": "Myanmar",
        "MN": "Mongolia",
        "MO": "Macao",
        "MP": "Northern Mariana Islands",
        "MQ": "Martinique",
        "MR": "Mauritania",
        "MS": "Montserrat",
        "MT": "Malta",
        "MU": "Mauritius",
        "MV": "Maldives",
        "MW": "Malawi",
        "MX": "Mexico",
        "MY": "Malaysia",
        "MZ": "Mozambique",
        "NA": "Namibia",
        "NC": "New Caledonia",
        "NE": "Niger",
        "NF": "Norfolk Island",
        "NG": "Nigeria",
        "NI": "Nicaragua",
        "NL": "Netherlands",
        "NO": "Norway",
        "NP": "Nepal",
        "NR": "Nauru",
        "NU": "Niue",
        "NZ": "New Zealand",
        "OM": "Oman",
        "PA": "Panama",
        "PE": "Peru",
        "PF": "French Polynesia",
        "PG": "Papua New Guinea",
        "PH": "Philippines",
        "PK": "Pakistan",
        "PL": "Poland",
        "PM": "Saint Pierre and Miquelon",
        "PN": "Pitcairn",
        "PR": "Puerto Rico",
        "PS": "Palestine, State of",
        "PT": "Portugal",
        "PW": "Palau",
        "PY": "Paraguay",
        "QA": "Qatar",
        "RE": "Réunion",
        "RO": "Romania",
        "RS": "Serbia",
        "RU": "Russian Federation",
        "RW": "Rwanda",
        "SA": "Saudi Arabia",
        "SB": "Solomon Islands",
        "SC": "Seychelles",
        "SD": "Sudan",
        "SE": "Sweden",
        "SG": "Singapore",
        "SH": "Saint Helena, Ascension and Tristan da Cunha",
        "SI": "Slovenia",
        "SJ": "Svalbard and Jan Mayen",
        "SK": "Slovakia",
        "SL": "Sierra Leone",
        "SM": "San Marino",
        "SN": "Senegal",
        "SO": "Somalia",
        "SR": "Suriname",
        "SS": "South Sudan",
        "ST": "Sao Tome and Principe",
        "SV": "El Salvador",
        "SX": "Sint Maarten (Dutch part)",
        "SY": "Syrian Arab Republic",
        "SZ": "Eswatini",
        "TC": "Turks and Caicos Islands",
        "TD": "Chad",
        "TF": "French Southern Territories",
        "TG": "Togo",
        "TH": "Thailand",
        "TJ": "Tajikistan",
        "TK": "Tokelau",
        "TL": "Timor-Leste",
        "TM": "Turkmenistan",
        "TN": "Tunisia",
        "TO": "Tonga",
        "TR": "Türkiye",
        "TT": "Trinidad and Tobago",
        "TV": "Tuvalu",
        "TW": "Taiwan, Province of China",
        "TZ": "Tanzania, United Republic of",
        "UA": "Ukraine",
        "UG": "Uganda",
        "UM": "United States Minor Outlying Islands",
        "US": "United States",
        "UY": "Uruguay",
        "UZ": "Uzbekistan",
        "VA": "Holy See",
        "VC": "Saint Vincent and the Grenadines",
        "VE": "Venezuela (Bolivarian Republic of)",
        "VG": "Virgin Islands (British)",
        "VI": "Virgin Islands (U.S.)",
        "VN": "Viet Nam",
        "VU": "Vanuatu",
        "WF": "Wallis and Futuna",
        "WS": "Samoa",
        "XK": "Kosovo",
        "YE": "Yemen",
        "YT": "Mayotte",
        "ZA": "South Africa",
        "ZM": "Zambia",
        "ZW": "Zimbabwe",
    }

    def _country_name(alpha2: str) -> str:
        return _COUNTRY_OVERRIDES.get(alpha2 or "", alpha2 or "")


DATA_PATH = os.path.join(os.getcwd(), "data", "airports.csv")


def load_airports(csv_path: str = DATA_PATH) -> Tuple[Dict[str, dict], Dict[str, str]]:
    by_iata: Dict[str, dict] = {}
    city_to_iata: Dict[str, str] = {}
    if not os.path.exists(csv_path):
        return by_iata, city_to_iata

    preference = {"large_airport": 3, "medium_airport": 2, "small_airport": 1}

    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            iata = (row.get("iata_code") or "").strip().upper()
            if len(iata) != 3:
                continue
            city = (row.get("municipality") or "").strip()
            country_code = (row.get("iso_country") or "").strip()
            country = _country_name(country_code)
            name = (row.get("name") or "").strip()
            atype = (row.get("type") or "").strip()

            by_iata[iata] = {
                "iata": iata,
                "city": city,
                "country": country,
                "name": name,
                "type": atype,
            }

            if city and country:
                key = f"{city}, {country}".lower()
                # prefer larger airport types
                if key not in city_to_iata:
                    city_to_iata[key] = iata
                else:
                    current = city_to_iata[key]
                    cur_pref = preference.get(by_iata.get(current, {}).get("type", ""), 0)
                    new_pref = preference.get(atype, 0)
                    if new_pref > cur_pref:
                        city_to_iata[key] = iata

    return by_iata, city_to_iata


_BY_IATA, _CITY_TO_IATA = load_airports()


def get_city_for_iata(iata: str) -> str:
    if not iata:
        return iata
    info = _BY_IATA.get(iata.upper())
    if not info:
        return iata.upper()
    city = info.get("city") or iata.upper()
    country = info.get("country") or ""
    return f"{city}, {country}".strip(", ")


def get_iata_for_city(city_or_code: str, country_hint: Optional[str] = None) -> str:
    if not city_or_code:
        return city_or_code
    v = city_or_code.strip()
    if len(v) == 3 and v.isalpha():
        return v.upper()

    if country_hint:
        key = f"{v}, {country_hint}".lower()
        code = _CITY_TO_IATA.get(key)
        if code:
            return code

    city_lower = v.lower()
    candidates = [k for k in _CITY_TO_IATA.keys() if k.startswith(city_lower + ", ")]
    if candidates:
        return _CITY_TO_IATA[candidates[0]]

    return v[:3].upper()


def normalize_to_iata(value: str, country_hint: Optional[str] = None) -> str:
    return get_iata_for_city(value, country_hint=country_hint)
