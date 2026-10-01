import pandas as pd

from adj_ppa import adj_ppa

FILES = {
    "transfers": ("data/transfers_2021_2025.xlsx", "data/transfers_2021_2025_adj.xlsx"),
    "non_transfers": ("data/non_transfers_2021_2025.xlsx", "data/non_transfers_2021_2025_adj.xlsx"),
}
POSITIONS = ["QB", "RB", "WR", "TE"]

# Combine both files so position averages are computed on every player,
frames = []
for source, (in_path, _) in FILES.items():
    df = pd.read_excel(in_path, sheet_name="All")
    df["source"] = source
    frames.append(df)

combined = adj_ppa(pd.concat(frames, ignore_index=True))

# Split back out and write each file with the same sheet layout as the original
for source, (_, out_path) in FILES.items():
    df = combined[combined["source"] == source].drop(columns="source")
    with pd.ExcelWriter(out_path) as writer:
        df.to_excel(writer, sheet_name="All", index=False)
        for position in POSITIONS:
            df[df["position"] == position].to_excel(writer, sheet_name=position, index=False)
    print(f"{source}: {len(df)} rows -> {out_path}")
