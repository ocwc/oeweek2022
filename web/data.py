# from https://github.com/sparcopen/opencon-2018-app-code/blob/e0200322bd71577e9800c40b05255d053bca8cf8/opencon/application/data.py

COUNTRY_LIST="""
    Afghanistan
    Albania
    Algeria
    Andorra
    Angola
    Antigua and Barbuda
    Argentina
    Armenia
    Aruba
    Australia
    Austria
    Azerbaijan
    Bahamas, The
    Bahrain
    Bangladesh
    Barbados
    Belarus
    Belgium
    Belize
    Benin
    Bhutan
    Bolivia
    Bosnia and Herzegovina
    Botswana
    Brazil
    Brunei
    Bulgaria
    Burkina Faso
    Burma
    Burundi
    Cambodia
    Cameroon
    Canada
    Cape Verde
    Central African Republic
    Chad
    Chile
    China
    Colombia
    Comoros
    Congo, Democratic Republic of the
    Congo, Republic of the
    Costa Rica
    Cote d'Ivoire
    Croatia
    Cuba
    Curacao
    Cyprus
    Czech Republic
    Denmark
    Djibouti
    Dominica
    Dominican Republic
    East Timor
    Ecuador
    Egypt
    El Salvador
    Equatorial Guinea
    Eritrea
    Estonia
    Ethiopia
    Fiji
    Finland
    France
    Gabon
    Gambia
    Georgia
    Germany
    Ghana
    Greece
    Grenada
    Guatemala
    Guinea
    Guinea-Bissau
    Guyana
    Haiti
    Holy See
    Honduras
    Hong Kong
    Hungary
    Iceland
    India
    Indonesia
    Iran
    Iraq
    Ireland
    Israel
    Italy
    Jamaica
    Japan
    Jordan
    Kazakhstan
    Kenya
    Kiribati
    Kosovo
    Kuwait
    Kyrgyzstan
    Laos
    Latvia
    Lebanon
    Lesotho
    Liberia
    Libya
    Liechtenstein
    Lithuania
    Luxembourg
    Macau
    Macedonia
    Madagascar
    Malawi
    Malaysia
    Maldives
    Mali
    Malta
    Marshall Islands
    Mauritania
    Mauritius
    Mexico
    Micronesia
    Moldova
    Monaco
    Mongolia
    Montenegro
    Morocco
    Mozambique
    Namibia
    Nauru
    Nepal
    Netherlands
    Netherlands Antilles
    New Zealand
    Nicaragua
    Niger
    Nigeria
    North Korea
    Norway
    Oman
    Pakistan
    Palau
    Palestinian Territories
    Panama
    Papua New Guinea
    Paraguay
    Peru
    Philippines
    Poland
    Portugal
    Qatar
    Romania
    Russia
    Rwanda
    Saint Kitts and Nevis
    Saint Lucia
    Saint Vincent and the Grenadines
    Samoa
    San Marino
    Sao Tome and Principe
    Saudi Arabia
    Senegal
    Serbia
    Seychelles
    Sierra Leone
    Singapore
    Sint Maarten
    Slovakia
    Slovenia
    Solomon Islands
    Somalia
    South Africa
    South Korea
    South Sudan
    Spain
    Sri Lanka
    Sudan
    Suriname
    Swaziland
    Sweden
    Switzerland
    Syria
    Taiwan
    Tajikistan
    Tanzania
    Thailand
    Timor-Leste
    Togo
    Tonga
    Trinidad and Tobago
    Tunisia
    Turkey
    Turkmenistan
    Tuvalu
    Uganda
    Ukraine
    United Arab Emirates
    United Kingdom
    United States of America
    Uruguay
    Uzbekistan
    Vanuatu
    Venezuela
    Vietnam
    Yemen
    Zambia
    Zimbabwe
    Country Not Listed
"""

COUNTRY_CHOICES = [(None, 'Please select an option below')]
COUNTRY_CHOICES += [((c.strip(), c.strip())) for c in COUNTRY_LIST.strip().split('\n')]
# note "Other" option added to the original list of countries (because of the instructions)

# --- --- --- --- ---

# from https://github.com/ocwc/oerweek-frontend/blob/f62653f6b4f125271e0b2787c065b08a3f0d0a10/app/utils/get-active-languages.js

LANGUAGE_LIST="""
    Arabic
    Burmese
    Croatian
    Dutch
    English
    Finnish
    French
    German
    Greek
    Japanese
    Mandarin
    Moldavian
    Polish
    Portuguese, Brazil
    Romanian
    Slovak
    Slovenian
    Spanish
    Ukrainian
    Other
"""

LANGUAGE_CHOICES = [(None, 'Please select an option below')]
LANGUAGE_CHOICES += [((c.strip(), c.strip())) for c in LANGUAGE_LIST.strip().split('\n')]

# --- --- --- --- ---
