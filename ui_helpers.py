import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CHART_COLOR = "#E50914"

DARK_LAYOUT = dict(
    showlegend=False,
    plot_bgcolor="#111111",
    paper_bgcolor="#1a1a1a",
    font_color="#cccccc",
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#2a2a2a"),
    yaxis=dict(gridcolor="#2a2a2a"),
)

DARK_LAYOUT_LEGEND = dict(
    plot_bgcolor="#111111",
    paper_bgcolor="#1a1a1a",
    font_color="#cccccc",
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(bgcolor="#1a1a1a", bordercolor="#2a2a2a", font=dict(color="#cccccc")),
)

def setup_page():
    """Configure Streamlit page and inject global CSS."""
    st.set_page_config(
        page_title="Customer Churn Analytics",
        page_icon=":bar_chart:",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1rem;
            max-width: 1400px;
        }

        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #1c1c1c 0%, #242424 100%);
            border: 1px solid #E50914;
            border-radius: 10px;
            padding: 1.1rem 1.3rem;
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.15);
        }
        [data-testid="metric-container"] label {
            color: #aaaaaa;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #ffffff;
            font-size: 1.55rem;
            font-weight: 700;
        }

        .section-pill {
            display: inline-block;
            background: #E50914;
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            margin-bottom: 0.6rem;
        }

        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def section_pill(label):
    """Render a red pill-shaped section heading above a content block."""
    st.markdown(
        f'<div class="section-pill">{label}</div>', unsafe_allow_html=True
    )

def make_bar(data, x, y, x_label, y_label):
    """Return a dark-themed Plotly bar chart with a single red color."""
    fig = px.bar(
        data,
        x=x,
        y=y,
        color_discrete_sequence=[CHART_COLOR],
        labels={x: x_label, y: y_label},
    )
    fig.update_layout(**DARK_LAYOUT)
    fig.update_traces(marker_line_width=0)
    return fig

def make_grouped_bar(x_vals_a, y_vals_a, name_a,
                     x_vals_b, y_vals_b, name_b,
                     x_title, y_title):
    """Return a dark-themed grouped bar chart with gray (a) and red (b) bars."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=name_a,
        x=x_vals_a,
        y=y_vals_a,
        marker_color="#444444",
        marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name=name_b,
        x=x_vals_b,
        y=y_vals_b,
        marker_color=CHART_COLOR,
        marker_line_width=0,
    ))
    layout = dict(DARK_LAYOUT_LEGEND)
    layout["barmode"] = "group"
    layout["xaxis"] = dict(title=x_title, gridcolor="#2a2a2a")
    layout["yaxis"] = dict(title=y_title, gridcolor="#2a2a2a")
    fig.update_layout(**layout)
    return fig
