import pandas as pd

df = pd.read_excel("data/transfers_2021_2025 1.xlsx", sheet_name="All")

# Non-Power to Power

print(df.shape)
print(df.head())

print("\nColumn names:")
print(df.columns.tolist())

print("\nTransfer direction counts:")
print(df["transfer_direction"].value_counts(dropna=False))

np_to_power = df[df["transfer_direction"] == "NP->P"].copy()

print("\nNP to Power rows:")
print(np_to_power.shape)

print("\nUnique NP to Power players:")
print(np_to_power["id"].nunique())

print("\nNP to Power players by position:")
print(np_to_power["position"].value_counts())

print("\nNP to Power players by season:")
print(np_to_power["season"].value_counts().sort_index())

print("\nNP to Power players by season and position:")
print(pd.crosstab(np_to_power["season"], np_to_power["position"]))

print("\nMissing values for key metrics:")
print(np_to_power[["usage_overall", "avgPPA_all"]].isna().sum())

print("\nAvailable values for key metrics:")
print(np_to_power[["usage_overall", "avgPPA_all"]].notna().sum())

#Power to Power
power_to_power = df[df["transfer_direction"] == "P->P"].copy()

print("\nPower to Power rows:")
print(power_to_power.shape)

print("\nUnique Power to Power players:")
print(power_to_power["id"].nunique())

print("\nPower to Power players by position:")
print(power_to_power["position"].value_counts())

print("\nPower to Power players by season:")
print(power_to_power["season"].value_counts().sort_index())

print("\nPower to Power players by season and position:")
print(pd.crosstab(power_to_power["season"], power_to_power["position"]))

print("\nPower to Power missing values for key metrics:")
print(power_to_power[["usage_overall", "avgPPA_all"]].isna().sum())

print("\nPower to Power available values for key metrics:")
print(power_to_power[["usage_overall", "avgPPA_all"]].notna().sum())

#Power to Non-Power
power_to_non_power = df[df["transfer_direction"] == "P->NP"].copy()

print("\nPower to Non-Power rows:")
print(power_to_non_power.shape)

print("\nUnique Power to Non-Power players:")
print(power_to_non_power["id"].nunique())

print("\nPower to Non-Power players by position:")
print(power_to_non_power["position"].value_counts())

print("\nPower to Non-Power players by season:")
print(power_to_non_power["season"].value_counts().sort_index())

print("\nPower to Non-Power players by season and position:")
print(pd.crosstab(power_to_non_power["season"], power_to_non_power["position"]))

print("\nPower to Non-Power missing values for key metrics:")
print(power_to_non_power[["usage_overall", "avgPPA_all"]].isna().sum())

print("\nPower to Non-Power available values for key metrics:")
print(power_to_non_power[["usage_overall", "avgPPA_all"]].notna().sum())