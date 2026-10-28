from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# browser tab title and full-width layout
st.set_page_config(
    page_title="NCAA Transfer Portal",
    layout="wide"
)

# player-season data for every transfer from 2021-2025
DATA_PATH = Path(__file__).parent / "data" / "transfers_2021_2025_adj.xlsx"

# conferences whose power status varies by season/team get split into two labels
# Notre Dame = Power Indpendent
MIXED_CONFERENCES = {"Pac-12", "FBS Independents"}

# Line colors
# blue if the player's stat went up, red if it went down
IMPROVED_COLOR = ("dodgerblue")
DECLINED_COLOR = "red"


# per-position metrics

ADJ_PPA = ("adjPPA", "Adjusted PPA", 3)
PASSING = [
    ("passing_ATT", "Pass Attempts", 0),
    ("passing_YDS", "Passing Yards", 0),
    ("passing_YPA", "Yards per Attempt", 2),
    ("passing_TD", "Passing TDs", 0),
]
RUSHING = [
    ("rushing_CAR", "Rush Attempts", 0),
    ("rushing_YDS", "Rushing Yards", 0),
    ("rushing_YPC", "Yards per Carry", 2),
    ("rushing_TD", "Rushing TDs", 0),
]
RECEIVING = [
    ("receiving_REC", "Receptions", 0),
    ("receiving_YDS", "Receiving Yards", 0),
    ("receiving_YPR", "Yards per Reception", 2),
    ("receiving_TD", "Receiving TDs", 0),
]

# Adjusted PPA comes first so it is the default stat in every tab
METRICS = {
    "QB": [ADJ_PPA] + PASSING,
    "RB": [ADJ_PPA] + RUSHING,
    "WR": [ADJ_PPA] + RECEIVING,
    "TE": [ADJ_PPA] + RECEIVING,
}

# Tab names in order
# QB first so it opens by default
POSITION_TABS = {"QB": "Quarterbacks", "RB": "Running Backs", "WR": "Wide Receivers", "TE": "Tight Ends"}

# Counting stats are blank when a player recorded none
COUNT_COLUMNS = [
    "passing_ATT", "passing_YDS", "passing_TD",
    "rushing_CAR", "rushing_YDS", "rushing_TD",
    "receiving_REC", "receiving_YDS", "receiving_TD",
]

# every stat column used by any position
STAT_COLUMNS = list(dict.fromkeys(col for metrics in METRICS.values() for col, _, _ in metrics))


def conference_label(conference, power_conf):
    """Name shown in the conference picker"""
    if conference in MIXED_CONFERENCES:
        return f"{conference} ({'P' if power_conf == 'Y' else 'NP'})"
    return conference


#cache so the excel file is only read once
@st.cache_data
def load_transfers():
    """One row per transfer stats after the transfer plus "_before" stats from the prior season"""
    df = pd.read_excel(DATA_PATH, sheet_name="All")

    # Treat missing counting stats as 0
    df[COUNT_COLUMNS] = df[COUNT_COLUMNS].fillna(0)
    df["conf_label"] = [
        conference_label(c, p) for c, p in zip(df["fbs_conference"], df["power_conf"])
    ]


    # FBS to FBS transfers only
    after = df[df["transfer_direction"].notna()].copy()
    before = df[["id", "season", "team", "conf_label", "power_conf", *STAT_COLUMNS]]

    # match each transfer season to the same player's previous season at their old team
    pairs = after.merge(
        before,
        left_on=["id", "prev_season", "prev_team"],
        right_on=["id", "season", "team"],
        suffixes=("", "_before"),
    )
    return pairs


def power_split(labels_with_power):
    """Split conference labels into non-power and power lists."""
    labels_with_power = list(labels_with_power)
    power = sorted({lbl for lbl, p in labels_with_power if p == "Y"})
    non_power = sorted({lbl for lbl, p in labels_with_power if p != "Y"})
    return non_power, power


def slope_chart(data, stat, stat_name, decimals):
    """line per player from their before value to their after value"""
    fig = go.Figure()

    # draw improved players in blue and declined players in red
    for improved, color, label in [
        (True, IMPROVED_COLOR, "Improved"),
        (False, DECLINED_COLOR, "Declined"),
    ]:
        group = data[(data[stat] >= data[f"{stat}_before"]) == improved]
        if group.empty:
            continue

        # One trace per group
        # None between players breaks the line so each player gets their own segment
        xs, ys, text = [], [], []
        for _, row in group.iterrows():
            xs += ["Before", "After", None]
            ys += [row[f"{stat}_before"], row[stat], None]

            # hovering over a players name shows their individual stats and teams

            hover = (
                f"<b>{row['name']}</b><br>"
                f"{row['prev_team']} → {row['team']} ({int(row['season'])})<br>"
                f"{stat_name}: {row[f'{stat}_before']:.{decimals}f} → {row[stat]:.{decimals}f}"
            )
            text += [hover, hover, None]

        # Fade the lines when there are lots of players so the chart stays readable
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers", name=f"{label} ({len(group)})",
            line=dict(color=color, width=1.5), marker=dict(size=8, color=color),
            opacity=0.5 if len(data) > 40 else 1,
            hovertext=text, hoverinfo="text",
        ))

    #  gray line for the group average
    fig.add_trace(go.Scatter(
        x=["Before", "After"],
        y=[data[f"{stat}_before"].mean(), data[stat].mean()],
        mode="lines+markers", name="Group average",
        line=dict(color="gray", width=4), marker=dict(size=12, color="gray"),
        hovertemplate=f"Average {stat_name}: %{{y:.{max(decimals, 1)}f}}<extra></extra>",
    ))

    # Chart size axis labels and legend position
    fig.update_layout(
        height=600,
        margin=dict(l=70, r=20, t=30, b=20),
        xaxis=dict(
            categoryorder="array", categoryarray=["Before", "After"],
            tickvals=["Before", "After"],
            ticktext=["Before transfer", "After transfer"],
            range=[-0.15, 1.15],
        ),
        yaxis=dict(title=dict(text=stat_name, standoff=12), automargin=True, gridcolor="rgba(128,128,128,0.2)", zeroline=False),
        legend=dict(orientation="h", y=1.06, x=0),
        hovermode="closest",
    )
    return fig

def improvement_chart(data, stat, stat_name):
    """Compare improvement percentages across transfer directions."""

    directions = ["NP->P", "P->P", "P->NP"]
    labels = ["NP → P", "P → P", "P → NP"]

    results = []

    for direction, label in zip(directions, labels):

        # Filter by transfer direction
        group = data[data["transfer_direction"] == direction]

        if group.empty:
            continue

        # Calculate each player's performance change
        changes = group[stat] - group[f"{stat}_before"]

        improved = (changes > 0).sum()
        declined = (changes < 0).sum()
        unchanged = (changes == 0).sum()

        total = len(group)

        results.append({
            "Direction": label,
            "Improved": improved / total * 100,
            "Declined": declined / total * 100,
            "Unchanged": unchanged / total * 100,
            "Players": total
        })

    if not results:
        return None

    results = pd.DataFrame(results)

    fig = go.Figure()

    categories = [
        ("Declined", "#E63946"),
        ("Unchanged", "#9CA3AF"),
        ("Improved", "#16A34A")
    ]

    for category, color in categories:

        fig.add_trace(go.Bar(
    y=[
        f"{direction} (n={players})"
        for direction, players in zip(results["Direction"], results["Players"])
    ],
    x=results[category],
            name=category,
            orientation="h",
            marker_color=color,
            text=[f"{v:.1f}%" if v >= 5 else "" for v in results[category]],
            textposition="inside",
            hovertemplate=(
                "%{y}<br>"
                + category + ": %{x:.1f}%"
                + "<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"How Players Perform After Transferring: {stat_name}",
        barmode="stack",
        height=380,
        xaxis=dict(
            title="Percentage of Players",
            range=[0, 100],
            ticksuffix="%"
        ),
        yaxis=dict(
            title="",
            categoryorder="array",
            categoryarray=[
    f"{direction} (n={players})"
    for direction, players in zip(
        results["Direction"][::-1],
        results["Players"][::-1]
    )
]
        ),
        legend=dict(
            orientation="h",
            y=1.12,
            x=0
        ),
        margin=dict(l=40, r=30, t=90, b=50)
    )

    return fig

def performance_chart(data, positiion):
    """Show average performance changes across transfer directions."""

    from plotly.subplots import make_subplots

    metrics = {
    "QB": [
        ("passing_ATT", "Pass Attempts", 1),
        ("passing_YDS", "Passing Yards", 1),
        ("passing_YPA", "Yards per Attempt", 2),
        ("passing_TD", "Passing Touchdowns", 1),
        ("adjPPA", "Adjusted PPA", 3),
    ],
    "RB": [
        ("rushing_CAR", "Rushing Attempts", 1),
        ("rushing_YDS", "Rushing Yards", 1),
        ("rushing_YPC", "Yards per Carry", 2),
        ("rushing_TD", "Rushing Touchdowns", 1),
        ("adjPPA", "Adjusted PPA", 3),
    ],
    "WR": [
        ("receiving_REC", "Receptions", 1),
        ("receiving_YDS", "Receiving Yards", 1),
        ("receiving_YPR", "Yards per Reception", 2),
        ("receiving_TD", "Receiving Touchdowns", 1),
        ("adjPPA", "Adjusted PPA", 3),
    ],
    "TE": [
        ("receiving_REC", "Receptions", 1),
        ("receiving_YDS", "Receiving Yards", 1),
        ("receiving_YPR", "Yards per Reception", 2),
        ("receiving_TD", "Receiving Touchdowns", 1),
        ("adjPPA", "Adjusted PPA", 3),
    ],
}[position]

    directions = [
        ("NP->P", "NP → P"),
        ("P->P", "P → P"),
        ("P->NP", "P → NP"),
    ]

    fig = make_subplots(
        rows=5,
        cols=1,
        subplot_titles=[metric[1] for metric in metrics],
        vertical_spacing=0.10,
    )

    for row_num, (stat, label, decimals) in enumerate(metrics, 1):

        for direction, direction_label in directions:

            group = data[
                data["transfer_direction"] == direction
            ].dropna(subset=[stat, f"{stat}_before"])

            if group.empty:
                continue

            change = (
                group[stat] - group[f"{stat}_before"]
            ).mean()

            color = "#16A34A" if change > 0 else "#E63946"

            fig.add_trace(
                go.Bar(
                    x=[change],
                    y=[direction_label],
                    orientation="h",
                    marker_color=color,
                    marker_line_width=0,
                    width=0.45,
                    text=[f"{change:+.{decimals}f}"],
                    textposition="outside",
                    cliponaxis=False,
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{direction_label}</b><br>"
                        f"{label}: %{{x:+.{decimals}f}}<br>"
                        f"Players: {len(group)}"
                        "<extra></extra>"
                    ),
                ),
                row=row_num,
                col=1,
            )

        fig.add_vline(
            x=0,
            line_color="#888888",
            line_width=1,
            row=row_num,
            col=1,
        )

        fig.update_yaxes(
            categoryorder="array",
            categoryarray=["P → NP", "P → P", "NP → P"],
            row=row_num,
            col=1,
        )

        fig.update_xaxes(
            zeroline=False,
            showgrid=False,
            row=row_num,
            col=1,
        )

    fig.update_layout(
        title=dict(
            text=f"Average {position} Performance Changes After Transferring",
            font=dict(size=23),
            x=0.5,
            xanchor="center",
        ),
        height=950,
        bargap=0.35,
        margin=dict(l=90, r=100, t=100, b=35),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )

    fig.update_annotations(
        font=dict(size=16, color="white")
    )

    return fig
st.title("NCAA Transfer Portal")

pairs = load_transfers()

# Conference options for each side split into non-power and power
non_power_from, power_from = power_split(zip(pairs["conf_label_before"], pairs["power_conf_before"]))
non_power_to, power_to = power_split(zip(pairs["conf_label"], pairs["power_conf"]))

# Two conference pickers side by side
side1, side2 = st.columns(2)
with side1:
    # Defaults to non-power conferences
    st.subheader("Transferred from")
    from_confs = st.multiselect(
        "Conferences before transfer",
        non_power_from + power_from,
        default=non_power_from,
        key="from_confs",
    )
with side2:
    # Defaults to power conferences
    st.subheader("Transferred to")
    to_confs = st.multiselect(
        "Conferences after transfer",
        non_power_to + power_to,
        default=power_to,
        key="to_confs",
    )

# Transfer year filter
years = sorted(pairs["season"].dropna().unique())
selected_years = st.multiselect(
    "Transfer year",
    years,
    default=years,
)    

# Keep only transfers between the selected conferences
filtered = pairs[
    pairs["conf_label_before"].isin(from_confs)
    & pairs["conf_label"].isin(to_confs)
    & pairs["season"].isin(selected_years)
]


def render_position(position):
    """Stat picker summary numbers and chart for one position tab."""

    # Stat dropdown with only this position's stats
    metrics = {col: (label, decimals) for col, label, decimals in METRICS[position]}
    stat = st.selectbox(
        "Statistic", list(metrics), format_func=lambda col: metrics[col][0],
        index=0, key=f"stat_{position}",
    )
    stat_name, decimals = metrics[stat]

    # Players at this position who have the stat for both seasons
    selected = filtered[filtered["position"] == position].dropna(subset=[stat, f"{stat}_before"])

    if selected.empty:
        st.info(f"No {POSITION_TABS[position].lower()} match these conferences.")
        return

    change = selected[stat] - selected[f"{stat}_before"]
    before_mean = selected[f"{stat}_before"].mean()
    after_mean = selected[stat].mean()
    mean_decimals = max(decimals, 1)
    mean_change = after_mean - before_mean
    improved_pct = (
        selected[stat] > selected[f"{stat}_before"]
    ).mean() * 100
    

    # Summary numbers above the chart
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Players", len(selected))
    m2.metric(f"Avg {stat_name} before", f"{before_mean:.{mean_decimals}f}")
    m3.metric(
        f"Avg {stat_name} after", f"{after_mean:.{mean_decimals}f}",
        delta=f"{after_mean - before_mean:+.{mean_decimals}f}",
    )
    m4.metric(f"Change in Avg {stat_name}",
              f"{mean_change:+.{mean_decimals}f}")
    m5.metric(f"% Improved {stat_name}", f"{improved_pct:.1f}%")

    st.plotly_chart(
        slope_chart(selected, stat, stat_name, decimals), width="stretch", key=f"chart_{position}"
    )

    # Show the distribution of change for the selected metric
    hist_fig = go.Figure(data=[go.Histogram(x=change, nbinsx=20)])
    hist_fig.add_vline(x=0, line_dash="dash", line_color="red")
    hist_fig.update_layout(
        title=f"Distribution of {stat_name} Change",
        xaxis_title=f"Change in {stat_name} (after - before)",
        yaxis_title="Number of players",
    )
    st.plotly_chart(
        hist_fig, width="stretch", key=f"hist_{position}"
    )
    #Parm -- Average Performance Change by Transfer Direction (position)
    if not filtered.empty:
        # Further filter the data to include only rows for the selected position
        position_filtered = filtered[filtered["position"] == position]
        if not position_filtered.empty:
            # Calculate the change in adjusted PPA (adjPPA) for each row
            # position_filtered["adjPPA_change"] = position_filtered["adjPPA"] - position_filtered["adjPPA_before"]
            position_filtered["stat_change"] = position_filtered[stat] - position_filtered[f"{stat}_before"]
            # Group the data by transfer direction and calculate the average adjPPA change for each group
            avg_stat_dir = (
                position_filtered.groupby("transfer_direction")["stat_change"].mean().reset_index()
                )
    # Define selected_position
    selected_position = position
    st.subheader(f"Average Performance Change by Transfer Direction ({POSITION_TABS[selected_position]})")
    fig_dir = px.bar(
        avg_stat_dir,
        x="transfer_direction",
        y="stat_change",
        labels={
            "transfer_direction": "Transfer Direction",
            "stat_change": f"Average {stat_name} Change",
        },
        color="transfer_direction",
    )
    # Remove legend from the bar chart
    fig_dir.update_layout(showlegend=False)
    # Display the bar chart in Streamlit
    st.plotly_chart(fig_dir,width="stretch", key=f"hist_{position}_direction")
        # Additional visualization for running backs only
    st.divider()
    st.subheader("Improvement vs. Decline")

    fig = improvement_chart(selected, stat, stat_name)

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key=f"improvement_chart_{position}"
       )
    else:
     st.info("No players match the selected filters.")

    st.divider()
    st.subheader("Performance by Metric")

    st.plotly_chart(
        performance_chart(selected, position),
        width="stretch",
        key=f"performance_chart_{position}"
    )


# Position tabs plus a glossary tab
tabs = st.tabs([*POSITION_TABS.values(), "Glossary"])

for tab, position in zip(tabs[:-1], POSITION_TABS):
    with tab:
        render_position(position)

with tabs[-1]:
    st.header("Glossary")
    st.subheader("1. Performance Metrics")
    st.markdown("""
    | Metric | Definition |
    | --- | --- |
    | **Role / Workload** | Measures how often a player is involved in the offense. |
    | **Production** | Measures the total yards a player produces during a season. |
    | **Efficiency** | Measures yards gained per passing attempt, rushing attempt, or reception. |
    | **Scoring** | Measures touchdowns produced by the player. |
    | **Advanced Efficiency** | Uses PPA-based statistics to measure performance beyond traditional box-score statistics. |
    """)

    st.subheader("2. Metrics by Position")
    st.markdown("""
    The same metric category uses a different statistic depending on the player's position.

    | Position | Workload | Production | Efficiency | Scoring |
    | --- | --- | --- | --- | --- |
    | **QB** | Pass Attempts | Passing Yards | Yards per Attempt | Passing TDs |
    | **RB** | Rush Attempts | Rushing Yards | Yards per Carry | Rushing TDs |
    | **WR** | Receptions | Receiving Yards | Yards per Reception | Receiving TDs |
    | **TE** | Receptions | Receiving Yards | Yards per Reception | Receiving TDs |
    """)
    st.markdown(
        "All positions also include **Adjusted PPA**"
    )

    st.subheader("3. Understanding the Dashboard")
    st.markdown("""
    | Term | Explanation |
    | --- | --- |
    | **Before Transfer** | Player's final recorded season at their previous school. |
    | **After Transfer** | Player's first recorded season at their new school. |
    | **Change** | After − Before. |
    | **% Improved** | Percentage of players whose selected metric increased. |
    | **Number of Players** | Number of players included in the current selection. |
    | **Transfer Year** | Season associated with the player's transfer. |
    """)

    st.subheader("4. Data & Limitations")
    st.markdown("""
    - **Data source:** [College Football Data](https://collegefootballdata.com/)
    - **Time period:** 2021–2025
    - **Limitations:** Some players have missing statistics or limited playing time. """
    )
