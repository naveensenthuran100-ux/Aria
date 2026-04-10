"""
Aria v2 — Chart Configurations
===============================
Configures high-end Altair data visualisations suitable for a native desktop feel.
"""

import altair as alt
import pandas as pd
import streamlit as st


def render_trend_graph(sessions_data, is_dark_mode=False):
    """
    Renders a premium Altair trend line graph based on session posture scores.
    Expects sessions_data to be a list of dictionaries, e.g. from get_recent_sessions().
    """
    if not sessions_data:
        # Empty state handling is usually done before calling this, but safe fallback
        st.markdown(
            '<div style="text-align:center;padding:40px;color:var(--text-muted);font-size:0.85rem;">'
            'Not enough data to display trend graph.'
            '</div>', 
            unsafe_allow_html=True
        )
        return

    # Extract relevant data
    # sessions_data is latest-first usually, so we reverse it for plotting left-to-right (old->new)
    df = pd.DataFrame(sessions_data)
    
    if "timestamp" not in df.columns or "posture_score" not in df.columns:
        return

    # Format timestamp
    df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime('%m-%d %H:%M')
    # Sort old to new for the x-axis
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # Style colors based on theme
    primary_col = "#A5B4FC" if is_dark_mode else "#6366F1"
    grid_col = "#333333" if is_dark_mode else "#E5E7EB"
    text_col = "#A1A1AA" if is_dark_mode else "#6B7280"

    chart = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(filled=False, fill="white", strokeWidth=2, size=60),
        strokeWidth=2,
        color=primary_col
    ).encode(
        x=alt.X('date:N', title=None, axis=alt.Axis(
             labelColor=text_col, 
             grid=True, 
             gridColor=grid_col, 
             gridDash=[2,2],
             domain=False, 
             ticks=False,
             labelAngle=-45
        )),
        y=alt.Y('posture_score:Q', title=None, scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(
             labelColor=text_col,
             grid=True,
             gridColor=grid_col,
             gridDash=[2,2],
             domain=False,
             ticks=False
        )),
        tooltip=[alt.Tooltip('date', title='Session Time'), alt.Tooltip('posture_score', title='Avg Posture Score')]
    ).properties(
        height=280
    ).configure_view(
        strokeWidth=0
    )

    st.altair_chart(chart, use_container_width=True)

def render_pie_chart(good_mins, bad_mins, is_dark_mode=False):
    """
    Renders an Altair donut chart for daily posture breakdown (Good vs Needs Improvement).
    """
    total_mins = good_mins + bad_mins
    if total_mins == 0:
        st.markdown(
            '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:0.85rem;">'
            'No posture data yet.'
            '</div>', 
            unsafe_allow_html=True
        )
        return

    df = pd.DataFrame({
        "Category": ["Good Posture", "Needs Improvement"],
        "Minutes": [good_mins, bad_mins]
    })
    
    # Determine colors based on themes
    good_color = "#34D399" if is_dark_mode else "#10B981"
    bad_color = "#F87171" if is_dark_mode else "#EF4444"
    text_col = "#E2E8F0" if is_dark_mode else "#1E293B"

    # Use theta to build pie
    base = alt.Chart(df).encode(
        theta=alt.Theta("Minutes:Q", stack=True),
        color=alt.Color("Category:N", scale=alt.Scale(
            domain=["Good Posture", "Needs Improvement"],
            range=[good_color, bad_color]
        ), legend=alt.Legend(title=None, labelColor=text_col)),
        tooltip=[alt.Tooltip("Category", title="Status"), alt.Tooltip("Minutes", title="Minutes Spent")]
    )

    pie = base.mark_arc(innerRadius=50, stroke="#fff", strokeWidth=1)

    chart = pie.properties(height=260).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)
