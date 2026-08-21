import re
import unicodedata
from pathlib import Path


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


def normalize_text(text):

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = text.lower()

    text = text.replace("_", " ")
    text = text.replace(".", " ")
    text = text.replace("-", " ")

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

    # Quality
    text = re.sub(
        r"\b(480p|576p|720p|1080p|2160p|4k|8k)\b",
        " ",
        text
    )

    # Release tags
    text = re.sub(
        r"\b(web[- ]?dl|webrip|bluray|brrip|hdrip|hdtv|dvdrip)\b",
        " ",
        text
    )

    # Codec
    text = re.sub(
        r"\b(x264|x265|h264|h265|hevc|av1)\b",
        " ",
        text
    )

    # Common audio tags
    text = re.sub(
        r"\b(5\.1|7\.1|aac|ddp|atmos)\b",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def title_key(text):

    return normalize_text(text)


def extract_year(text):

    match = re.search(
        r"\b(19\d{2}|20\d{2})\b",
        text
    )

    if match:
        return int(
            match.group(1)
        )

    return None


def detect_language(text):

    lower = text.lower()

    for language, patterns in LANGUAGE_PATTERNS.items():

        for pattern in patterns:

            if re.search(
                pattern,
                lower
            ):
                return language

    return "Unknown"


def extract_quality(text):

    match = re.search(
        r"\b(480p|576p|720p|1080p|2160p|4k|8k)\b",
        text,
        flags=re.I
    )

    if match:
        return match.group(1)

    return "Unknown"


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


def extract_title(filename):

    name = Path(
        filename
    ).stem

    name = re.sub(
        r"\b(480p|576p|720p|1080p|2160p|4k|8k)\b",
        " ",
        name,
        flags=re.I
    )

    name = re.sub(
        r"\b(web[- ]?dl|webrip|bluray|brrip|hdrip|hdtv|dvdrip)\b",
        " ",
        name,
        flags=re.I
    )

    name = re.sub(
        r"\b(x264|x265|h264|h265|hevc|av1)\b",
        " ",
        name,
        flags=re.I
    )

    for patterns in LANGUAGE_PATTERNS.values():

        for pattern in patterns:

            name = re.sub(
                pattern,
                " ",
                name,
                flags=re.I
            )

    # Remove trailing year.
    name = re.sub(
        r"[\s._-]+"
        r"(19\d{2}|20\d{2})"
        r"[\s._-]*$",
        "",
        name
    )

    name = re.sub(
        r"[\[\](){}]",
        " ",
        name
    )

    name = re.sub(
        r"[._]+",
        " ",
        name
    )

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name.strip()


def is_media(message):

    return bool(
        message.video
        or message.document
        or message.audio
        or message.animation
    )
