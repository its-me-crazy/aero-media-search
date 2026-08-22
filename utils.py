import re
import unicodedata
from pathlib import Path


# =====================================================
# LANGUAGE PATTERNS
# =====================================================

LANGUAGE_PATTERNS = {

    "Hindi": [
        r"\bhindi\b",
        r"\bhin\b"
    ],

    "English": [
        r"\benglish\b",
        r"\beng\b"
    ],

    "Telugu": [
        r"\btelugu\b",
        r"\btel\b"
    ],

    "Tamil": [
        r"\btamil\b",
        r"\btam\b"
    ],

    "Malayalam": [
        r"\bmalayalam\b",
        r"\bmal\b"
    ],

    "Kannada": [
        r"\bkannada\b",
        r"\bkan\b"
    ]
}


# =====================================================
# NOISE PATTERNS
# =====================================================

QUALITY_PATTERN = (
    r"\b("
    r"480p|576p|720p|1080p|1440p|2160p|"
    r"4k|8k"
    r")\b"
)

RELEASE_PATTERN = (
    r"\b("
    r"web[- ]?dl|web[- ]?rip|"
    r"bluray|blu[- ]?ray|"
    r"brrip|hdrip|hdtv|dvdrip|"
    r"camrip|webrip"
    r")\b"
)

CODEC_PATTERN = (
    r"\b("
    r"x264|x265|h264|h265|"
    r"hevc|av1|avc"
    r")\b"
)

AUDIO_PATTERN = (
    r"\b("
    r"5\.1|7\.1|"
    r"aac|aac2\.0|"
    r"dd|ddp|"
    r"ac3|eac3|"
    r"atmos|"
    r"mp3|flac"
    r")\b"
)

SOURCE_PATTERN = (
    r"\b("
    r"amzn|amazon|"
    r"netflix|"
    r"nf|"
    r"prime|"
    r"hotstar|"
    r"zee5|"
    r"sonyliv|"
    r"jio"
    r")\b"
)


# =====================================================
# NORMALIZE TEXT
# =====================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text)

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = text.lower()

    # Replace separators
    text = text.replace(
        "_",
        " "
    )

    text = text.replace(
        ".",
        " "
    )

    text = text.replace(
        "-",
        " "
    )

    # Remove brackets and their contents
    text = re.sub(
        r"\[[^\]]*\]",
        " ",
        text
    )

    text = re.sub(
        r"\([^)]*\)",
        " ",
        text
    )

    text = re.sub(
        r"\{[^}]*\}",
        " ",
        text
    )

    # Quality
    text = re.sub(
        QUALITY_PATTERN,
        " ",
        text,
        flags=re.I
    )

    # Release/source tags
    text = re.sub(
        RELEASE_PATTERN,
        " ",
        text,
        flags=re.I
    )

    text = re.sub(
        SOURCE_PATTERN,
        " ",
        text,
        flags=re.I
    )

    # Codec
    text = re.sub(
        CODEC_PATTERN,
        " ",
        text,
        flags=re.I
    )

    # Audio
    text = re.sub(
        AUDIO_PATTERN,
        " ",
        text,
        flags=re.I
    )

    # Common release tags
    text = re.sub(
        r"\b("
        r"proper|repack|extended|"
        r"remastered|uncut|"
        r"complete|dual|multi|"
        r"dubbed|dub"
        r")\b",
        " ",
        text,
        flags=re.I
    )

    # Normalize apostrophes
    text = text.replace(
        "'",
        ""
    )

    # Keep letters/numbers/spaces
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE
    )

    # Collapse spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =====================================================
# TITLE KEY
# =====================================================

def title_key(text):

    return normalize_text(
        text
    )


# =====================================================
# TITLE TOKENS
# =====================================================

def title_tokens(text):

    key = title_key(
        text
    )

    if not key:
        return []

    tokens = key.split()

    # Remove very common filename words
    ignored = {
        "the",
        "a",
        "an"
    }

    result = []

    for token in tokens:

        if (
            token
            and token not in ignored
            and token not in result
        ):
            result.append(token)

    return result


# =====================================================
# EXTRACT YEAR
# =====================================================

def extract_year(text):

    if not text:
        return None

    matches = re.findall(
        r"\b(19\d{2}|20\d{2})\b",
        text
    )

    if not matches:
        return None

    # Usually the last year is the release year.
    return int(
        matches[-1]
    )


# =====================================================
# DETECT LANGUAGE
# =====================================================

def detect_language(text):

    if not text:
        return "Unknown"

    lower = text.lower()

    for language, patterns in LANGUAGE_PATTERNS.items():

        for pattern in patterns:

            if re.search(
                pattern,
                lower
            ):
                return language

    return "Unknown"


# =====================================================
# EXTRACT QUALITY
# =====================================================

def extract_quality(text):

    if not text:
        return "Unknown"

    match = re.search(
        QUALITY_PATTERN,
        text,
        flags=re.I
    )

    if match:

        quality = match.group(1)

        if quality.lower() == "4k":
            return "4K"

        if quality.lower() == "8k":
            return "8K"

        return quality

    return "Unknown"


# =====================================================
# GET FILENAME
# =====================================================

def get_filename(message):

    if message.document:

        return (
            message.document.file_name
            or "Unknown File"
        )

    if message.video:

        return (
            message.video.file_name
            or "Video"
        )

    if message.audio:

        return (
            message.audio.file_name
            or "Audio"
        )

    if message.animation:

        return (
            message.animation.file_name
            or "Animation"
        )

    return "Unknown File"


# =====================================================
# EXTRACT TITLE
# =====================================================

def extract_title(filename):

    if not filename:
        return ""

    name = Path(
        filename
    ).stem

    # Remove bracketed release information
    name = re.sub(
        r"\[[^\]]*\]",
        " ",
        name
    )

    name = re.sub(
        r"\([^)]*\)",
        " ",
        name
    )

    name = re.sub(
        r"\{[^}]*\}",
        " ",
        name
    )

    # Quality
    name = re.sub(
        QUALITY_PATTERN,
        " ",
        name,
        flags=re.I
    )

    # Release
    name = re.sub(
        RELEASE_PATTERN,
        " ",
        name,
        flags=re.I
    )

    # Source
    name = re.sub(
        SOURCE_PATTERN,
        " ",
        name,
        flags=re.I
    )

    # Codec
    name = re.sub(
        CODEC_PATTERN,
        " ",
        name,
        flags=re.I
    )

    # Audio
    name = re.sub(
        AUDIO_PATTERN,
        " ",
        name,
        flags=re.I
    )

    # Language
    for patterns in LANGUAGE_PATTERNS.values():

        for pattern in patterns:

            name = re.sub(
                pattern,
                " ",
                name,
                flags=re.I
            )

    # Remove year anywhere near the end
    name = re.sub(
        r"[\s._-]+"
        r"(19\d{2}|20\d{2})"
        r"[\s._-]*$",
        " ",
        name
    )

    # Replace separators
    name = re.sub(
        r"[._-]+",
        " ",
        name
    )

    # Remove remaining symbols
    name = re.sub(
        r"[^\w\s]",
        " ",
        name,
        flags=re.UNICODE
    )

    # Normalize spaces
    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name.strip()


# =====================================================
# MEDIA CHECK
# =====================================================

def is_media(message):

    return bool(
        message.video
        or message.document
        or message.audio
        or message.animation
    )
