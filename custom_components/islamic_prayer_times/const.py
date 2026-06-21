"""Constants for Islamic Prayer Times integration."""

DOMAIN = "islamic_prayer_times"

CONF_LOCATION = "location"
CONF_CALC_METHOD = "calc_method"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

CONF_TARKE_SEHER_OFFSET = "tarke_seher_offset"
CONF_FAJR_OFFSET = "fajr_offset"
CONF_ZUHR_OFFSET = "zuhr_offset"
CONF_ASR_OFFSET = "asr_offset"
CONF_MAGHRIB_OFFSET = "maghrib_offset"
CONF_ISHA_OFFSET = "isha_offset"

CONF_NEXT_PRAYER_FAJR = "next_prayer_fajr"
CONF_NEXT_PRAYER_ZUHR = "next_prayer_zuhr"
CONF_NEXT_PRAYER_ASR = "next_prayer_asr"
CONF_NEXT_PRAYER_MAGHRIB = "next_prayer_maghrib"
CONF_NEXT_PRAYER_ISHA = "next_prayer_isha"

PRAYER_TARKE_SEHER = "tarke_seher"
PRAYER_FAJR = "fajr"
PRAYER_ZUHR = "zuhr"
PRAYER_ASR = "asr"
PRAYER_MAGHRIB = "maghrib"
PRAYER_ISHA = "isha"
PRAYER_NEXT = "next_prayer"

PRAYERS = [
    PRAYER_TARKE_SEHER,
    PRAYER_FAJR,
    PRAYER_ZUHR,
    PRAYER_ASR,
    PRAYER_MAGHRIB,
    PRAYER_ISHA,
]

PRAYER_NAMES = {
    PRAYER_TARKE_SEHER: "Tark-e-Seher",
    PRAYER_FAJR: "Fajr",
    PRAYER_ZUHR: "Zuhr",
    PRAYER_ASR: "Asr",
    PRAYER_MAGHRIB: "Maghrib",
    PRAYER_ISHA: "Isha",
}

PRAYER_OFFSET_MAP = {
    PRAYER_TARKE_SEHER: CONF_TARKE_SEHER_OFFSET,
    PRAYER_FAJR: CONF_FAJR_OFFSET,
    PRAYER_ZUHR: CONF_ZUHR_OFFSET,
    PRAYER_ASR: CONF_ASR_OFFSET,
    PRAYER_MAGHRIB: CONF_MAGHRIB_OFFSET,
    PRAYER_ISHA: CONF_ISHA_OFFSET,
}

PRAYER_NEXT_TOGGLE_MAP = {
    PRAYER_FAJR: CONF_NEXT_PRAYER_FAJR,
    PRAYER_ZUHR: CONF_NEXT_PRAYER_ZUHR,
    PRAYER_ASR: CONF_NEXT_PRAYER_ASR,
    PRAYER_MAGHRIB: CONF_NEXT_PRAYER_MAGHRIB,
    PRAYER_ISHA: CONF_NEXT_PRAYER_ISHA,
}

# praytimes library key -> display label
CALC_METHODS = {
    "MWL": "Muslim World League (MWL)",
    "ISNA": "Islamic Society of North America (ISNA)",
    "Egypt": "Egyptian General Authority of Survey",
    "Karachi": "University of Islamic Sciences, Karachi",
    "Makkah": "Umm Al-Qura University, Makkah",
    "Tehran": "Institute of Geophysics, Tehran",
    "Jafari": "Shia Ithna-Ashari, Leva Institute, Qum",
    "Dubai": "Dubai",
    "Qatar": "Qatar",
    "Kuwait": "Kuwait",
    "MoonSighting": "Moon Sighting Committee",
    "Singapore": "Singapore",
    "UOIF": "UOIF (France)",
    "KEMENAG": "KEMENAG / SIHAT (Indonesia)",
}

DEFAULT_CALC_METHOD = "Karachi"

# Maps our prayer keys to praytimes output keys
PRAYTIMES_KEY_MAP = {
    PRAYER_TARKE_SEHER: "imsak",
    PRAYER_FAJR: "fajr",
    PRAYER_ZUHR: "dhuhr",
    PRAYER_ASR: "asr",
    PRAYER_MAGHRIB: "maghrib",
    PRAYER_ISHA: "isha",
}

# Custom methods not built into praytimes — registered at coordinator init
CUSTOM_PRAYTIMES_METHODS = {
    "Dubai": {
        "name": "Dubai",
        "params": {"fajr": 18.2, "isha": 18.2, "maghrib": "0 min", "midnight": "Standard"},
    },
    "Qatar": {
        "name": "Qatar",
        "params": {"fajr": 18, "isha": "90 min", "maghrib": "0 min", "midnight": "Standard"},
    },
    "Kuwait": {
        "name": "Kuwait",
        "params": {"fajr": 18, "isha": 17.5, "maghrib": "0 min", "midnight": "Standard"},
    },
    "MoonSighting": {
        "name": "Moon Sighting Committee",
        "params": {"fajr": 18, "isha": 18, "maghrib": "0 min", "midnight": "Standard"},
    },
    "Singapore": {
        "name": "Singapore",
        "params": {"fajr": 20, "isha": 18, "maghrib": "0 min", "midnight": "Standard"},
    },
    "UOIF": {
        "name": "UOIF (France)",
        "params": {"fajr": 12, "isha": 12, "maghrib": "0 min", "midnight": "Standard"},
    },
    "KEMENAG": {
        "name": "KEMENAG / SIHAT (Indonesia)",
        "params": {"fajr": 20, "isha": 18, "maghrib": "2 min", "midnight": "Standard"},
    },
}
