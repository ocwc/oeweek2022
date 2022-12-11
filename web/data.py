import geonamescache

GC = geonamescache.GeonamesCache()

COUNTRY_CHOICES = [(None, "Please select an option below")]
COUNTRY_CHOICES += [((c, c)) for c in sorted(GC.get_countries_by_names().keys())]
COUNTRY_CHOICES += [("Country Not Listed", "Country Not Listed")]

# --- --- --- --- ---

# from https://github.com/ocwc/oerweek-frontend/blob/f62653f6b4f125271e0b2787c065b08a3f0d0a10/app/utils/get-active-languages.js

LANGUAGE_LIST = """
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

LANGUAGE_CHOICES = [(None, "Please select an option below")]
LANGUAGE_CHOICES += [
    ((c.strip(), c.strip())) for c in LANGUAGE_LIST.strip().split("\n")
]

#

LICENSE_CHOICES = [
    ("Public domain", "Public domain"),
    ("CC-0", "CC Zero (CC 0)"),
    ("CC-BY", "CC Attribution (CC BY)"),
    ("CC-BY-SA", "CC Attribution — Share-Alike (CC BY-SA)"),
    ("CC-BY-NC", "CC Attribution — Non-Commercial (CC BY-NC)"),
    ("CC-NC-SA", "CC Attribution — Non-Commercial — Share-Alike (CC BY-NC-SA)"),
    ("Other", "Other open license"),
]
