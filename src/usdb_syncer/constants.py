"""Constants"""

import re

MINIMUM_BPM = 200.0


class UsdbStrings:
    """Relevant strings from USDB"""

    WELCOME: str
    SONG_EDITED_BY: str
    SONG_RATING: str
    GOLDEN_NOTES: str
    SONGCHECK: str
    DATE: str
    CREATED_BY: str
    VIEWS: str
    VERIFY_NEW_SONGS: str
    DATASET_NOT_FOUND = "Datensatz nicht gefunden"
    WELCOME_PLEASE_LOGIN = "Welcome, Please login"


class UsdbStringsEnglish(UsdbStrings):
    """Relevant strings from USDB"""

    WELCOME = "Welcome"
    SONG_EDITED_BY = "Song edited by:"
    SONG_RATING = "Rating"
    GOLDEN_NOTES = "Golden Notes"
    SONGCHECK = "Songcheck"
    DATE = "Date"
    CREATED_BY = "Created by"
    VIEWS = "Views"
    VERIFY_NEW_SONGS = "Verify New Songs"


class UsdbStringsGerman(UsdbStrings):
    """Relevant strings from USDB"""

    WELCOME = "Willkommen"
    SONG_EDITED_BY = "Song editiert von:"
    SONG_RATING = "Bewertung"
    GOLDEN_NOTES = "Goldene Noten"
    SONGCHECK = "Songcheck"
    DATE = "Datum"
    CREATED_BY = "Erstellt von"
    VIEWS = "Aufrufe"
    VERIFY_NEW_SONGS = "Neue Songs verifizieren"


class UsdbStringsFrench(UsdbStrings):
    """Relevant strings from USDB"""

    WELCOME = "Bienvenue"
    SONG_EDITED_BY = "Chanson modifiée par:"
    SONG_RATING = "Classement"
    GOLDEN_NOTES = "Notes en or"
    SONGCHECK = "Songcheck"
    DATE = "Date"
    CREATED_BY = "créé par"
    VIEWS = "Affichages"
    VERIFY_NEW_SONGS = "Vérifier les nouvelles chansons"


class Usdb:
    """Constants related to USDB."""

    DOMAIN = "usdb.animux.de"
    BASE_URL = "https://" + DOMAIN + "/"
    MAX_SONG_ID = 30000
    MAX_SONGS_PER_PAGE = 100
    DATETIME_STRF = "%d.%m.%y - %H:%M"


SUPPORTED_VIDEO_SOURCES_REGEX = re.compile(
    r"""\b
        (
            (?:https?://)?
            (?:www\.)?
            (?:
                youtube\.com
                | youtube-nocookie\.com
                | youtu\.be
                | vimeo\.com
                | archive\.org
                | fb\.watch
                | universal-music\.de
                | dailymotion\.com
            )
            /\S+
        )
    """,
    re.VERBOSE,
)
