from pathlib import Path
import html
import json
import re

import pandas as pd
import streamlit as st


# =============================================================================
# Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
APP_DATA_DIR = PROJECT_ROOT / "app_data"

TALKS_APP_PATH = APP_DATA_DIR / "talks_app.json"
RECOMMENDATIONS_APP_PATH = APP_DATA_DIR / "recommendations_app.json"

BYU_COMPANION_ITEMS_PATH = APP_DATA_DIR / "byu_companion_items_app_v2.json"
BYU_COMPANION_RECS_PATH = APP_DATA_DIR / "byu_companion_recommendations_app_v2.json"

STUDY_PATHS_APP_PATH = APP_DATA_DIR / "study_paths_app.json"


# =============================================================================
# Recommendation Mode Configuration
# =============================================================================

MODE_DESCRIPTIONS = {
    "Best Overall": (
        "Uses a weighted combination of semantic similarity, official Church topic labels, "
        "and phrase-level overlap. This is the recommended default."
    ),
    "Similar Spiritual Need": (
        "Emphasizes broad semantic and pastoral similarity across the full talk. "
        "This mode is useful when you want talks that feel spiritually or emotionally adjacent."
    ),
    "Similar Doctrine": (
        "Emphasizes official General Conference topic labels assigned by the Church. "
        "This mode is more grounded in official topic indexing, but may be less nuanced."
    ),
    "Similar Language / Imagery": (
        "Emphasizes shared words, phrases, metaphors, and rhetorical texture. "
        "This mode is useful for finding talks with similar language or imagery."
    ),
}

MODE_SCORE_LABELS = {
    "Best Overall": "Best overall score",
    "Similar Spiritual Need": "Spiritual-need similarity",
    "Similar Doctrine": "Official-topic similarity",
    "Similar Language / Imagery": "Language / imagery similarity",
}


# =============================================================================
# Data Loading
# =============================================================================

@st.cache_data(show_spinner=False)
def load_app_data():
    """
    Load lightweight deployable app data.

    Returns
    -------
    tuple[list[dict], dict, list[dict], dict]
        Conference talks, Conference recommendations, BYU companion items,
        and BYU companion recommendations.
    """
    with open(TALKS_APP_PATH, "r", encoding="utf-8") as f:
        talks = json.load(f)

    with open(RECOMMENDATIONS_APP_PATH, "r", encoding="utf-8") as f:
        recommendations = json.load(f)

    talks = normalize_talk_records(talks)

    byu_companion_items = []
    byu_companion_recommendations = {}

    if BYU_COMPANION_ITEMS_PATH.exists():
        with open(BYU_COMPANION_ITEMS_PATH, "r", encoding="utf-8") as f:
            byu_companion_items = json.load(f)

        byu_companion_items = normalize_byu_companion_records(byu_companion_items)

    if BYU_COMPANION_RECS_PATH.exists():
        with open(BYU_COMPANION_RECS_PATH, "r", encoding="utf-8") as f:
            byu_companion_recommendations = json.load(f)

    study_paths_app = {}

    if STUDY_PATHS_APP_PATH.exists():
        with open(STUDY_PATHS_APP_PATH, "r", encoding="utf-8") as f:
            study_paths_app = json.load(f)

    return (
        talks,
        recommendations,
        byu_companion_items,
        byu_companion_recommendations,
        study_paths_app,
    )


def normalize_talk_records(talks):
    """
    Normalize talk records so the app can rely on consistent fields.

    Parameters
    ----------
    talks : list[dict]
        Raw talk records from talks_app.json.

    Returns
    -------
    list[dict]
        Normalized talk records.
    """
    normalized = []

    for i, talk in enumerate(talks):
        official_topics = talk.get("official_topics", [])

        if isinstance(official_topics, str):
            official_topics = [
                topic.strip()
                for topic in official_topics.split(",")
                if topic.strip()
            ]

        scripture_references = talk.get("scripture_references", [])

        if isinstance(scripture_references, str):
            scripture_references = [
                ref.strip()
                for ref in scripture_references.split(",")
                if ref.strip()
            ]

        scripture_chapters = talk.get("scripture_chapters", [])

        if isinstance(scripture_chapters, str):
            scripture_chapters = [
                ref.strip()
                for ref in scripture_chapters.split(",")
                if ref.strip()
            ]

        scripture_books = talk.get("scripture_books", [])

        if isinstance(scripture_books, str):
            scripture_books = [
                ref.strip()
                for ref in scripture_books.split(",")
                if ref.strip()
            ]

        url = talk.get("url", "")
        year = talk.get("year", None)

        if year is None:
            year = get_year_from_url(url)

        normalized.append({
            "index": int(talk.get("index", i)),
            "title": talk.get("title", ""),
            "speaker": talk.get("speaker", ""),
            "year": year,
            "url": url,
            "official_topics": official_topics,
            "scripture_references": scripture_references,
            "scripture_chapters": scripture_chapters,
            "scripture_books": scripture_books,
        })

    return normalized


def normalize_byu_companion_records(items):
    """
    Normalize BYU companion records so the app can rely on consistent fields.

    Parameters
    ----------
    items : list[dict]
        Raw BYU companion items.

    Returns
    -------
    list[dict]
        Normalized BYU companion items.
    """
    normalized = []

    for i, item in enumerate(items):
        official_topics = item.get("official_topics", [])

        if isinstance(official_topics, str):
            official_topics = [
                topic.strip()
                for topic in official_topics.split(",")
                if topic.strip()
            ]

        scripture_references = item.get("scripture_references", [])

        if isinstance(scripture_references, str):
            scripture_references = [
                ref.strip()
                for ref in scripture_references.split(",")
                if ref.strip()
            ]

        byu_topics = item.get("byu_topics", [])

        if isinstance(byu_topics, str):
            byu_topics = [
                topic.strip()
                for topic in byu_topics.split(",")
                if topic.strip()
            ]

        normalized.append({
            "companion_index": int(item.get("companion_index", i)),
            "item_id": item.get("item_id", ""),
            "source_type": item.get("source_type", "byu_speech"),
            "collection": item.get("collection", "BYU Speeches"),
            "source_authority": item.get("source_authority", "byu_speeches"),
            "source_priority": item.get("source_priority", 2),
            "title": item.get("title", ""),
            "speaker": item.get("speaker", ""),
            "author": item.get("author", item.get("speaker", "")),
            "year": item.get("year"),
            "date": item.get("date", ""),
            "url": item.get("url", ""),
            "speech_type": item.get("speech_type", ""),
            "official_topics": official_topics,
            "scripture_references": scripture_references,
            "byu_topics": byu_topics,
        })

    return normalized


def get_byu_companion_by_index(byu_companion_items, index):
    """
    Retrieve a BYU companion item by companion index.
    """
    return byu_companion_items[index]


def get_byu_companion_recommendations(
    selected_index,
    byu_companion_items,
    byu_companion_recommendations,
    k=5,
):
    """
    Retrieve BYU Speeches companion recommendations for a Conference talk.

    Parameters
    ----------
    selected_index : int
        General Conference talk index.
    byu_companion_items : list[dict]
        BYU companion metadata.
    byu_companion_recommendations : dict
        Compact BYU recommendations keyed by Conference talk index.
    k : int
        Number of companion recommendations.

    Returns
    -------
    list[dict]
        Enriched BYU companion recommendation records.
    """
    raw_recommendations = byu_companion_recommendations.get(str(selected_index), [])

    enriched = []

    for rec in raw_recommendations[:k]:
        byu_index = int(rec["i"])
        score = float(rec.get("s", 0.0))

        item = get_byu_companion_by_index(byu_companion_items, byu_index)

        enriched.append({
            "index": byu_index,
            "title": item.get("title", ""),
            "speaker": item.get("speaker", ""),
            "year": item.get("year"),
            "date": item.get("date", ""),
            "speech_type": item.get("speech_type", ""),
            "score": score,
            "url": item.get("url", ""),
            "collection": item.get("collection", "BYU Speeches"),
            "byu_topics": item.get("byu_topics", []),
        })

    return enriched


# =============================================================================
# Metadata Helpers
# =============================================================================

def get_year_from_url(url):
    """
    Extract the General Conference year from a talk URL.

    Parameters
    ----------
    url : str
        General Conference talk URL.

    Returns
    -------
    int or None
        The year if found; otherwise None.
    """
    if not url:
        return None

    parts = url.split("/")

    try:
        gc_index = parts.index("general-conference")
        return int(parts[gc_index + 1])
    except (ValueError, IndexError):
        return None


def build_talks_df(talks):
    """
    Build a searchable DataFrame from the loaded talks.

    Parameters
    ----------
    talks : list[dict]
        List of talk records.

    Returns
    -------
    DataFrame
        Searchable talk metadata.
    """
    rows = []

    for talk in talks:
        rows.append({
            "index": talk.get("index"),
            "title": talk.get("title", ""),
            "speaker": talk.get("speaker", ""),
            "year": talk.get("year"),
            "official_topics": ", ".join(talk.get("official_topics", [])),
            "url": talk.get("url", ""),
        })

    return pd.DataFrame(rows)


def get_talk_by_index(talks, index):
    """
    Retrieve a talk by its stored index.

    Parameters
    ----------
    talks : list[dict]
        Talk records.
    index : int
        Talk index.

    Returns
    -------
    dict
        Matching talk.
    """
    return talks[index]


def shared_topics(talk_a, talk_b):
    """
    Return official topics shared by two talks.

    Parameters
    ----------
    talk_a : dict
        First talk.
    talk_b : dict
        Second talk.

    Returns
    -------
    list[str]
        Sorted shared official topics.
    """
    topics_a = set(talk_a.get("official_topics", []))
    topics_b = set(talk_b.get("official_topics", []))

    return sorted(topics_a.intersection(topics_b))


def normalize_reference_text(text):
    """
    Normalize scripture reference text for searching.

    Parameters
    ----------
    text : str
        Raw scripture reference text.

    Returns
    -------
    str
        Normalized reference text.
    """
    if text is None:
        return ""

    text = str(text).lower().strip()

    text = text.replace("–", "-").replace("—", "-")

    text = text.replace("&", "and")
    text = re.sub(r"\bd\s*and\s*c\b", "doctrine and covenants", text)
    text = re.sub(r"\bd\.?\s*and\s*c\.?\b", "doctrine and covenants", text)

    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .")

    return text


def search_scripture_references(talks, query):
    """
    Search talks by scripture reference, chapter, or book.

    Parameters
    ----------
    talks : list[dict]
        Talk records with scripture reference fields.
    query : str
        User search query, such as "Mosiah 3:19", "Mosiah 3", or "Mosiah".

    Returns
    -------
    DataFrame
        Matching talks.
    """
    normalized_query = normalize_reference_text(query)

    if not normalized_query:
        return pd.DataFrame()

    rows = []

    for talk in talks:
        exact_refs = talk.get("scripture_references", [])
        chapter_refs = talk.get("scripture_chapters", [])
        book_refs = talk.get("scripture_books", [])

        normalized_exact_refs = [
            normalize_reference_text(ref)
            for ref in exact_refs
        ]

        normalized_chapter_refs = [
            normalize_reference_text(ref)
            for ref in chapter_refs
        ]

        normalized_book_refs = [
            normalize_reference_text(ref)
            for ref in book_refs
        ]

        exact_matches = [
            ref for ref, norm_ref in zip(exact_refs, normalized_exact_refs)
            if norm_ref == normalized_query
        ]

        partial_exact_matches = [
            ref for ref, norm_ref in zip(exact_refs, normalized_exact_refs)
            if normalized_query in norm_ref and norm_ref != normalized_query
        ]

        chapter_matches = [
            ref for ref, norm_ref in zip(chapter_refs, normalized_chapter_refs)
            if norm_ref == normalized_query
        ]

        book_matches = [
            ref for ref, norm_ref in zip(book_refs, normalized_book_refs)
            if norm_ref == normalized_query
        ]

        if exact_matches:
            match_type = "Exact reference"
            priority = 4
            matched_references = exact_matches

        elif partial_exact_matches:
            match_type = "Reference range / partial reference"
            priority = 3
            matched_references = partial_exact_matches

        elif chapter_matches:
            match_type = "Same chapter"
            priority = 2
            matched_references = chapter_matches

        elif book_matches:
            match_type = "Same book"
            priority = 1
            matched_references = book_matches

        else:
            continue

        rows.append({
            "index": talk.get("index"),
            "title": talk.get("title", ""),
            "speaker": talk.get("speaker", ""),
            "year": talk.get("year"),
            "match_type": match_type,
            "priority": priority,
            "matched_references": ", ".join(matched_references),
            "all_scripture_references": ", ".join(exact_refs),
            "official_topics": ", ".join(talk.get("official_topics", [])),
            "url": talk.get("url", ""),
        })

    results_df = pd.DataFrame(rows)

    if len(results_df) == 0:
        return results_df

    return results_df.sort_values(
        ["priority", "year", "title"],
        ascending=[False, False, True]
    ).drop(columns=["priority"])


# =============================================================================
# Recommendation Helpers
# =============================================================================

def get_recommendation_modes(recommendations_app):
    """
    Determine available recommendation modes from recommendations_app.json.

    Supports the preferred structure:
        {mode_name: {talk_index: [recommendations]}}

    Returns
    -------
    list[str]
        Available recommendation modes.
    """
    if not isinstance(recommendations_app, dict):
        return []

    preferred_modes = [
        "Best Overall",
        "Similar Spiritual Need",
        "Similar Doctrine",
        "Similar Language / Imagery",
    ]

    existing_modes = [
        mode for mode in preferred_modes
        if mode in recommendations_app
    ]

    if existing_modes:
        return existing_modes

    return list(recommendations_app.keys())


def get_precomputed_recommendations(
    selected_index,
    recommendation_mode,
    recommendations_app,
    talks,
    k=5,
):
    """
    Retrieve precomputed recommendations for a selected talk and mode.

    Supports compact records of the form:
        {"i": recommended_index, "s": score}

    Also supports older verbose records with:
        {"index": recommended_index, "score": score}
    """
    mode_data = recommendations_app.get(recommendation_mode, {})
    raw_recommendations = []

    if isinstance(mode_data, dict):
        raw_recommendations = mode_data.get(str(selected_index), [])

        if not raw_recommendations:
            raw_recommendations = mode_data.get(selected_index, [])

    # Fallback for alternate structure:
    # {selected_index: {mode_name: [recommendations]}}
    if not raw_recommendations:
        selected_data = recommendations_app.get(str(selected_index), {})

        if isinstance(selected_data, dict):
            raw_recommendations = selected_data.get(recommendation_mode, [])

    enriched = []

    for rec in raw_recommendations[:k]:
        # Compact format.
        if "i" in rec:
            rec_index = int(rec["i"])
            score = float(rec.get("s", 0.0))

        # Older verbose format.
        else:
            rec_index = int(rec.get("index", rec.get("recommended_index")))
            score = float(rec.get("score", 0.0))

        talk = get_talk_by_index(talks, rec_index)

        enriched.append({
            "index": rec_index,
            "title": talk.get("title", ""),
            "speaker": talk.get("speaker", ""),
            "year": talk.get("year"),
            "score": score,
            "official_topics": ", ".join(talk.get("official_topics", [])),
            "url": talk.get("url", ""),
        })

    return enriched


def format_talk_option(index, talks_df):
    """
    Format a talk option for a Streamlit selectbox.

    Parameters
    ----------
    index : int
        Talk index.
    talks_df : DataFrame
        Searchable talk metadata.

    Returns
    -------
    str
        Human-readable talk option.
    """
    row = talks_df.loc[talks_df["index"] == index].iloc[0]
    return f"{row['title']} — {row['speaker']} ({row['year']})"


def filter_talks_for_selector(talks_df, query=None, speaker=None, year=None):
    """
    Filter talks for a selection widget.

    Parameters
    ----------
    talks_df : DataFrame
        Talk metadata.
    query : str, optional
        Title search query.
    speaker : str, optional
        Speaker search query.
    year : str or int, optional
        Year filter.

    Returns
    -------
    DataFrame
        Filtered talks.
    """
    filtered = talks_df.copy()

    if query:
        filtered = filtered[
            filtered["title"].str.contains(query, case=False, na=False, regex=False)
        ]

    if speaker:
        filtered = filtered[
            filtered["speaker"].str.contains(speaker, case=False, na=False, regex=False)
        ]

    if year:
        try:
            year_value = int(year)
            filtered = filtered[filtered["year"] == year_value]
        except ValueError:
            pass

    return filtered


def build_source_items_df(talks, byu_companion_items):
    """
    Build a searchable DataFrame containing both General Conference talks
    and BYU Speeches companion sources.

    Returns
    -------
    DataFrame
        Searchable source-item metadata.
    """
    rows = []

    for talk in talks:
        rows.append({
            "option_id": f"conference::{talk.get('index')}",
            "source_type": "conference_talk",
            "source_label": "General Conference",
            "index": talk.get("index"),
            "title": talk.get("title", ""),
            "speaker": talk.get("speaker", ""),
            "year": talk.get("year"),
            "topics": ", ".join(talk.get("official_topics", [])),
            "url": talk.get("url", ""),
        })

    for item in byu_companion_items:
        rows.append({
            "option_id": f"byu::{item.get('companion_index')}",
            "source_type": "byu_speech",
            "source_label": "BYU Speeches",
            "index": item.get("companion_index"),
            "title": item.get("title", ""),
            "speaker": item.get("speaker", ""),
            "year": item.get("year"),
            "topics": ", ".join(item.get("byu_topics", [])),
            "url": item.get("url", ""),
        })

    return pd.DataFrame(rows)


def filter_source_items(source_items_df, query=None, speaker=None, year=None, source_label=None):
    """
    Filter source items for the Compare Sources tab.
    """
    filtered = source_items_df.copy()

    if source_label and source_label != "All":
        filtered = filtered[filtered["source_label"] == source_label]

    if query:
        filtered = filtered[
            filtered["title"].str.contains(query, case=False, na=False, regex=False)
        ]

    if speaker:
        filtered = filtered[
            filtered["speaker"].str.contains(speaker, case=False, na=False, regex=False)
        ]

    if year:
        try:
            year_value = int(year)
            filtered = filtered[filtered["year"] == year_value]
        except ValueError:
            pass

    return filtered


def get_source_item_by_option_id(option_id, talks, byu_companion_items):
    """
    Retrieve a source item from an option ID like:
        conference::123
        byu::45
    """
    source_type, raw_index = option_id.split("::")
    index = int(raw_index)

    if source_type == "conference":
        item = get_talk_by_index(talks, index).copy()
        item["source_type"] = "conference_talk"
        item["source_label"] = "General Conference"
        item["display_index"] = index
        item["topics_for_comparison"] = item.get("official_topics", [])
        return item

    if source_type == "byu":
        item = get_byu_companion_by_index(byu_companion_items, index).copy()
        item["source_type"] = "byu_speech"
        item["source_label"] = "BYU Speeches"
        item["display_index"] = index
        item["topics_for_comparison"] = item.get("byu_topics", [])
        return item

    raise ValueError(f"Unknown source option: {option_id}")


def format_source_option(option_id, source_items_df):
    """
    Format a source option for a Streamlit selectbox.
    """
    row = source_items_df.loc[source_items_df["option_id"] == option_id].iloc[0]
    return f"{row['title']} — {row['speaker']} ({row['year']}) · {row['source_label']}"


def compare_label_lists(labels_a, labels_b):
    """
    Compare two label lists while preserving display labels.

    Returns
    -------
    tuple[list[str], list[str], list[str]]
        Shared labels, labels only in A, labels only in B.
    """
    labels_a = [label for label in labels_a if str(label).strip()]
    labels_b = [label for label in labels_b if str(label).strip()]

    norm_to_a = {str(label).strip().lower(): label for label in labels_a}
    norm_to_b = {str(label).strip().lower(): label for label in labels_b}

    set_a = set(norm_to_a.keys())
    set_b = set(norm_to_b.keys())

    shared_norm = sorted(set_a.intersection(set_b))
    only_a_norm = sorted(set_a.difference(set_b))
    only_b_norm = sorted(set_b.difference(set_a))

    shared = [norm_to_a[key] for key in shared_norm]
    only_a = [norm_to_a[key] for key in only_a_norm]
    only_b = [norm_to_b[key] for key in only_b_norm]

    return shared, only_a, only_b


def get_source_scripture_references(item):
    """
    Return scripture references for a source item.
    """
    return item.get("scripture_references", [])


def render_source_card(item, label):
    """
    Render a compact metadata card for a source item.
    """
    st.markdown(
        f"""
        <div class="study-card">
            <div class="small-label">{escape_html(label)}</div>
            <h3>{escape_html(item.get('title', ''))}</h3>
            <p><strong>Speaker:</strong> {escape_html(item.get('speaker', ''))}</p>
            <p><strong>Year:</strong> {escape_html(item.get('year', ''))}</p>
            <p><strong>Source:</strong> {escape_html(item.get('source_label', ''))}</p>
            <p>
                <a href="{escape_html(item.get('url', ''))}" target="_blank">
                    Open source
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_topic_sets(talk_a, talk_b):
    """
    Compare official topics between two talks.

    Returns
    -------
    tuple[list[str], list[str], list[str]]
        Shared topics, topics only in talk_a, topics only in talk_b.
    """
    topics_a = set(talk_a.get("official_topics", []))
    topics_b = set(talk_b.get("official_topics", []))

    shared = sorted(topics_a.intersection(topics_b))
    only_a = sorted(topics_a.difference(topics_b))
    only_b = sorted(topics_b.difference(topics_a))

    return shared, only_a, only_b


def get_scripture_sets(talk_a, talk_b):
    """
    Compare exact scripture references between two talks.

    Returns
    -------
    tuple[list[str], list[str], list[str]]
        Shared references, references only in talk_a, references only in talk_b.
    """
    refs_a = set(talk_a.get("scripture_references", []))
    refs_b = set(talk_b.get("scripture_references", []))

    shared = sorted(refs_a.intersection(refs_b))
    only_a = sorted(refs_a.difference(refs_b))
    only_b = sorted(refs_b.difference(refs_a))

    return shared, only_a, only_b


def get_all_official_topics(talks):
    """
    Return a sorted list of all official topic labels in the corpus.
    """
    topics = set()

    for talk in talks:
        topics.update(talk.get("official_topics", []))

    return sorted(topics)


def build_topic_study_path(topic, talks, path_length=7, path_style="Balanced"):
    """
    Build a lightweight study path for a selected official topic.

    This deployment version avoids similarity matrices and uses a simple,
    transparent ordering:
        - Balanced: newer talks from diverse speakers where possible
        - Recent: newest talks first
        - Classic: oldest talks first

    Parameters
    ----------
    topic : str
        Official topic label.
    talks : list[dict]
        Talk records.
    path_length : int
        Number of talks to include.
    path_style : str
        One of "Balanced", "Recent", or "Classic".

    Returns
    -------
    DataFrame
        Ordered study path.
    """
    candidates = [
        talk for talk in talks
        if topic in talk.get("official_topics", [])
    ]

    if not candidates:
        return pd.DataFrame()

    if path_style == "Recent":
        ordered = sorted(
            candidates,
            key=lambda talk: (talk.get("year") or 0, talk.get("title", "")),
            reverse=True,
        )

    elif path_style == "Classic":
        ordered = sorted(
            candidates,
            key=lambda talk: (talk.get("year") or 0, talk.get("title", "")),
        )

    else:
        # Balanced: start with recent talks but diversify speakers where possible.
        recent_first = sorted(
            candidates,
            key=lambda talk: (talk.get("year") or 0, talk.get("title", "")),
            reverse=True,
        )

        selected = []
        used_speakers = set()

        for talk in recent_first:
            speaker = talk.get("speaker", "")

            if speaker not in used_speakers:
                selected.append(talk)
                used_speakers.add(speaker)

            if len(selected) >= path_length:
                break

        if len(selected) < path_length:
            for talk in recent_first:
                if talk not in selected:
                    selected.append(talk)

                if len(selected) >= path_length:
                    break

        ordered = selected

    rows = []

    for step, talk in enumerate(ordered[:path_length], start=1):
        rows.append({
            "step": step,
            "index": talk.get("index"),
            "title": talk.get("title", ""),
            "speaker": talk.get("speaker", ""),
            "year": talk.get("year"),
            "official_topics": ", ".join(talk.get("official_topics", [])),
            "url": talk.get("url", ""),
        })

    return pd.DataFrame(rows)


# =============================================================================
# Rendering Helpers
# =============================================================================

def escape_html(value):
    """
    Escape text before inserting it into custom HTML.
    """
    return html.escape(str(value), quote=True)


def render_topic_chips(topics):
    """
    Render official topics as small visual chips.

    Parameters
    ----------
    topics : list[str]
        Topic labels.
    """
    if not topics:
        st.write("None found.")
        return

    chip_html = " ".join(
        f"<span class='topic-chip'>{escape_html(topic)}</span>"
        for topic in topics
        if str(topic).strip()
    )

    if chip_html:
        st.markdown(chip_html, unsafe_allow_html=True)
    else:
        st.write("None found.")


def render_topic_chip_string(topic_string):
    """
    Render a comma-separated topic string as chips.

    Parameters
    ----------
    topic_string : str
        Comma-separated topic labels.
    """
    if not topic_string:
        st.write("None found.")
        return

    topics = [
        topic.strip()
        for topic in topic_string.split(",")
        if topic.strip()
    ]

    render_topic_chips(topics)


def render_score(score_label, score):
    """
    Render a similarity score with consistent styling.

    Parameters
    ----------
    score_label : str
        Label for the score.
    score : float
        Numeric score.
    """
    st.markdown(
        f"<span class='score-pill'>{escape_html(score_label)}: {score:.3f}</span>",
        unsafe_allow_html=True,
    )


def render_scripture_reference_list(references):
    """
    Render a readable list of scripture references.

    Parameters
    ----------
    references : list[str]
        Extracted scripture references.
    """
    if not references:
        st.write("No extracted scripture references found.")
        return

    st.write(", ".join(references))


# =============================================================================
# Streamlit Page Setup
# =============================================================================

st.set_page_config(
    page_title="General Conference Study Tools",
    page_icon="📖",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-header {
        padding: 1.25rem 1.5rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #f7f4ee 0%, #ffffff 100%);
        border: 1px solid #e6dfd3;
        margin-bottom: 1.5rem;
    }

    .main-header h1 {
        margin-bottom: 0.25rem;
    }

    .subtle-text {
        color: #666666;
        font-size: 0.95rem;
        line-height: 1.55;
    }

    .study-card {
        padding: 1.1rem 1.25rem;
        border-radius: 1rem;
        border: 1px solid #e6e6e6;
        background-color: #ffffff;
        margin-bottom: 1rem;
    }

    .small-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #777777;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    .topic-chip {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        margin: 0.15rem 0.2rem 0.15rem 0;
        border-radius: 999px;
        background-color: #f1f3f5;
        border: 1px solid #dee2e6;
        font-size: 0.82rem;
    }

    .score-pill {
        display: inline-block;
        padding: 0.28rem 0.6rem;
        margin: 0.25rem 0 0.35rem 0;
        border-radius: 999px;
        background-color: #eef6ff;
        border: 1px solid #cfe8ff;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .purpose-box {
        padding: 1rem 1.25rem;
        border-left: 4px solid #9a7b4f;
        background-color: #faf7f1;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }

    .section-note {
        padding: 0.8rem 1rem;
        border-radius: 0.75rem;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
        color: #555555;
        font-size: 0.95rem;
        line-height: 1.55;
    }

    a {
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-header">
        <h1>General Conference Study Tools</h1>
        <p class="subtle-text">
            Discover related General Conference talks, explore official topic connections,
            and find where scriptures are referenced across decades of conference addresses.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Purpose of this tool", expanded=False):
    st.markdown(
        """
        <div class="purpose-box">
        This tool is intended to help users discover official Church sources for deeper
        personal study. It does not define doctrine and should not replace scripture study,
        prophetic counsel, prayer, or the guidance of the Holy Ghost.
        </div>

        The <strong>Talk Recommender</strong> offers several ways of finding related talks:
        official-topic overlap, semantic similarity, and shared language or imagery.

        The <strong>Scripture Explorer</strong> helps locate General Conference talks that
        reference specific scriptures, chapters, or books.
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Load Data
# =============================================================================

try:
    (
        talks,
        recommendations_app,
        byu_companion_items,
        byu_companion_recs,
        study_paths_app,
    ) = load_app_data()
    talks_df = build_talks_df(talks)
    available_modes = get_recommendation_modes(recommendations_app)
    source_items_df = build_source_items_df(
        talks=talks,
        byu_companion_items=byu_companion_items,
    )
    byu_companions_available = (
    len(byu_companion_items) > 0
    and len(byu_companion_recs) > 0
)

except Exception as e:
    st.error("The app could not load the required app data files.")
    st.exception(e)
    st.stop()


# =============================================================================
# Sidebar Controls
# =============================================================================

with st.sidebar:
    st.header("Settings")

    if not available_modes:
        st.error("No recommendation modes were found in recommendations_app.json.")
        st.stop()

    recommendation_mode = st.selectbox(
        "Recommendation mode",
        options=available_modes,
        index=available_modes.index("Best Overall")
        if "Best Overall" in available_modes
        else 0,
    )

    st.caption(MODE_DESCRIPTIONS.get(recommendation_mode, ""))

    k = st.slider(
        "Number of recommendations",
        min_value=3,
        max_value=15,
        value=5,
        step=1,
    )

    show_byu_companions = st.checkbox(
        "Show BYU Speeches companions",
        value=True,
        disabled=not byu_companions_available,
    )

    if not byu_companions_available:
        st.caption("BYU companion data is not available in this deployment.")

    if byu_companions_available:
        st.caption(f"BYU companion items: {len(byu_companion_items):,}")

    with st.expander("Debug: app data status"):
        st.write("BYU item file exists:", BYU_COMPANION_ITEMS_PATH.exists())
        st.write("BYU rec file exists:", BYU_COMPANION_RECS_PATH.exists())

        if BYU_COMPANION_ITEMS_PATH.exists():
            st.write(
                "BYU item file size:",
                BYU_COMPANION_ITEMS_PATH.stat().st_size,
                "bytes",
            )

        if BYU_COMPANION_RECS_PATH.exists():
            st.write(
                "BYU rec file size:",
                BYU_COMPANION_RECS_PATH.stat().st_size,
                "bytes",
            )

        st.write("Loaded BYU companion items:", len(byu_companion_items))
        st.write("Loaded BYU companion rec keys:", len(byu_companion_recs))
        st.write("BYU companions available:", byu_companions_available)

    st.divider()

    speaker_filter = st.text_input(
        "Optional speaker filter",
        placeholder="Holland, Nelson, Uchtdorf...",
    )

    year_filter = st.text_input(
        "Optional year filter",
        placeholder="2013",
    )

    st.divider()

    st.caption(f"Loaded {len(talks):,} talks.")
    st.caption("Data source: `app_data/`")
    st.caption(f"Mode: `{recommendation_mode}`")


# =============================================================================
# Tabs
# =============================================================================

talk_tab, scripture_tab, compare_tab, study_path_tab = st.tabs(
    ["Talk Recommender", "Scripture Explorer", "Compare Sources", "Study Path"]
)


# =============================================================================
# Talk Recommender Tab
# =============================================================================

with talk_tab:
    st.subheader("Talk Recommender")

    st.markdown(
        """
        <div class="section-note">
        Search for a General Conference talk, choose a recommendation mode, and explore
        related talks through different kinds of connection: doctrine, spiritual need,
        language, imagery, and official topic overlap.
        </div>
        """,
        unsafe_allow_html=True,
    )

    search_query = st.text_input(
        "Search for a talk",
        placeholder=(
            "Try: Like a Broken Vessel, Think Celestial, "
            "The Laborers in the Vineyard"
        ),
        key="talk_search_query",
    )

    filtered_df = talks_df.copy()

    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(
                search_query,
                case=False,
                na=False,
                regex=False,
            )
        ]

    if speaker_filter:
        filtered_df = filtered_df[
            filtered_df["speaker"].str.contains(
                speaker_filter,
                case=False,
                na=False,
                regex=False,
            )
        ]

    if year_filter:
        try:
            year_value = int(year_filter)
            filtered_df = filtered_df[filtered_df["year"] == year_value]
        except ValueError:
            st.warning("Year filter must be a number.")

    if not search_query:
        st.info("Search for a talk title to begin.")

    else:
        st.markdown("### Matching Talks")

        display_df = filtered_df[
            ["index", "title", "speaker", "year", "official_topics"]
        ].head(25)

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
        )

        if len(filtered_df) == 0:
            st.info("No matching talks found.")

        else:
            option_indices = filtered_df["index"].head(100).tolist()

            selected_index = st.selectbox(
                "Choose a talk",
                options=option_indices,
                format_func=lambda index: format_talk_option(index, talks_df),
                key="selected_talk_index",
            )

            selected_talk = get_talk_by_index(talks, selected_index)

            st.divider()

            left_col, right_col = st.columns([2, 1])

            with left_col:
                st.markdown("### Selected Talk")

                selected_title = escape_html(selected_talk.get("title", ""))
                selected_speaker = escape_html(selected_talk.get("speaker", ""))
                selected_year = selected_talk.get("year")
                selected_url = escape_html(selected_talk.get("url", ""))

                st.markdown(
                    f"""
                    <div class="study-card">
                        <div class="small-label">Selected Talk</div>
                        <h3>{selected_title}</h3>
                        <p><strong>Speaker:</strong> {selected_speaker}</p>
                        <p><strong>Year:</strong> {selected_year}</p>
                        <p>
                            <a href="{selected_url}" target="_blank">
                                Open talk on Church website
                            </a>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with right_col:
                selected_topics = selected_talk.get("official_topics", [])

                st.markdown("### Official Topics")
                render_topic_chips(selected_topics)

                selected_scriptures = selected_talk.get("scripture_references", [])

                with st.expander("Extracted scripture references"):
                    render_scripture_reference_list(selected_scriptures)

            st.divider()

            st.markdown("### You May Also Like")

            st.caption(f"Recommendation mode: **{recommendation_mode}**")
            st.caption(MODE_DESCRIPTIONS.get(recommendation_mode, ""))

            recommendations = get_precomputed_recommendations(
                selected_index,
                recommendation_mode,
                recommendations_app,
                talks,
                k=k,
            )

            score_label = MODE_SCORE_LABELS.get(
                recommendation_mode,
                "Recommendation score",
            )

            if not recommendations:
                st.info("No precomputed recommendations found for this talk and mode.")

            for rank, rec in enumerate(recommendations, start=1):
                rec_talk = get_talk_by_index(talks, rec["index"])
                overlap = shared_topics(selected_talk, rec_talk)

                with st.container(border=True):
                    st.markdown(f"### {rank}. {rec['title']}")

                    meta_col, topic_col = st.columns([1, 2])

                    with meta_col:
                        st.markdown(f"**Speaker:** {rec['speaker']}")
                        st.markdown(f"**Year:** {rec['year']}")
                        render_score(score_label, rec["score"])
                        st.markdown(f"[Open talk]({rec['url']})")

                    with topic_col:
                        st.markdown("**Shared official topics:**")
                        if overlap:
                            render_topic_chips(overlap)
                        else:
                            st.write("None")

                        rec_scriptures = rec_talk.get("scripture_references", [])

                        with st.expander("Extracted scripture references"):
                            render_scripture_reference_list(rec_scriptures)

                        if rec["official_topics"]:
                            with st.expander("All official topics for this recommendation"):
                                render_topic_chip_string(rec["official_topics"])
                        else:
                            st.markdown("**Official topics:** None found")

            if show_byu_companions and byu_companions_available:
                st.divider()

                st.markdown("### BYU Speeches Companion Sources")

                st.markdown(
                    """
                    <div class="section-note">
                    These companion sources come from BYU Speeches and are offered as
                    optional supplemental study material. General Conference remains the
                    primary recommendation source above.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                byu_companions = get_byu_companion_recommendations(
                    selected_index=selected_index,
                    byu_companion_items=byu_companion_items,
                    byu_companion_recommendations=byu_companion_recs,
                    k=k,
                )

                if not byu_companions:
                    st.info("No BYU companion sources found for this talk.")

                for rank, companion in enumerate(byu_companions, start=1):
                    with st.container(border=True):
                        st.markdown(f"### {rank}. {companion['title']}")

                        meta_col, source_col = st.columns([1, 2])

                        with meta_col:
                            st.markdown(f"**Speaker:** {companion['speaker']}")
                            st.markdown(f"**Year:** {companion['year']}")
                            st.markdown(
                                f"**BYU companion score:** `{companion['score']:.3f}`"
                            )
                            st.markdown(f"[Open BYU Speech]({companion['url']})")

                        with source_col:
                            st.markdown("**Source:**")
                            st.write(companion.get("collection", "BYU Speeches"))

                            if companion.get("speech_type"):
                                st.markdown("**Speech type:**")
                                st.write(companion["speech_type"])

                            if companion.get("date"):
                                st.markdown("**Date:**")
                                st.write(companion["date"])

                            if companion.get("byu_topics"):
                                st.markdown("**BYU topics:**")
                                render_topic_chips(companion["byu_topics"])


# =============================================================================
# Scripture Explorer Tab
# =============================================================================

with scripture_tab:
    st.subheader("Scripture Explorer")

    st.markdown(
        """
        <div class="section-note">
        Find General Conference talks that reference a scripture. Search by exact
        reference, chapter, or book. This tool is separate from the main recommender
        so scripture overlap remains a direct study pathway rather than a hidden
        ingredient in the recommendation score.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not any("scripture_references" in talk for talk in talks):
        st.warning(
            "The currently loaded talk data does not appear to include scripture "
            "references. Rebuild `talks_app.json` from the scripture-enriched dataset."
        )

    scripture_query = st.text_input(
        "Search for a scripture",
        placeholder="Try: Mosiah 3:19, Alma 7, John 3:16, D&C 121",
        key="scripture_query",
    )

    if not scripture_query:
        st.info("Enter a scripture reference to begin.")

    else:
        scripture_results = search_scripture_references(
            talks,
            scripture_query
        )

        if len(scripture_results) == 0:
            st.warning("No scripture references found for that search.")

        else:
            st.markdown(
                f"Found **{len(scripture_results)}** matching talks."
            )

            st.dataframe(
                scripture_results[
                    [
                        "title",
                        "speaker",
                        "year",
                        "match_type",
                        "matched_references",
                        "official_topics",
                    ]
                ].head(100),
                width="stretch",
                hide_index=True,
            )

            st.divider()

            st.markdown("### Matching Talks")

            for row in scripture_results.head(25).itertuples():
                with st.container(border=True):
                    st.markdown(f"### {row.title}")

                    meta_col, ref_col = st.columns([1, 2])

                    with meta_col:
                        st.markdown(f"**Speaker:** {row.speaker}")
                        st.markdown(f"**Year:** {row.year}")
                        st.markdown(f"**Match type:** {row.match_type}")
                        st.markdown(f"[Open talk]({row.url})")

                    with ref_col:
                        st.markdown("**Matched reference(s):**")
                        st.write(row.matched_references)

                        if row.official_topics:
                            with st.expander("Official topics"):
                                render_topic_chip_string(row.official_topics)
                        else:
                            st.markdown("**Official topics:** None found")

                        with st.expander("All extracted scripture references"):
                            if row.all_scripture_references:
                                st.write(row.all_scripture_references)
                            else:
                                st.write("No extracted references found.")


# =============================================================================
# Compare Sources Tab
# =============================================================================

with compare_tab:
    st.subheader("Compare Sources")

    st.markdown(
        """
        <div class="section-note">
        Select two study sources and compare their topics, scripture references,
        source metadata, and visible study connections. This can compare two
        General Conference talks, a Conference talk with a BYU Speech, or two
        BYU Speeches.
        </div>
        """,
        unsafe_allow_html=True,
    )

    source_filter_options = ["All", "General Conference", "BYU Speeches"]

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### First Source")

        source_a_filter = st.selectbox(
            "Source type",
            options=source_filter_options,
            index=0,
            key="compare_source_filter_a",
        )

        query_a = st.text_input(
            "Search first source",
            placeholder="Try: Like a Broken Vessel",
            key="compare_query_a",
        )

        speaker_a = st.text_input(
            "Optional speaker filter",
            placeholder="Holland, Nelson, Wilcox...",
            key="compare_speaker_a",
        )

        year_a = st.text_input(
            "Optional year filter",
            placeholder="2013",
            key="compare_year_a",
        )

        filtered_a = filter_source_items(
            source_items_df,
            query=query_a,
            speaker=speaker_a,
            year=year_a,
            source_label=source_a_filter,
        )

        if len(filtered_a) == 0:
            st.info("No matching first sources found.")
            selected_option_a = None
        else:
            option_ids_a = filtered_a["option_id"].head(100).tolist()

            selected_option_a = st.selectbox(
                "Choose first source",
                options=option_ids_a,
                format_func=lambda option_id: format_source_option(option_id, source_items_df),
                key="compare_selected_source_a",
            )

    with col_b:
        st.markdown("### Second Source")

        source_b_filter = st.selectbox(
            "Source type",
            options=source_filter_options,
            index=0,
            key="compare_source_filter_b",
        )

        query_b = st.text_input(
            "Search second source",
            placeholder="Try: Addressing Mental Health or His Grace Is Sufficient",
            key="compare_query_b",
        )

        speaker_b = st.text_input(
            "Optional speaker filter",
            placeholder="Holland, Nelson, Wilcox...",
            key="compare_speaker_b",
        )

        year_b = st.text_input(
            "Optional year filter",
            placeholder="2021",
            key="compare_year_b",
        )

        filtered_b = filter_source_items(
            source_items_df,
            query=query_b,
            speaker=speaker_b,
            year=year_b,
            source_label=source_b_filter,
        )

        if len(filtered_b) == 0:
            st.info("No matching second sources found.")
            selected_option_b = None
        else:
            option_ids_b = filtered_b["option_id"].head(100).tolist()

            selected_option_b = st.selectbox(
                "Choose second source",
                options=option_ids_b,
                format_func=lambda option_id: format_source_option(option_id, source_items_df),
                key="compare_selected_source_b",
            )

    if selected_option_a is None or selected_option_b is None:
        st.info("Select two sources to compare.")

    elif selected_option_a == selected_option_b:
        st.warning("Choose two different sources to compare.")

    else:
        item_a = get_source_item_by_option_id(
            selected_option_a,
            talks=talks,
            byu_companion_items=byu_companion_items,
        )

        item_b = get_source_item_by_option_id(
            selected_option_b,
            talks=talks,
            byu_companion_items=byu_companion_items,
        )

        st.divider()

        st.markdown("### Selected Sources")

        source_card_col_1, source_card_col_2 = st.columns(2)

        with source_card_col_1:
            render_source_card(item_a, "First Source")

        with source_card_col_2:
            render_source_card(item_b, "Second Source")

        st.divider()

        st.markdown("### Topic Comparison")

        topics_a = item_a.get("topics_for_comparison", [])
        topics_b = item_b.get("topics_for_comparison", [])

        shared_topics, only_a_topics, only_b_topics = compare_label_lists(
            topics_a,
            topics_b,
        )

        topic_col_1, topic_col_2, topic_col_3 = st.columns(3)

        with topic_col_1:
            st.markdown("**Shared topic labels**")
            render_topic_chips(shared_topics)

        with topic_col_2:
            st.markdown(f"**Only in {item_a.get('title', 'first source')}**")
            render_topic_chips(only_a_topics)

        with topic_col_3:
            st.markdown(f"**Only in {item_b.get('title', 'second source')}**")
            render_topic_chips(only_b_topics)

        if (
            item_a.get("source_type") != item_b.get("source_type")
            and not shared_topics
        ):
            st.caption(
                "Note: General Conference and BYU Speeches use different topic-label systems, "
                "so exact shared labels may be sparse even when the sources are meaningfully related."
            )

        st.divider()

        st.markdown("### Scripture Reference Comparison")

        refs_a = get_source_scripture_references(item_a)
        refs_b = get_source_scripture_references(item_b)

        shared_refs, only_a_refs, only_b_refs = compare_label_lists(
            refs_a,
            refs_b,
        )

        ref_col_1, ref_col_2, ref_col_3 = st.columns(3)

        with ref_col_1:
            st.markdown("**Shared scripture references**")
            render_scripture_reference_list(shared_refs)

        with ref_col_2:
            st.markdown(f"**Only in {item_a.get('title', 'first source')}**")
            render_scripture_reference_list(only_a_refs)

        with ref_col_3:
            st.markdown(f"**Only in {item_b.get('title', 'second source')}**")
            render_scripture_reference_list(only_b_refs)

        if item_a.get("source_type") == "byu_speech" or item_b.get("source_type") == "byu_speech":
            st.caption(
                "BYU scripture-reference extraction is not yet as complete as General Conference "
                "scripture-reference extraction, so this comparison may understate shared scriptures."
            )


# =============================================================================
# Study Path Tab
# =============================================================================

with study_path_tab:
    st.subheader("Study Path")

    st.markdown(
        """
        <div class="section-note">
        Build a guided study path from official General Conference topic labels.
        Each path is organized by study role rather than merely listing talks that
        share a topic.
        </div>
        """,
        unsafe_allow_html=True,
    )

    paths_available = (
        isinstance(study_paths_app, dict)
        and "topics" in study_paths_app
        and len(study_paths_app["topics"]) > 0
    )

    if not paths_available:
        st.warning(
            "Study Path v2 data is not available. Run "
            "`11_study_path_v2.ipynb` and make sure `study_paths_app.json` "
            "exists in `app_data/`."
        )

    else:
        all_topics = sorted(study_paths_app["topics"].keys())

        topic_col, settings_col = st.columns([2, 1])

        with topic_col:
            selected_topic = st.selectbox(
                "Choose an official topic",
                options=all_topics,
                index=all_topics.index("Jesus Christ")
                if "Jesus Christ" in all_topics
                else 0,
            )

        with settings_col:
            path_style = st.selectbox(
                "Path style",
                options=["Balanced", "Recent", "Classic"],
                index=0,
            )

        st.markdown("**Sources to include**")

        include_conference_in_path = st.checkbox(
            "General Conference",
            value=True,
            key="study_path_include_conference",
        )

        include_byu_in_path = st.checkbox(
            "BYU Speeches",
            value=True,
            key="study_path_include_byu",
            disabled=not byu_companions_available,
        )

        with st.expander("Future source types"):
            st.checkbox(
                "Preach My Gospel sections",
                value=False,
                disabled=True,
                key="study_path_include_pmg_disabled",
            )
            st.checkbox(
                "Scripture passages",
                value=False,
                disabled=True,
                key="study_path_include_scriptures_disabled",
            )
            st.checkbox(
                "Come, Follow Me sections",
                value=False,
                disabled=True,
                key="study_path_include_cfm_disabled",
            )
            st.checkbox(
                "Inspirational Messages / Videos",
                value=False,
                disabled=True,
                key="study_path_include_inspiration_disabled",
            )
            st.checkbox(
                "Scripture Videos",
                value=False,
                disabled=True,
                key="study_path_include_scripture_videos_disabled",
            )

        selected_path = study_paths_app["topics"][selected_topic][path_style]

        st.divider()

        st.markdown(f"### Study Path: {selected_topic}")

        st.caption(
            f"Style: **{path_style}** · "
            f"Candidate Conference talks: **{selected_path.get('candidate_count', 0)}**"
        )

        raw_path_items = selected_path.get("items", [])

        path_items = []

        for item in raw_path_items:
            source_type = item.get("source_type", "")

            if source_type == "conference_talk" and include_conference_in_path:
                path_items.append(item)

            elif source_type == "byu_speech" and include_byu_in_path:
                path_items.append(item)

        if not include_conference_in_path and not include_byu_in_path:
            st.warning("Choose at least one source type to include.")

        elif not path_items:
            st.info(
                "No study path items are available for the selected source combination."
            )

        else:
            for step_number, item in enumerate(path_items, start=1):
                source_type = item.get("source_type", "")

                with st.container(border=True):
                    st.markdown(f"### Step {step_number}: {item.get('role', 'Study')}")

                    meta_col, detail_col = st.columns([1, 2])

                    with meta_col:
                        st.markdown(f"**Title:** {item.get('title', '')}")
                        st.markdown(f"**Speaker:** {item.get('speaker', '')}")

                        if item.get("year"):
                            st.markdown(f"**Year:** {item.get('year')}")

                        if source_type == "conference_talk":
                            st.markdown("**Source:** General Conference")
                        elif source_type == "byu_speech":
                            st.markdown("**Source:** BYU Speeches")

                            if item.get("speech_type"):
                                st.markdown(f"**Type:** {item.get('speech_type')}")

                        if item.get("score") is not None:
                            st.markdown(f"**Path score:** `{item.get('score'):.3f}`")

                        if item.get("url"):
                            st.markdown(f"[Open source]({item.get('url')})")

                    with detail_col:
                        st.markdown("**Why this appears here:**")
                        st.write(item.get("reason", ""))

                        if source_type == "conference_talk":
                            topics = item.get("official_topics", [])

                            if topics:
                                st.markdown("**Official topics:**")
                                render_topic_chips(topics)

                        elif source_type == "byu_speech":
                            byu_topics = item.get("byu_topics", [])

                            if byu_topics:
                                st.markdown("**BYU topics:**")
                                render_topic_chips(byu_topics)

            if include_conference_in_path:
                scripture_anchors = selected_path.get("scripture_anchors", [])

                st.divider()

                st.markdown("### Scripture Anchors")

                if not scripture_anchors:
                    st.write("No scripture anchors were extracted for this path.")

                else:
                    scripture_df = pd.DataFrame(scripture_anchors)

                    st.dataframe(
                        scripture_df,
                        width="stretch",
                        hide_index=True,
                    )