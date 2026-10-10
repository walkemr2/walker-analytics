"""Read-only Catalyst research monitor. Freshness is NOT production eligibility."""
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

REQUIRED = ('event_id', 'event_title', 'source_url', 'published_at', 'evidence_type', 'research_gate', 'gold_event_label')
FRESH_DAYS = 7
RECENT_DAYS = 30


def assess_freshness(published_at, as_of=None):
    """Classify publication age only. No event-date or material-change inference."""
    now = pd.Timestamp(as_of if as_of is not None else datetime.now(timezone.utc))
    if now.tzinfo is None:
        now = now.tz_localize('UTC')
    else:
        now = now.tz_convert('UTC')
    published = pd.to_datetime(published_at, utc=True, errors='coerce')
    if pd.isna(published):
        return 'UNKNOWN', None
    age = (now - published).total_seconds() / 86400
    if age < -1/24:
        return 'FUTURE_DATE_CHECK', round(age, 1)
    if age <= FRESH_DAYS:
        return 'NEW_PUBLICATION', round(max(age, 0), 1)
    if age <= RECENT_DAYS:
        return 'RECENT_CONTEXT', round(age, 1)
    return 'HISTORICAL', round(age, 1)


def render_shadow_monitor(csv_path):
    st.header('Catalyst Research Monitor')
    st.caption('RESEARCH ONLY · Publication freshness does not establish a new economic event or a trade signal.')
    path = Path(csv_path)
    if not path.is_file():
        st.info('Research register not found. Research Monitor is unavailable; core dashboard is unaffected.')
        return
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:
        st.warning(f'Research register could not be read: {type(exc).__name__}')
        return
    missing = [col for col in REQUIRED if col not in df.columns]
    if missing:
        st.warning('Research register schema mismatch: ' + ', '.join(missing))
        return
    df = df.drop_duplicates(subset=['event_id'], keep='first').copy()
    df['published_dt'] = pd.to_datetime(df['published_at'], utc=True, errors='coerce')
    df = df.sort_values('published_dt', ascending=False, na_position='last')
    now = datetime.now(timezone.utc)
    results = [assess_freshness(x, as_of=now) for x in df['published_at']]
    df['freshness'] = [x[0] for x in results]
    df['publication_age_days'] = [x[1] for x in results]
    a, b, c = st.columns(3)
    a.metric('Research candidates', len(df))
    b.metric('Unreviewed', int((df['gold_event_label'].str.upper() == 'UNREVIEWED').sum()))
    c.metric('Verified for production', 0)
    st.warning('Historical research snapshot, not a live catalyst feed. All records remain in research quarantine; no production eligibility is implied.')
    st.subheader('Publication freshness')
    st.caption(f'As of {now.strftime("%Y-%m-%d %H:%M UTC")}. NEW_PUBLICATION: 0–{FRESH_DAYS} days; RECENT_CONTEXT: >{FRESH_DAYS}–{RECENT_DAYS} days; HISTORICAL: >{RECENT_DAYS} days. These are configurable research thresholds, not trading thresholds.')
    st.info('Publication date ≠ economic measurement period ≠ detection date. ONGOING is never inferred from an old article: it requires independently verified, newly published material evidence. No ongoing-event determination is made here.')
    summary = df['freshness'].value_counts()
    cols = st.columns(4)
    for col, key in zip(cols, ('NEW_PUBLICATION', 'RECENT_CONTEXT', 'HISTORICAL', 'UNKNOWN')):
        col.metric(key.replace('_', ' ').title(), int(summary.get(key, 0)))
    types = sorted(x for x in df['evidence_type'].unique() if x)
    selected_types = st.multiselect('Evidence type', types, default=types, key='catalyst_research_evidence_type')
    statuses = sorted(df['freshness'].unique())
    selected_statuses = st.multiselect('Publication freshness', statuses, default=statuses, key='catalyst_research_freshness')
    view = df[df['evidence_type'].isin(selected_types) & df['freshness'].isin(selected_statuses)]
    st.caption(f'Showing {len(view)} of {len(df)} research candidates')
    for _, row in view.iterrows():
        with st.expander(f"{row['event_title']} · {row['evidence_type']} · {row['freshness']}"):
            st.write('**Published:**', row['published_at'] or 'Unknown')
            st.write('**Publication age (days):**', row['publication_age_days'] if row['publication_age_days'] is not None else 'Unknown')
            st.write('**Publication freshness:**', row['freshness'])
            st.write('**Research gate:**', row['research_gate'] or 'Not assessed')
            st.write('**Human label:**', row['gold_event_label'] or 'Unreviewed')
            for field, label in (('source_claim','Source claim'), ('blocking_check','Outstanding check'), ('measurement_period','Measurement period'), ('comparison_period','Comparison period'), ('review_justification','Review rationale')):
                if field in row and row[field]:
                    st.write(f'**{label}:**', row[field])
            if not row.get('measurement_period', ''):
                st.caption('Measurement/event date not independently normalized in this research register.')
            url = row['source_url']
            if isinstance(url, str) and url.startswith(('https://', 'http://')):
                st.link_button('Read original source', url)
    st.caption('Read-only snapshot. No changes to Decision Engine, Flow, Technical, production Catalyst data, or publishing scripts.')
