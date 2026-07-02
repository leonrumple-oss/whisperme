"""Zentrale Farbpalette — angelehnt an die Design-Vorlage des Nutzers:
dunkles Graphit, leuchtende Akzentfarben pro Bereich, Koralle als
Primäraktion. Tupel = (heller Modus, dunkler Modus); einfache Strings
gelten in beiden Modi.
"""

WINBG = ("#ececef", "#121218")
CARD = ("#ffffff", "#212129")
TXT = ("#1b1b22", "#f2f2f7")
SUB = ("#8a8a96", "#9a9aa8")
FIELD = ("#f0f0f4", "#2c2c37")
FIELD_HOVER = ("#e4e4ea", "#383845")
BORDER = ("#e2e2e9", "#3a3a48")

# Koralle wie die "Clear all"/"Exit"-Buttons der Vorlage
PRIMARY = "#ff5c4d"
PRIMARY_HOVER = "#ff7a6d"
PRIMARY_TXT = "#ffffff"

# Akzentfarben der Bereiche (wie die bunten Icon-Kacheln der Vorlage)
BLUE = "#3d8bff"
ORANGE = "#ff8b3d"
VIOLET = "#8b5cf6"
GREEN = "#22c55e"
TEAL = "#0eb8c9"

ACCENT_HOVER = {
    BLUE: "#61a1ff",
    ORANGE: "#ffa261",
    VIOLET: "#a37ef8",
    GREEN: "#3fd377",
    TEAL: "#3ecbd9",
    PRIMARY: PRIMARY_HOVER,
}

# Segment-Text: hell auf Akzent im Dunkelmodus, dunkel im Hellmodus
SEG_TXT = ("#1b1b22", "#ffffff")
