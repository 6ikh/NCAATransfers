import pandas as pd

df = pd.read_excel("data/transfers_2021_2025 1.xlsx", sheet_name="All")

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

