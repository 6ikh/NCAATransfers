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

print("Average Change in RB Rushing Attempts:")

for group, change in zip(transfer_groups, average_carry_changes):
    print(group, round(change, 2))

# Visual 1: Average Change in RB Rushing Attempts

plt.figure(figsize=(9, 5))

bars = plt.bar(
    transfer_groups,
    average_carry_changes,
    color=["#D9534F", "#4C78A8", "#59A14F"]
)

plt.axhline(0, color="black", linewidth=1)

plt.title("How Does Transferring Affect RB Workload?")
plt.ylabel("Average Change in Rushing Attempts")
plt.xlabel("Transfer Direction")

for bar, value in zip(bars, average_carry_changes):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value,
        f"{value:+.1f}",
        ha="center",
        va="bottom" if value >= 0 else "top"
    )

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

plt.figure(figsize=(9, 5))

bars = plt.bar(
    transfer_groups,
    average_ppa_changes,
    color=["#D9534F", "#4C78A8", "#59A14F"]
)

plt.axhline(0, color="black", linewidth=1)

plt.title("Average Change in RB Adjusted PPA After Transferring")
plt.ylabel("Average Change in Adjusted PPA")
plt.xlabel("Transfer Direction")

for bar, value in zip(bars, average_ppa_changes):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value,
        f"{value:+.3f}",
        ha="center",
        va="bottom" if value >= 0 else "top"
    )

plt.tight_layout()
plt.show()

# Visual 3: RB Workload Change vs Efficiency Change

plt.figure(figsize=(10, 6))

rb_groups = [
    (np_to_p["RB"], "NP → P", "#D9534F"),
    (p_to_p["RB"], "P → P", "#4C78A8"),
    (p_to_np["RB"], "P → NP", "#59A14F")
]

for data, label, color in rb_groups:
    plt.scatter(
        data["rushing_CAR_change"],
        data["adjPPA_change"],
        label=label,
        color=color,
        alpha=0.6
    )

plt.axhline(0, color="black", linewidth=1)
plt.axvline(0, color="black", linewidth=1)

plt.title("RB Workload Change vs Efficiency Change")
plt.xlabel("Change in Rushing Attempts")
plt.ylabel("Change in Adjusted PPA")
plt.legend()

plt.tight_layout()
plt.show()