import pandas as pd
import matplotlib.pyplot as plt

np_to_p = pd.read_excel(
    "data/np_to_power_before_after.xlsx",
    sheet_name=None
)

p_to_p = pd.read_excel(
    "data/power_to_power_before_after.xlsx",
    sheet_name=None
)

p_to_np = pd.read_excel(
    "data/power_to_non_power_before_after.xlsx",
    sheet_name=None
)


# Visual 1: Average Change in RB Rushing Attempts

transfer_groups = ["NP → P", "P → P", "P → NP"]

average_carry_changes = [
    np_to_p["RB"]["rushing_CAR_change"].mean(),
    p_to_p["RB"]["rushing_CAR_change"].mean(),
    p_to_np["RB"]["rushing_CAR_change"].mean()
]

fig, ax = plt.subplots(figsize=(10, 5))

colors = ["#D9534F", "#4C78A8", "#59A14F"]

bars = ax.barh(
    transfer_groups,
    average_carry_changes,
    color=colors,
    height=0.55
)

# Zero reference line
ax.axvline(0, color="#444444", linewidth=1)

# Add labels at the end of each bar
for bar, value in zip(bars, average_carry_changes):
    ax.annotate(
        f"{value:+.1f}",
        xy=(value, bar.get_y() + bar.get_height() / 2),
        xytext=(6 if value >= 0 else -6, 0),
        textcoords="offset points",
        ha="left" if value >= 0 else "right",
        va="center",
        fontsize=12,
        fontweight="bold"
    )

ax.set_title(
    "RBs Moving Up Lose Carries, While Those Moving Down Gain Them",
    fontsize=15,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Average Change in Rushing Attempts")
ax.invert_yaxis()

# Make room for labels
ax.set_xlim(
    min(average_carry_changes) - 20,
    max(average_carry_changes) + 20
)

# Remove unnecessary borders
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

ax.tick_params(axis="y", length=0)
ax.grid(axis="x", alpha=0.12)
ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# Visual 2: Average Change in RB Adjusted PPA

average_ppa_changes = [
    np_to_p["RB"]["adjPPA_change"].mean(),
    p_to_p["RB"]["adjPPA_change"].mean(),
    p_to_np["RB"]["adjPPA_change"].mean()
]

print("\nAverage Change in RB Adjusted PPA:")

for group, change in zip(transfer_groups, average_ppa_changes):
    print(group, round(change, 3))

fig, ax = plt.subplots(figsize=(10, 5))

colors = ["#D9534F", "#4C78A8", "#59A14F"]

bars = ax.barh(
    transfer_groups,
    average_ppa_changes,
    color=colors,
    height=0.55
)

ax.axvline(0, color="#444444", linewidth=1)

# Add values beside each bar
for bar, value in zip(bars, average_ppa_changes):
    label = "0.000" if abs(value) < 0.0005 else f"{value:+.3f}"

    ax.annotate(
        label,
        xy=(value, bar.get_y() + bar.get_height() / 2),
        xytext=(8 if value >= 0 else -8, 0),
        textcoords="offset points",
        ha="left" if value >= 0 else "right",
        va="center",
        fontsize=12,
        fontweight="bold"
    )

ax.set_title(
    "RBs Moving to Power Conferences See a Small Efficiency Decline",
    fontsize=15,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Average Change in Adjusted PPA")
ax.invert_yaxis()

ax.set_xlim(
    min(average_ppa_changes) - 0.008,
    max(average_ppa_changes) + 0.008
)

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

ax.tick_params(axis="y", length=0)
ax.grid(axis="x", alpha=0.12)
ax.set_axisbelow(True)

plt.tight_layout()
plt.show()

# Visual 3: RB Workload vs Efficiency

fig, ax = plt.subplots(figsize=(11, 6))

rb_groups = [
    (np_to_p["RB"], "NP → P", "#E63946"),
    (p_to_p["RB"], "P → P", "#2563EB"),
    (p_to_np["RB"], "P → NP", "#16A34A")
]

for data, label, color in rb_groups:
    ax.scatter(
        data["rushing_CAR_change"],
        data["adjPPA_change"],
        label=label,
        color=color,
        alpha=0.85,
        s=48,
        edgecolors="white",
        linewidths=0.4
    )

# Zero reference lines
ax.axhline(0, color="#555555", linewidth=1.2)
ax.axvline(0, color="#555555", linewidth=1.2)

# Title and labels
ax.set_title(
    "How RB Workload and Efficiency Change After Transferring",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_xlabel(
    "Change in Rushing Attempts",
    fontsize=12
)

ax.set_ylabel(
    "Change in Adjusted PPA",
    fontsize=12
)

# Light gridlines
ax.grid(
    color="#E5E7EB",
    linewidth=0.7,
    alpha=0.5
)

ax.set_axisbelow(True)

# Remove unnecessary borders
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

# Legend below the chart
ax.legend(
    title="Transfer Direction",
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=3,
    frameon=False,
    fontsize=11
)

plt.tight_layout()
plt.show()


# Visual 4: RB Performance Changes Across Five Metrics

rb_metrics = {
    "Rushing Attempts": "rushing_CAR_change",
    "Rushing Yards": "rushing_YDS_change",
    "Yards Per Carry": "rushing_YPC_change",
    "Rushing Touchdowns": "rushing_TD_change",
    "Adjusted PPA": "adjPPA_change"
}

rb_data = [
    np_to_p["RB"],
    p_to_p["RB"],
    p_to_np["RB"]
]

colors = ["#E63946", "#2563EB", "#16A34A"]

fig, axes = plt.subplots(5, 1, figsize=(11, 10))

for ax, (metric_name, column) in zip(axes, rb_metrics.items()):

    averages = [data[column].mean() for data in rb_data]

    # Put each transfer group on a separate line
    y_positions = [2, 1, 0]

    for value, y, color in zip(averages, y_positions, colors):
        ax.scatter(
            value,
            y,
            color=color,
            s=110,
            zorder=3
        )

        # Show the actual value next to each dot
        label = f"{value:+.3f}" if metric_name == "Adjusted PPA" else f"{value:+.1f}"

        ax.annotate(
            label,
            (value, y),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10
        )

    ax.axvline(0, color="#777777", linewidth=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(["NP → P", "P → P", "P → NP"])

    ax.set_title(
        metric_name,
        loc="left",
        fontsize=12,
        fontweight="bold"
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", alpha=0.12)
    ax.set_axisbelow(True)

fig.suptitle(
    "How RB Performance Changes After Transferring",
    fontsize=17,
    fontweight="bold",
    y=0.98
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()

# Visual 5: Percentage of RBs Who Improved or Declined

rb_groups = [
    np_to_p["RB"],
    p_to_p["RB"],
    p_to_np["RB"]
]

improved_percentages = []
declined_percentages = []
sample_sizes = []

for data in rb_groups:
    changes = data["rushing_YDS_change"].dropna()
    changes = changes[changes != 0]

    improved = (changes > 0).mean() * 100
    declined = (changes < 0).mean() * 100

    improved_percentages.append(improved)
    declined_percentages.append(declined)
    sample_sizes.append(len(changes))

# Create chart
fig, ax = plt.subplots(figsize=(10, 5))

colors = {
    "declined": "#D9534F",
    "improved": "#59A14F"
}

bars_declined = ax.barh(
    transfer_groups,
    declined_percentages,
    color=colors["declined"],
    label="Declined",
    height=0.55
)

bars_improved = ax.barh(
    transfer_groups,
    improved_percentages,
    left=declined_percentages,
    color=colors["improved"],
    label="Improved",
    height=0.55
)

# Add percentages inside each section
for i in range(len(transfer_groups)):
    declined = declined_percentages[i]
    improved = improved_percentages[i]

    ax.text(
        declined / 2,
        i,
        f"{declined:.0f}%",
        ha="center",
        va="center",
        color="white",
        fontsize=12,
        fontweight="bold"
    )

    ax.text(
        declined + improved / 2,
        i,
        f"{improved:.0f}%",
        ha="center",
        va="center",
        color="white",
        fontsize=12,
        fontweight="bold"
    )

# Labels and formatting
ax.set_xlim(0, 100)
ax.invert_yaxis()

ax.set_title(
    "Most RBs Moving to Power Conferences Lose Rushing Yards",
    fontsize=15,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Percentage of Running Backs")

# Remove unnecessary borders
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

ax.tick_params(axis="y", length=0)

# Legend
ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=2,
    frameon=False
)

# Add sample sizes
for i, n in enumerate(sample_sizes):
    ax.text(
        102,
        i,
        f"n={n}",
        va="center",
        fontsize=10
    )

ax.set_xlim(0, 112)

plt.tight_layout()
plt.show()

# Visual 6: RB Rushing Yard Changes by Season

fig, ax = plt.subplots(figsize=(11, 6))

rb_groups_with_labels = [
    (np_to_p["RB"], "NP → P", "#E63946"),
    (p_to_p["RB"], "P → P", "#2563EB"),
    (p_to_np["RB"], "P → NP", "#16A34A")
]

for data, label, color in rb_groups_with_labels:

    yearly_changes = (
        data.groupby("season")["rushing_YDS_change"]
        .mean()
        .reindex([2022, 2023, 2024, 2025])
    )

    print(f"\n{label} Average RB Rushing Yard Change by Season:")
    print(yearly_changes)

    ax.plot(
        yearly_changes.index,
        yearly_changes.values,
        marker="o",
        markersize=9,
        linewidth=3,
        color=color,
        label=label
    )

    # Label the last available data point
    last_values = yearly_changes.dropna()

    if not last_values.empty:
        last_year = last_values.index[-1]
        last_value = last_values.iloc[-1]

        ax.annotate(
            f"{label}: {last_value:+.0f}",
            xy=(last_year, last_value),
            xytext=(12, 0),
            textcoords="offset points",
            va="center",
            color=color,
            fontsize=11,
            fontweight="bold"
        )

# Zero reference line
ax.axhline(0, color="#555555", linewidth=1.2)

# Title and labels
ax.set_title(
    "How RB Rushing Yard Changes Vary by Transfer Season",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Transfer Season", fontsize=12)
ax.set_ylabel("Average Change in Rushing Yards", fontsize=12)

ax.set_xticks([2022, 2023, 2024, 2025])

# Make room for labels on the right
ax.set_xlim(2021.8, 2025.9)

# Clean up chart
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

ax.grid(
    axis="y",
    color="#E5E7EB",
    linewidth=0.8
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()