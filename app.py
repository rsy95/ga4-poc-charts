import streamlit as st
import pandas as pd
from google.analytics.data_v1beta import (
    BetaAnalyticsDataClient,
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="GA4 Insights POC",
    layout="wide",
)

st.title("📊 GA4 Insights Dashboard (POC)")

# -------------------------
# AUTH / CLIENT SETUP
# -------------------------
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["ga4"],
    scopes=["https://www.googleapis.com/auth/analytics.readonly"],
)

client = BetaAnalyticsDataClient(credentials=credentials)
PROPERTY_ID = st.secrets["ga4"]["property_id"]

# -------------------------
# DATE RANGE PICKER
# -------------------------
with st.sidebar:
    st.header("Filters")
    days = st.selectbox("Date Range", [7, 14, 30, 90], index=2)

# -------------------------
# GA4 DATA FUNCTIONS
# -------------------------
@st.cache_data(ttl=3600)
def get_users_sessions(days):
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        date_ranges=[
            DateRange(start_date=f"{days}daysAgo", end_date="today")
        ],
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        rows.append({
            "date": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=3600)
def get_top_pages():
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        limit=10,
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        rows.append({
            "page": row.dimension_values[0].value,
            "views": int(row.metric_values[0].value),
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_traffic_sources():
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="sessionSource")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        limit=10,
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        rows.append({
            "source": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value),
        })

    return pd.DataFrame(rows)

# -------------------------
# LOAD DATA
# -------------------------
df_trend = get_users_sessions(days)
df_pages = get_top_pages()
df_sources = get_traffic_sources()

# -------------------------
# KPI METRICS
# -------------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "Active Users",
    f"{df_trend['users'].sum():,}"
)

col2.metric(
    "Sessions",
    f"{df_trend['sessions'].sum():,}"
)

col3.metric(
    "Avg Users / Day",
    f"{int(df_trend['users'].mean()):,}"
)

# -------------------------
# CHARTS
# -------------------------
st.subheader("📈 Traffic Over Time")
st.line_chart(
    df_trend.set_index("date")[["users", "sessions"]]
)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📄 Top Pages")
    st.bar_chart(
        df_pages.set_index("page")["views"]
    )

with col_right:
    st.subheader("🌍 Traffic Sources")
    st.bar_chart(
        df_sources.set_index("source")["sessions"]
    )

# -------------------------
# RAW DATA (OPTIONAL)
# -------------------------
with st.expander("🔍 View Raw Data"):
    st.write("Trend Data", df_trend)
    st.write("Top Pages", df_pages)
    st.write("Traffic Sources", df_sources)
