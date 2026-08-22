import re
import unicodedata
from pathlib import Path


# =====================================================
# LANGUAGE DETECTION
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
    ],

    "Bengali": [
        r"\bbengali\b",
        r"\bben\b"
    ],

    "Marathi": [
        r"\bmarathi\b",
        r"\bmar\b"
    ],

    "Punjabi": [
        r"\bpunjabi\b",
        r"\bpun\b"
    ]
}


# =====================================================
# NORMALIZATION
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
    text = re.sub(
        r"[_\-.]+",
        " ",
        text
    )

    # Remove bracketed information
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
        r"\b("
        r"480p|576p|720p|1080p|1440p|2160p|"
        r"4k|8k"
        r")\b",
        " ",
        text,
        flags=re.I
    )

    # Release tags
    text = re.sub(
        r"\b("
        r"web[- ]?dl|web[- ]?rip|webrip|"
        r"bluray|blu[- ]?ray|brrip|"
        r"hdrip|hdtv|dvdrip|"
        r"camrip|cam|ts|telesync|"
        r"proper|repack"
        r")\b",
        " ",
        text,
        flags=re.I
    )

    # Codec
    text = re.sub(
        r"\b("
        r"x264|x265|h264|h265|hevc|av1"
        r")\b",
        " ",
        text,
        flags=re.I
    )

    # Audio
    text = re.sub(
        r"\b("
        r"5\.1|7\.1|aac|ac3|dd|ddp|"
        r"ddp2\.0|ddp5\.1|ddp7\.1|"
        r"atmos|dts|truehd"
        r")\b",
        " ",
        text,
        flags=re.I
    )

    # Common source tags
    text = re.sub(
        r"\b("
        r"nf|amzn|amazon|netflix|"
        r"dsnp|disney|hulu|"
        r"yts|rarbg"
        r")\b",
        " ",
        text,
        flags=re.I
    )

    # Keep alphanumeric characters and spaces
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE
    )

    # Multiple spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def title_key(text):

    return normalize_text(text)


# =====================================================
# YEAR
# =====================================================

def extract_year(text):

    if not text:
        return None

    match = re.search(
        r"\b(19\d{2}|20\d{2})\b",
        str(text)
    )

    if match:
        return int(
            match.group(1)
        )

    return None


# =====================================================
# LANGUAGE
# =====================================================

def detect_language(text):

    if not text:
        return "Unknown"

    lower = str(text).lower()

    for language, patterns in LANGUAGE_PATTERNS.items():

        for pattern in patterns:

            if re.search(
                pattern,
                lower
            ):
                return language

    return "Unknown"


# =====================================================
# QUALITY
# =====================================================

def extract_quality(text):

    if not text:
        return "Unknown"

    match = re.search(
        r"\b("
        r"480p|576p|720p|1080p|1440p|2160p|"
        r"4k|8k"
        r")\b",
        str(text),
        flags=re.I
    )

    if match:
        return match.group(1)

    return "Unknown"


# =====================================================
# FILENAME
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
# TITLE EXTRACTION
# =====================================================

def extract_title(filename):

    if not filename:
        return ""

    name = Path(
        str(filename)
    ).stem

    # Remove quality
    name = re.sub(
        r"\b("
        r"480p|576p|720p|1080p|1440p|2160p|"
        r"4k|8k"
        r")\b",
        " ",
        name,
        flags=re.I
    )

    # Remove release/source tags
    name = re.sub(
        r"\b("
        r"web[- ]?dl|web[- ]?rip|webrip|"
        r"bluray|blu[- ]?ray|brrip|hdrip|"
        r"hdtv|dvdrip|camrip|cam|"
        r"proper|repack"
        r")\b",
        " ",
        name,
        flags=re.I
    )

    # Remove codecs
    name = re.sub(
        r"\b("
        r"x264|x265|h264|h265|hevc|av1"
        r")\b",
        " ",
        name,
        flags=re.I
    )

    # Remove audio tags
    name = re.sub(
        r"\b("
        r"5\.1|7\.1|aac|ac3|dd|ddp|"
        r"atmos|dts|truehd"
        r")\b",
        " ",
        name,
        flags=re.I
    )

    # Remove languages
    for patterns in LANGUAGE_PATTERNS.values():

        for pattern in patterns:

            name = re.sub(
                pattern,
                " ",
                name,
                flags=re.I
            )

    # Remove trailing year
    name = re.sub(
        r"[\s._-]+"
        r"(19\d{2}|20\d{2})"
        r"[\s._-]*$",
        "",
        name
    )

    # Replace separators
    name = re.sub(
        r"[._\-]+",
        " ",
        name
    )

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
