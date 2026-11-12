import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection 

# browser tab title and full-width layout
st.set_page_config(
    page_title="NCAA Transfer Portal",
    layout="wide"
)

# conferences whose power status varies by season/team get split into two labels
# Notre Dame = Power Indpendent
MIXED_CONFERENCES = {"Pac-12", "FBS Independents"}

# Shared chart colors
IMPROVED_COLOR = "#3B82F6"
DECLINED_COLOR = "#EF4444"
NEUTRAL_COLOR = "#94A3B8"
BAR_COLOR = "#3B82F6"

# Table height that shows the top 10 by default but is scrollable
TEN_ROW_HEIGHT = 35 * 11 + 3

# Apply consistent formatting across Plotly charts
def apply_chart_style(fig):
    """Apply shared visual styling to Plotly charts."""

    fig.update_layout(
        template="plotly_dark",
        font=dict(
            family="Arial",
            size=15,
            color="#E2E8F0"
        ),
        title_font=dict(size=20),
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        hoverlabel=dict(font_size=13)
    )

    fig.update_xaxes(
        title_font=dict(size=15),
        tickfont=dict(size=15)
    )

    fig.update_yaxes(
        title_font=dict(size=15),
        tickfont=dict(size=15)
    )

    return fig

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


# Cache the remote sheet for one hour to limit requests while keeping updates fresh.
@st.cache_data(ttl=3600)
def load_transfers():
    """Load transfer data from the Google Sheet and pair it with prior-season stats."""
    connection = st.connection("gsheets", type=GSheetsConnection)
    # GSheetsConnection expects the numeric tab gid for public sheets, not its tab name.
    df = connection.read(ttl=3600)

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

def conference_filter(label, non_power, power, key):
    """Select all, power, non-power, or individual conferences."""

    selection = st.radio(
        label,
        ["All Conferences", "Power (P)", "Non-Power (NP)", "Custom"],
        horizontal=True,
        key=f"{key}_group"
    )

    if selection == "All Conferences":
        return non_power + power

    if selection == "Power (P)":
        return power

    if selection == "Non-Power (NP)":
        return non_power

    return st.multiselect(
        "Select individual conferences",
        options=non_power + power,
        default=non_power + power,
        key=f"{key}_custom"
    )


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
            line=dict(color=color, width=1), marker=dict(size=5, color=color),
            opacity=0.3 if len(data) > 40 else 0.7,
            hovertext=text, hoverinfo="text",
        ))

    #  gray line for the group average
    fig.add_trace(go.Scatter(
        x=["Before", "After"],
        y=[data[f"{stat}_before"].mean(), data[stat].mean()],
        mode="lines+markers", name="Group average",
        line=dict(color=NEUTRAL_COLOR, width=5), marker=dict(size=12, color=NEUTRAL_COLOR),
        hovertemplate=f"Average {stat_name}: %{{y:.{max(decimals, 1)}f}}<extra></extra>",
    ))  

    # Chart title, size, axis labels, and legend position
    fig.update_layout(
        title=f"Individual Player Performance: {stat_name}",
        height=600,
        margin=dict(l=70, r=20, t=70, b=20),
        xaxis=dict(
            categoryorder="array", categoryarray=["Before", "After"],
            tickvals=["Before", "After"],
            ticktext=["Before transfer", "After transfer"],
            range=[-0.15, 1.15],
        ),
        yaxis=dict(title=dict(text=stat_name, standoff=12), automargin=True, gridcolor="rgba(128,128,128,0.2)", zeroline=False),
        legend=dict(orientation="h", y=1.06, x=0, font=dict(size=15)),
        hovermode="closest",
    )
    fig = apply_chart_style(fig)

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
    ("Declined", DECLINED_COLOR),
    ("Unchanged", NEUTRAL_COLOR),
    ("Improved", IMPROVED_COLOR)
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
        title=f"Performance Outcomes: {stat_name}",
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
            x=0,
            font=dict(size=15)
        ),
        margin=dict(l=40, r=30, t=90, b=50)
    )

    fig = apply_chart_style(fig)

    return fig

def transfer_leaderboard(data, stat):
    """Find the biggest improvements and declines after transferring."""

    leaderboard = data.copy()

    before_col = f"{stat}_before"

    # Only include players with valid before-and-after data
    leaderboard = leaderboard.dropna(
        subset=[stat, before_col]
    ).copy()

    # Calculate performance change
    leaderboard["Change"] = (
        leaderboard[stat] - leaderboard[before_col]
    )

    # Only include players whose performance improved
    most_improved = (
        leaderboard[leaderboard["Change"] > 0]
        .sort_values("Change", ascending=False)
        .head(10)
    )

    # Only include players whose performance declined
    biggest_declines = (
        leaderboard[leaderboard["Change"] < 0]
        .sort_values("Change", ascending=True)
        .head(10)
    )

    return most_improved, biggest_declines

def apply_workload_requirements(data):
    """Keep players with enough opportunities in both seasons."""

    requirements = {
        "QB": ("passing_ATT", 100),
        "RB": ("rushing_CAR", 50),
        "WR": ("receiving_REC", 20),
        "TE": ("receiving_REC", 10),
    }

    eligible_groups = []

    for position, (column, minimum) in requirements.items():
        group = data[data["position"] == position].copy()

        group = group[
            (group[column] >= minimum)
            & (group[f"{column}_before"] >= minimum)
        ]

        eligible_groups.append(group)

    return pd.concat(eligible_groups, ignore_index=True)

def biggest_transfer_by_season(data, stat):
    """Find the biggest positive performance change in each transfer season."""

    seasonal_data = data.dropna(
        subset=["season", stat, f"{stat}_before"]
    ).copy()

    # Calculate each player's change after transferring
    seasonal_data["Change"] = (
        seasonal_data[stat] - seasonal_data[f"{stat}_before"]
    )

    # Only consider players whose statistic improved
    seasonal_data = seasonal_data[
        seasonal_data["Change"] > 0
    ]

    if seasonal_data.empty:
        return seasonal_data

    # Sort from the largest improvement to the smallest
    seasonal_data = seasonal_data.sort_values(
        "Change", ascending=False
    )

    # Keep the biggest improvement from each season
    seasonal_winners = seasonal_data.drop_duplicates(
        subset=["season"], keep="first"
    )

    return seasonal_winners.sort_values("season")

st.title("NCAA Football Transfer Portal")

pairs = load_transfers()


def render_position(position, filtered):
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

    # switch between chart types so only one chart shows at a time
    chart_type = st.radio(
        "Chart",
        ["Before vs. After", "Distribution of Changes", "Improved vs. Declined"],
        horizontal=True,
        key=f"chart_type_{position}"
    )

    if chart_type == "Before vs. After":
        fig = slope_chart(selected, stat, stat_name, decimals)

    elif chart_type == "Distribution of Changes":
        # Show the distribution of change for the selected metric
        fig = go.Figure(
            data=[go.Histogram(
                x=change,
                nbinsx=20,
                marker_color=BAR_COLOR
            )]
        )
        fig.add_vline(x=0, line_dash="dash", line_color=NEUTRAL_COLOR)
        fig.update_layout(
            title=f"Distribution of Changes: {stat_name}",
            xaxis_title=f"Change in {stat_name}",
            yaxis_title="Number of players",
        )
        fig = apply_chart_style(fig)

    else:
        fig = improvement_chart(selected, stat, stat_name)

    if fig is not None:
        st.plotly_chart(fig, width="stretch", key=f"chart_{position}")
    else:
        st.info("No players match the selected filters.")

def render_leaderboard(filtered):
    """Biggest improvements and declines for the Index page filters."""

    # Position selector
    leaderboard_position = st.selectbox(
        "Position",
        ["All Positions", "QB", "RB", "WR", "TE"],
        key="leaderboard_position"
    )

    # Choose statistics based on the selected position
    if leaderboard_position == "All Positions":
        leaderboard_metrics = [ADJ_PPA]
        leaderboard_data = filtered.copy()
    else:
        leaderboard_metrics = METRICS[leaderboard_position]
        leaderboard_data = filtered[
            filtered["position"] == leaderboard_position
        ].copy()

    # Statistic selector
    leaderboard_stat = st.selectbox(
        "Statistic",
        [metric[0] for metric in leaderboard_metrics],
        format_func=lambda stat: next(
            metric[1]
            for metric in leaderboard_metrics
            if metric[0] == stat
        ),
        key="leaderboard_stat"
    )

    # show name and decimal places for the selected stats
    stat_label, decimals = next(
        (label, places)
        for col, label, places in leaderboard_metrics
        if col == leaderboard_stat
    )

    # Count players before applying workload requirements
    total_players = len(leaderboard_data)

    # Apply automatic position-specific workload requirements
    leaderboard_data = apply_workload_requirements(leaderboard_data)

    # every eligible player ranked by change
    ranked = leaderboard_data.dropna(
        subset=[leaderboard_stat, f"{leaderboard_stat}_before"]
    ).copy()
    ranked["Change"] = ranked[leaderboard_stat] - ranked[f"{leaderboard_stat}_before"]
    ranked = ranked.sort_values("Change", ascending=False)

    if ranked.empty:
        st.info("No players match the selected filters.")
    else:
        display_data = ranked[
            [
                "name",
                "position",
                "prev_team",
                "team",
                f"{leaderboard_stat}_before",
                leaderboard_stat,
                "Change"
            ]
        ].copy()

        # Add ranking numbers
        display_data.insert(0, "Rank", range(1, len(display_data) + 1))

        #shorter labels for the table
        stat_short = {
            "passing_YPA": "YPA",
            "rushing_YPC": "YPC",
            "receiving_YPR": "YPR",
            "adjPPA": "Adj. PPA",
        }.get(leaderboard_stat, stat_label)

        before_label = f"Before {stat_short}"
        after_label = f"After {stat_short}"
        change_label = f"{stat_short} Change"

        display_data.columns = [
            "Rank", "Player", "Position", "Previous School",
            "New School", before_label, after_label, change_label
        ]

        #formatting
        def style_change(value):
            if value > 0:
                return "color: #4ADE80; font-weight: bold"
            elif value < 0:
                return "color: #F87171; font-weight: bold"
            return "color: #94A3B8"

        styled_data = display_data.style.map(
            style_change,
            subset=[change_label]
        ).format({
            before_label: f"{{:.{decimals}f}}",
            after_label: f"{{:.{decimals}f}}",
            change_label: f"{{:+.{decimals}f}}",
        })

        st.dataframe(
            styled_data,
            hide_index=True,
            width="stretch",
            height=TEN_ROW_HEIGHT
        )

    st.divider()

    eligible_players = len(leaderboard_data)
    excluded_players = total_players - eligible_players

    # Show eligibility summary
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Transfers", total_players)
    col2.metric("Eligible Transfers", eligible_players)
    col3.metric("Excluded Transfers", excluded_players)

    # Explain the requirements
    with st.expander("How do players qualify?"):
        st.write(
            "Players must meet the minimum workload requirement "
            "in BOTH their season before transferring and their "
            "first season after transferring."
        )

        st.table(pd.DataFrame({
            "Position": ["QB", "RB", "WR", "TE"],
            "Minimum Opportunities": [
                "100 passing attempts",
                "50 rushing attempts",
                "20 receptions",
                "10 receptions"
            ]
        }))

        st.caption(
            "These are provisional analytical thresholds, "
            "not official NCAA eligibility standards."
        )
    # Calculate the rankings using the selected position and statistic
    most_improved, biggest_declines = transfer_leaderboard(
        leaderboard_data, leaderboard_stat
    )

    # Switch between improvements and declines
    leaderboard_view = st.radio(
        "Leaderboard",
        ["Most Improved", "Biggest Declines"],
        horizontal=True,
        key="leaderboard_view"
    )

    if leaderboard_view == "Most Improved":
        results = most_improved
    else:
        results = biggest_declines

        # Featured player
    if not results.empty:
        top_player = results.iloc[0]

        if leaderboard_view == "Most Improved":
            featured_title = "TOP IMPROVEMENT"
            featured_color = "#4ADE80"
            featured_background = "#17271F"
            featured_border = "#285A3B"
        else:
            featured_title = "BIGGEST DECLINE"
            featured_color = "#F87171"
            featured_background = "#2B1B20"
            featured_border = "#6B3038"

        top_change = top_player["Change"]

        st.markdown(
            f"""
            <div style="
                background-color: {featured_background};
                border: 1px solid {featured_border};
                border-radius: 12px;
                padding: 20px 24px;
                margin: 14px 0 22px 0;
            ">
                <div style="
                    color: {featured_color};
                    font-size: 12px;
                    font-weight: 700;
                    letter-spacing: 1.5px;
                    margin-bottom: 12px;
                ">
                    🏆 {featured_title}
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 16px;
                    flex-wrap: wrap;
                ">
                    <div>
                        <div style="
                            color: #F8FAFC;
                            font-size: 24px;
                            font-weight: 700;
                        ">
                            {top_player["name"]}
                        </div>
                        <div style="
                            color: #B5C7BB;
                            font-size: 14px;
                            margin-top: 6px;
                        ">
                            {top_player["prev_team"]} → {top_player["team"]}
                        </div>
                    </div>
                    <div style="
                        color: {featured_color};
                        font-size: 30px;
                        font-weight: 700;
                    ">
                        {top_change:+.3f}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if results.empty:
        st.info("No players match the selected filters.")
    else:
        # Top 10 performance change chart
        
        # Keep the leaderboard ranking order
        chart_data = results.copy()

        # Add ranking numbers to player names
        chart_data["Ranked Player"] = [
            f"{i}. {name}"
            for i, name in enumerate(chart_data["name"], start=1)
        ]

        # Reverse only for Plotly so #1 appears at the top
        chart_data = chart_data.iloc[::-1]
        bar_color = (
            "#4ADE80"
            if leaderboard_view == "Most Improved"
            else "#F87171"
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=chart_data["Change"],
            y=chart_data["Ranked Player"],
            orientation="h",
            marker_color=bar_color,
            text=chart_data["Change"].apply(
                lambda x: f"{x:+.{decimals}f}"
            ),
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>"
                "Performance Change: %{x:+.3f}"
                "<extra></extra>"
            )
        ))

        fig.update_layout(
            title="Top 10 Performance Changes",
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=75, t=55, b=30),
            xaxis_title="Change",
            yaxis_title=None,
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Compare Two Players")

    comparison_data = leaderboard_data.dropna(
        subset=[leaderboard_stat, f"{leaderboard_stat}_before"]
    ).copy()

    comparison_data = comparison_data.reset_index(drop=True)

    if len(comparison_data) < 2:
        st.info("Not enough eligible transfers to compare.")
    else:
        comparison_data["Player Label"] = (
            comparison_data["name"].astype(str)
            + " ("
            + comparison_data["prev_team"].astype(str)
            + " → "
            + comparison_data["team"].astype(str)
            + ", "
            + comparison_data["season"].astype(str)
            + ")"
        )

                # Create a searchable list of eligible players
        player_options = comparison_data.index.tolist()

        col1, col2 = st.columns(2)

        with col1:
            player_1_index = st.selectbox(
                "Player 1",
                options=player_options,
                format_func=lambda i: comparison_data.loc[i, "Player Label"],
                index=0,
                placeholder="Search for Player 1",
                key="compare_player_1"
            )

        with col2:
            player_2_index = st.selectbox(
                "Player 2",
                options=player_options,
                format_func=lambda i: comparison_data.loc[i, "Player Label"],
                index=1,
                placeholder="Search for Player 2",
                key="compare_player_2"
            )

        if player_1_index == player_2_index:
            st.warning("Please select two different players.")
        else:
            player_1 = comparison_data.loc[player_1_index]
            player_2 = comparison_data.loc[player_2_index]

                    # Get the selected statistic
            before_col = f"{leaderboard_stat}_before"

            # Calculate performance changes
            player_1_change = (
                player_1[leaderboard_stat] - player_1[before_col]
            )

            player_2_change = (
                player_2[leaderboard_stat] - player_2[before_col]
            )

            # Create side-by-side comparison
            comparison_table = pd.DataFrame({
                "Statistic": [
                    "Player",
                    "Position",
                    "Previous School",
                    "New School",
                    "Transfer Year",
                    "Before Transfer",
                    "After Transfer",
                    "Change"
                ],
                "Player 1": [
                    player_1["name"],
                    player_1["position"],
                    player_1["prev_team"],
                    player_1["team"],
                    player_1["season"],
                    f"{player_1[before_col]:.{decimals}f}",
                    f"{player_1[leaderboard_stat]:.{decimals}f}",
                    f"{player_1_change:+.{decimals}f}"
                ],
                "Player 2": [
                    player_2["name"],
                    player_2["position"],
                    player_2["prev_team"],
                    player_2["team"],
                    player_2["season"],
                    f"{player_2[before_col]:.{decimals}f}",
                    f"{player_2[leaderboard_stat]:.{decimals}f}",
                    f"{player_2_change:+.{decimals}f}"
                ]
            })

            st.markdown("#### Player Comparison")
            st.dataframe(
                comparison_table,
                hide_index=True,
                width="stretch"
            )

                        # Before-and-after player comparison chart
            player_names = [
            player_1["name"],
            player_2["name"]
            ]

            fig_compare = go.Figure()

            fig_compare.add_trace(go.Bar(
                name="Before Transfer",
                x=player_names,
                y=[
                    player_1[before_col],
                    player_2[before_col]
                ],
                marker_color="#64748B",
                text=[
                    f"{player_1[before_col]:.{decimals}f}",
                    f"{player_2[before_col]:.{decimals}f}"
                ],
                textposition="outside"
            ))

            fig_compare.add_trace(go.Bar(
                name="After Transfer",
                x=player_names,
                y=[
                    player_1[leaderboard_stat],
                    player_2[leaderboard_stat]
                ],
                marker_color="#38BDF8",
                text=[
                    f"{player_1[leaderboard_stat]:.{decimals}f}",
                    f"{player_2[leaderboard_stat]:.{decimals}f}"
                ],
                textposition="outside"
            ))

                        # Improve chart appearance
            stat_label = next(
                metric[1]
                for metric in leaderboard_metrics
                if metric[0] == leaderboard_stat
            )

            fig_compare.update_layout(
                title=dict(
                    text=f"{stat_label}: Before vs. After Transfer",
                    font=dict(size=20, color="#F8FAFC"),
                    x=0
                ),
                barmode="group",
                template="plotly_dark",
                height=420,
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                font=dict(
                    family="Arial",
                    size=14,
                    color="#E2E8F0"
                ),
                xaxis=dict(
                    title=None,
                    showgrid=False,
                    tickfont=dict(size=14)
                ),
                yaxis=dict(
                    title=stat_label,
                    showgrid=True,
                    gridcolor="#29313C",
                    zeroline=True,
                    zerolinecolor="#64748B",
                    tickfont=dict(size=12)
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title=None
                ),
                margin=dict(l=45, r=20, t=100, b=45),
                bargap=0.35,
                bargroupgap=0.08,
                hovermode="x unified"
            )

            fig_compare.update_traces(
                textfont=dict(size=14),
                cliponaxis=False
            )

            st.plotly_chart(
                fig_compare,
                width="stretch"
            )

            # Dynamic player comparison insight
            st.markdown("#### Comparison Insight")

            difference = player_1_change - player_2_change

            if abs(difference) < 0.000001:
                insight = (
                    f"{player_1['name']} and {player_2['name']} "
                    "experienced the same performance change."
                )

            elif difference > 0:
                if player_1_change >= 0 and player_2_change >= 0:
                    explanation = "improved more than"
                elif player_1_change < 0 and player_2_change < 0:
                    explanation = "experienced a smaller decline than"
                else:
                    explanation = "had a more favorable performance change than"

                insight = (
                    f"{player_1['name']} {explanation} "
                    f"{player_2['name']}."
                )

            else:
                if player_1_change >= 0 and player_2_change >= 0:
                    explanation = "improved more than"
                elif player_1_change < 0 and player_2_change < 0:
                    explanation = "experienced a smaller decline than"
                else:
                    explanation = "had a more favorable performance change than"

                insight = (
                    f"{player_2['name']} {explanation} "
                    f"{player_1['name']}."
                )

            st.info(
                f"{insight} "
                f"{player_1['name']} changed by "
                f"{player_1_change:+.{decimals}f}, while "
                f"{player_2['name']} changed by "
                f"{player_2_change:+.{decimals}f}."
            )


    # Biggest transfer success by season
    st.divider()
    st.subheader("Biggest Transfer Success by Season (2022–2025)")

    st.write(
        "The player with the largest improvement in the selected "
        "statistic for each transfer season."
    )

    # Use the already-filtered and workload-eligible players
    seasonal_winners = biggest_transfer_by_season(
        leaderboard_data, leaderboard_stat
    )

    if seasonal_winners.empty:
        st.info("No qualifying improvements match the selected filters.")

    else:
        # Get the statistic's display name and decimal formatting
        stat_name, decimals = next(
            (label, decimals)
            for col, label, decimals in leaderboard_metrics
            if col == leaderboard_stat
        )

        
        # Prepare the seasonal winners table
        seasonal_table = seasonal_winners[
            [
                "season", "name", "position",
                "prev_team", "team",
                f"{leaderboard_stat}_before",
                leaderboard_stat, "Change"
            ]
        ].copy()

        seasonal_table.columns = [
            "Season", "Player", "Position",
            "Previous School", "New School",
            f"Before {stat_name}",
            f"After {stat_name}",
            "Change"
        ]

        # Highlight the strongest improvement
        highest_change = seasonal_table["Change"].max()

        def highlight_seasonal_change(value):
            if value == highest_change:
                return (
                    "background-color: #163B2B; "
                    "color: #4ADE80; font-weight: bold"
                )
            return "color: #4ADE80; font-weight: bold"

        styled_seasonal = (
            seasonal_table.style
            .map(highlight_seasonal_change, subset=["Change"])
            .format({
                f"Before {stat_name}": f"{{:.{decimals}f}}",
                f"After {stat_name}": f"{{:.{decimals}f}}",
                "Change": f"{{:+.{decimals}f}}"
            })
        )

        st.dataframe(
            styled_seasonal,
            hide_index=True,
            width="stretch",
            row_height=42
        )

        # Create a chart with player names and seasons
        chart_data = seasonal_winners.copy()
        chart_data["Label"] = (
            chart_data["name"].astype(str)
            + "<br>"
            + chart_data["season"].astype(int).astype(str)
        )

        highest_change = chart_data["Change"].max()

        chart_colors = [
            "#4ADE80" if value == highest_change else "#3B82F6"
            for value in chart_data["Change"]
        ]

        fig_season = go.Figure()

        fig_season.add_trace(go.Bar(
            x=chart_data["Label"],
            y=chart_data["Change"],
            marker=dict(
                color=chart_colors,
                line=dict(width=0)
            ),
            text=chart_data["Change"].apply(
                lambda value: f"{value:+.{decimals}f}"
            ),
            textposition="outside",
            textfont=dict(size=16, color="#F8FAFC"),
            cliponaxis=False,
            customdata=chart_data[
                ["name", "prev_team", "team", "season"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]} → %{customdata[2]}<br>"
                "Season: %{customdata[3]}<br>"
                "Improvement: %{y:+.3f}"
                "<extra></extra>"
            )
        ))

        fig_season.update_layout(
            title=dict(
                text=f"Top {stat_name} Improvement by Season",
                font=dict(size=21),
                x=0
            ),
            xaxis=dict(
                title=None,
                type="category",
                showgrid=False,
                tickfont=dict(size=13)
            ),
            yaxis=dict(
                title=f"Change in {stat_name}",
                gridcolor="rgba(148,163,184,0.15)",
                zeroline=False,
                rangemode="tozero"
            ),
            height=440,
            bargap=0.35,
            margin=dict(l=55, r=25, t=75, b=70),
            showlegend=False
        )

        fig_season = apply_chart_style(fig_season)

        st.plotly_chart(
            fig_season,
            width="stretch",
            key="seasonal_winners_chart"
        )


def metrics_page():
    """conference/year filters"""

    # conference options split into non-power and power
    non_power_from, power_from = power_split(zip(pairs["conf_label_before"], pairs["power_conf_before"]))
    non_power_to, power_to = power_split(zip(pairs["conf_label"], pairs["power_conf"]))

        # Two conference filters side by side
    side1, side2 = st.columns(2)

    with side1:
        st.subheader("Transferred from")

        from_confs = conference_filter(
            "Conferences before transfer",
            non_power_from,
            power_from,
            "from_confs"
        )

    with side2:
        st.subheader("Transferred to")

        to_confs = conference_filter(
            "Conferences after transfer",
            non_power_to,
            power_to,
            "to_confs"
        )

    # transfer year filter
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

    # one tab per position
    tabs = st.tabs(list(POSITION_TABS.values()))

    for tab, position in zip(tabs, POSITION_TABS):
        with tab:
            render_position(position, filtered)


def index_page():
    """Team and player index"""
    st.header("Index")

    # switch between the team index and the player leaderboard
    view = st.radio(
        "View",
        ["Teams", "Players"],
        horizontal=True,
        key="index_view",
    )

    data = pairs

    # defaulting to NP -> P transfers from every season and conference
    f1, f2, f3 = st.columns(3)
    with f1:
        conferences = st.multiselect(
            "Conference",
            sorted(data["fbs_conference"].dropna().unique()),
            key="index_confs",
            placeholder="All conferences",
        )
    with f2:
        directions = st.multiselect(
            "Transfer direction",
            ["NP->P", "P->NP", "P->P", "NP->NP"],
            default=["NP->P"],
            key="index_directions",
            placeholder="All directions",
        )
    with f3:
        seasons = st.multiselect(
            "Season",
            sorted(data["season"].dropna().unique()),
            key="index_seasons",
            placeholder="All seasons",
        )

    # no filter if nothing is selected
    if conferences:
        data = data[data["fbs_conference"].isin(conferences)]
    if directions:
        data = data[data["transfer_direction"].isin(directions)]
    if seasons:
        data = data[data["season"].isin(seasons)]

    if data.empty:
        st.info("No transfers match these filters.")
        return

    if view == "Players":
        render_leaderboard(data)
        return

    # transfers that have adjusted PPA at both schools
    data = data.dropna(subset=["adjPPA", "adjPPA_before"])

    if data.empty:
        st.info("No transfers match these filters.")
        return

    # conference and power status come from the team's most recent season in the selection
    # this should fix the pac 12 edge case
    data = data.assign(ppa_added=data["adjPPA"] - data["adjPPA_before"]).sort_values("season")
    teams = (
        data.groupby("team")
        .agg(
            conference=("fbs_conference", "last"),
            power=("power_conf", "last"),
            transfers=("id", "count"),
            ppa_added=("ppa_added", "sum"),
        )
        .reset_index()
        .sort_values("ppa_added", ascending=False)
    )
    teams["power"] = teams["power"].map({"Y": "Yes"}).fillna("No")

    st.dataframe(
        teams,
        hide_index=True,
        width="stretch",
        height=TEN_ROW_HEIGHT,
        column_config={
            "team": "Team",
            "conference": "Conference",
            "power": "Power",
            "transfers": st.column_config.NumberColumn("Transfers"),
            "ppa_added": st.column_config.NumberColumn("PPA Added", format="%+.3f"),
        },
    )


def glossary_page():
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

def player_profiles():
    st.header("Player Profiles")
    st.write("Search for a player to view their detailed stats, personal information, and performance trends.")

    if 'pairs' not in globals():
        st.error("The 'pairs' DataFrame is not defined.")
        return

    # Dropdown for Player Selection
    player_names = pairs["name"].dropna().unique()
    player_name = st.selectbox("Select Player Name", options=player_names, index=0)

    if player_name:
        player_data = pairs[pairs["name"] == player_name]

        if not player_data.empty:
            # Placeholder for Personal Information
            st.subheader(f"Personal Information for {player_name}")
            st.write("This section will include personal details like hometown, high school, and birth date")


            st.subheader(f"Stats for {player_name}")
            st.dataframe(player_data)

            st.subheader("Performance Trends")
            metrics = ["passing_YDS", "rushing_YDS", "receiving_YDS"]
            for metric in metrics:
                if metric in player_data.columns:
                    if len(player_data["season"].unique()) < 1:
                        st.warning(f"Not enough data to plot {metric} over time for {player_name}.")
                        continue

                    player_data = player_data.sort_values(by="season")
                    fig = px.line(
                        player_data,
                        x="season",
                        y=metric,
                        title=f"{metric} Over Time",
                        labels={"season": "Season", metric: metric},
                    )
                    st.plotly_chart(fig)
        else:
            st.warning(f"No data available for {player_name}.")

# New site menu
page = st.navigation(
    [
        st.Page(metrics_page, title="Metrics", url_path="metrics", default=True),
        st.Page(index_page, title="Index", url_path="index"),
        st.Page(glossary_page, title="Glossary", url_path="glossary"),
        st.Page(player_profiles, title="Player Profiles", url_path="player-profiles"),

    ],
    position="top",
)
page.run()
