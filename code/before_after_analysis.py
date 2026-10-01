import pandas as pd

df = pd.read_excel("data/transfers_2021_2025_adj.xlsx", sheet_name="All")

np_to_power = df[df["transfer_direction"] == "NP->P"].copy()

print("NP to Power transfers:")
print(np_to_power.shape)

np_to_power["previous_season"] = np_to_power["season"] - 1

print("\nTransfer season and previous season:")
print(np_to_power[["name", "season", "previous_season", "prev_team", "team"]].head(10))

before_stats = df[
    [
        "id",
        "season",
        "team",
        "passing_ATT",
        "passing_YDS",
        "passing_YPA",
        "passing_TD",
        "rushing_CAR",
        "rushing_YDS",
        "rushing_YPC",
        "rushing_TD",
        "receiving_REC",
        "receiving_YDS",
        "receiving_YPR",
        "receiving_TD",
        "adjPPA"
    ]
].copy()

before_stats = before_stats.rename(columns={
    "season": "previous_season",
    "team": "before_team",
    "passing_ATT": "passing_ATT_before",
    "passing_YDS": "passing_YDS_before",
    "passing_YPA": "passing_YPA_before",
    "passing_TD": "passing_TD_before",
    "rushing_CAR": "rushing_CAR_before",
    "rushing_YDS": "rushing_YDS_before",
    "rushing_YPC": "rushing_YPC_before",
    "rushing_TD": "rushing_TD_before",
    "receiving_REC": "receiving_REC_before",
    "receiving_YDS": "receiving_YDS_before",
    "receiving_YPR": "receiving_YPR_before",
    "receiving_TD": "receiving_TD_before",
    "adjPPA": "adjPPA_before"
})

print("\nPrevious-season data:")
print(before_stats.head())

before_after = np_to_power.merge(
    before_stats,
    on=["id", "previous_season"],
    how="left"
)

before_after["team_match"] = before_after["before_team"] == before_after["prev_team"]

print("\nPrevious team matches:")
print(before_after["team_match"].value_counts())

valid_matches = before_after[before_after["team_match"]].copy()

print("\nValidated before/after matches:")
print(len(valid_matches))

valid_matches["passing_ATT_change"] = (
    valid_matches["passing_ATT"] - valid_matches["passing_ATT_before"]
)

valid_matches["passing_YDS_change"] = (
    valid_matches["passing_YDS"] - valid_matches["passing_YDS_before"]
)

valid_matches["passing_YPA_change"] = (
    valid_matches["passing_YPA"] - valid_matches["passing_YPA_before"]
)

valid_matches["passing_TD_change"] = (
    valid_matches["passing_TD"] - valid_matches["passing_TD_before"]
)

valid_matches["rushing_CAR_change"] = (
    valid_matches["rushing_CAR"] - valid_matches["rushing_CAR_before"]
)

valid_matches["rushing_YDS_change"] = (
    valid_matches["rushing_YDS"] - valid_matches["rushing_YDS_before"]
)

valid_matches["rushing_YPC_change"] = (
    valid_matches["rushing_YPC"] - valid_matches["rushing_YPC_before"]
)

valid_matches["rushing_TD_change"] = (
    valid_matches["rushing_TD"] - valid_matches["rushing_TD_before"]
)

valid_matches["receiving_REC_change"] = (
    valid_matches["receiving_REC"] - valid_matches["receiving_REC_before"]
)

valid_matches["receiving_YDS_change"] = (
    valid_matches["receiving_YDS"] - valid_matches["receiving_YDS_before"]
)

valid_matches["receiving_YPR_change"] = (
    valid_matches["receiving_YPR"] - valid_matches["receiving_YPR_before"]
)

valid_matches["receiving_TD_change"] = (
    valid_matches["receiving_TD"] - valid_matches["receiving_TD_before"]
)

valid_matches["adjPPA_change"] = (
    valid_matches["adjPPA"] - valid_matches["adjPPA_before"]
)

qb_output = valid_matches[valid_matches["position"] == "QB"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "passing_ATT_before", "passing_ATT", "passing_ATT_change",
        "passing_YDS_before", "passing_YDS", "passing_YDS_change",
        "passing_YPA_before", "passing_YPA", "passing_YPA_change",
        "passing_TD_before", "passing_TD", "passing_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

rb_output = valid_matches[valid_matches["position"] == "RB"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "rushing_CAR_before", "rushing_CAR", "rushing_CAR_change",
        "rushing_YDS_before", "rushing_YDS", "rushing_YDS_change",
        "rushing_YPC_before", "rushing_YPC", "rushing_YPC_change",
        "rushing_TD_before", "rushing_TD", "rushing_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

wr_output = valid_matches[valid_matches["position"] == "WR"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "receiving_REC_before", "receiving_REC", "receiving_REC_change",
        "receiving_YDS_before", "receiving_YDS", "receiving_YDS_change",
        "receiving_YPR_before", "receiving_YPR", "receiving_YPR_change",
        "receiving_TD_before", "receiving_TD", "receiving_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

te_output = valid_matches[valid_matches["position"] == "TE"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "receiving_REC_before", "receiving_REC", "receiving_REC_change",
        "receiving_YDS_before", "receiving_YDS", "receiving_YDS_change",
        "receiving_YPR_before", "receiving_YPR", "receiving_YPR_change",
        "receiving_TD_before", "receiving_TD", "receiving_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

with pd.ExcelWriter(
    "data/np_to_power_before_after.xlsx",
    engine="openpyxl"
) as writer:
    qb_output.to_excel(writer, sheet_name="QB", index=False)
    rb_output.to_excel(writer, sheet_name="RB", index=False)
    wr_output.to_excel(writer, sheet_name="WR", index=False)
    te_output.to_excel(writer, sheet_name="TE", index=False)

print("\nNP to Power Excel file created with QB, RB, WR, and TE sheets.")
# -----------------------------
# Power to Power
# -----------------------------

power_to_power = df[df["transfer_direction"] == "P->P"].copy()

print("\nPower to Power transfers:")
print(power_to_power.shape)

power_to_power["previous_season"] = power_to_power["season"] - 1

p_to_p_before_after = power_to_power.merge(
    before_stats,
    on=["id", "previous_season"],
    how="left"
)

p_to_p_before_after["team_match"] = (
    p_to_p_before_after["before_team"] == p_to_p_before_after["prev_team"]
)

valid_p_to_p = p_to_p_before_after[p_to_p_before_after["team_match"]].copy()

valid_p_to_p["passing_ATT_change"] = (
    valid_p_to_p["passing_ATT"] - valid_p_to_p["passing_ATT_before"]
)

valid_p_to_p["passing_YDS_change"] = (
    valid_p_to_p["passing_YDS"] - valid_p_to_p["passing_YDS_before"]
)

valid_p_to_p["passing_YPA_change"] = (
    valid_p_to_p["passing_YPA"] - valid_p_to_p["passing_YPA_before"]
)

valid_p_to_p["passing_TD_change"] = (
    valid_p_to_p["passing_TD"] - valid_p_to_p["passing_TD_before"]
)

valid_p_to_p["rushing_CAR_change"] = (
    valid_p_to_p["rushing_CAR"] - valid_p_to_p["rushing_CAR_before"]
)

valid_p_to_p["rushing_YDS_change"] = (
    valid_p_to_p["rushing_YDS"] - valid_p_to_p["rushing_YDS_before"]
)

valid_p_to_p["rushing_YPC_change"] = (
    valid_p_to_p["rushing_YPC"] - valid_p_to_p["rushing_YPC_before"]
)

valid_p_to_p["rushing_TD_change"] = (
    valid_p_to_p["rushing_TD"] - valid_p_to_p["rushing_TD_before"]
)

valid_p_to_p["receiving_REC_change"] = (
    valid_p_to_p["receiving_REC"] - valid_p_to_p["receiving_REC_before"]
)

valid_p_to_p["receiving_YDS_change"] = (
    valid_p_to_p["receiving_YDS"] - valid_p_to_p["receiving_YDS_before"]
)

valid_p_to_p["receiving_YPR_change"] = (
    valid_p_to_p["receiving_YPR"] - valid_p_to_p["receiving_YPR_before"]
)

valid_p_to_p["receiving_TD_change"] = (
    valid_p_to_p["receiving_TD"] - valid_p_to_p["receiving_TD_before"]
)

valid_p_to_p["adjPPA_change"] = (
    valid_p_to_p["adjPPA"] - valid_p_to_p["adjPPA_before"]
)

p_to_p_qb = valid_p_to_p[valid_p_to_p["position"] == "QB"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "passing_ATT_before", "passing_ATT", "passing_ATT_change",
        "passing_YDS_before", "passing_YDS", "passing_YDS_change",
        "passing_YPA_before", "passing_YPA", "passing_YPA_change",
        "passing_TD_before", "passing_TD", "passing_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

p_to_p_rb = valid_p_to_p[valid_p_to_p["position"] == "RB"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "rushing_CAR_before", "rushing_CAR", "rushing_CAR_change",
        "rushing_YDS_before", "rushing_YDS", "rushing_YDS_change",
        "rushing_YPC_before", "rushing_YPC", "rushing_YPC_change",
        "rushing_TD_before", "rushing_TD", "rushing_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

p_to_p_wr = valid_p_to_p[valid_p_to_p["position"] == "WR"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "receiving_REC_before", "receiving_REC", "receiving_REC_change",
        "receiving_YDS_before", "receiving_YDS", "receiving_YDS_change",
        "receiving_YPR_before", "receiving_YPR", "receiving_YPR_change",
        "receiving_TD_before", "receiving_TD", "receiving_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

p_to_p_te = valid_p_to_p[valid_p_to_p["position"] == "TE"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "receiving_REC_before", "receiving_REC", "receiving_REC_change",
        "receiving_YDS_before", "receiving_YDS", "receiving_YDS_change",
        "receiving_YPR_before", "receiving_YPR", "receiving_YPR_change",
        "receiving_TD_before", "receiving_TD", "receiving_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

with pd.ExcelWriter(
    "data/power_to_power_before_after.xlsx",
    engine="openpyxl"
) as writer:
    p_to_p_qb.to_excel(writer, sheet_name="QB", index=False)
    p_to_p_rb.to_excel(writer, sheet_name="RB", index=False)
    p_to_p_wr.to_excel(writer, sheet_name="WR", index=False)
    p_to_p_te.to_excel(writer, sheet_name="TE", index=False)

print("\nPower to Power Excel file created with QB, RB, WR, and TE sheets.")
# -----------------------------
# Power to Non-Power
# -----------------------------

power_to_non_power = df[df["transfer_direction"] == "P->NP"].copy()

print("\nPower to Non-Power transfers:")
print(power_to_non_power.shape)

power_to_non_power["previous_season"] = power_to_non_power["season"] - 1

p_to_np_before_after = power_to_non_power.merge(
    before_stats,
    on=["id", "previous_season"],
    how="left"
)

p_to_np_before_after["team_match"] = (
    p_to_np_before_after["before_team"] == p_to_np_before_after["prev_team"]
)

valid_p_to_np = p_to_np_before_after[p_to_np_before_after["team_match"]].copy()

valid_p_to_np["passing_ATT_change"] = (
    valid_p_to_np["passing_ATT"] - valid_p_to_np["passing_ATT_before"]
)

valid_p_to_np["passing_YDS_change"] = (
    valid_p_to_np["passing_YDS"] - valid_p_to_np["passing_YDS_before"]
)

valid_p_to_np["passing_YPA_change"] = (
    valid_p_to_np["passing_YPA"] - valid_p_to_np["passing_YPA_before"]
)

valid_p_to_np["passing_TD_change"] = (
    valid_p_to_np["passing_TD"] - valid_p_to_np["passing_TD_before"]
)

valid_p_to_np["rushing_CAR_change"] = (
    valid_p_to_np["rushing_CAR"] - valid_p_to_np["rushing_CAR_before"]
)

valid_p_to_np["rushing_YDS_change"] = (
    valid_p_to_np["rushing_YDS"] - valid_p_to_np["rushing_YDS_before"]
)

valid_p_to_np["rushing_YPC_change"] = (
    valid_p_to_np["rushing_YPC"] - valid_p_to_np["rushing_YPC_before"]
)

valid_p_to_np["rushing_TD_change"] = (
    valid_p_to_np["rushing_TD"] - valid_p_to_np["rushing_TD_before"]
)

valid_p_to_np["receiving_REC_change"] = (
    valid_p_to_np["receiving_REC"] - valid_p_to_np["receiving_REC_before"]
)

valid_p_to_np["receiving_YDS_change"] = (
    valid_p_to_np["receiving_YDS"] - valid_p_to_np["receiving_YDS_before"]
)

valid_p_to_np["receiving_YPR_change"] = (
    valid_p_to_np["receiving_YPR"] - valid_p_to_np["receiving_YPR_before"]
)

valid_p_to_np["receiving_TD_change"] = (
    valid_p_to_np["receiving_TD"] - valid_p_to_np["receiving_TD_before"]
)

valid_p_to_np["adjPPA_change"] = (
    valid_p_to_np["adjPPA"] - valid_p_to_np["adjPPA_before"]
)

p_to_np_qb = valid_p_to_np[valid_p_to_np["position"] == "QB"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "passing_ATT_before", "passing_ATT", "passing_ATT_change",
        "passing_YDS_before", "passing_YDS", "passing_YDS_change",
        "passing_YPA_before", "passing_YPA", "passing_YPA_change",
        "passing_TD_before", "passing_TD", "passing_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

p_to_np_rb = valid_p_to_np[valid_p_to_np["position"] == "RB"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "rushing_CAR_before", "rushing_CAR", "rushing_CAR_change",
        "rushing_YDS_before", "rushing_YDS", "rushing_YDS_change",
        "rushing_YPC_before", "rushing_YPC", "rushing_YPC_change",
        "rushing_TD_before", "rushing_TD", "rushing_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

p_to_np_wr = valid_p_to_np[valid_p_to_np["position"] == "WR"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "receiving_REC_before", "receiving_REC", "receiving_REC_change",
        "receiving_YDS_before", "receiving_YDS", "receiving_YDS_change",
        "receiving_YPR_before", "receiving_YPR", "receiving_YPR_change",
        "receiving_TD_before", "receiving_TD", "receiving_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

p_to_np_te = valid_p_to_np[valid_p_to_np["position"] == "TE"][
    [
        "name", "prev_team", "team", "previous_season", "season",
        "receiving_REC_before", "receiving_REC", "receiving_REC_change",
        "receiving_YDS_before", "receiving_YDS", "receiving_YDS_change",
        "receiving_YPR_before", "receiving_YPR", "receiving_YPR_change",
        "receiving_TD_before", "receiving_TD", "receiving_TD_change",
        "adjPPA_before", "adjPPA", "adjPPA_change"
    ]
]

with pd.ExcelWriter(
    "data/power_to_non_power_before_after.xlsx",
    engine="openpyxl"
) as writer:
    p_to_np_qb.to_excel(writer, sheet_name="QB", index=False)
    p_to_np_rb.to_excel(writer, sheet_name="RB", index=False)
    p_to_np_wr.to_excel(writer, sheet_name="WR", index=False)
    p_to_np_te.to_excel(writer, sheet_name="TE", index=False)

print("\nPower to Non-Power Excel file created with QB, RB, WR, and TE sheets.")