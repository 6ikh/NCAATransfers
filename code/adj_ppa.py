import pandas as pd

# Plays needed before a player's own avgPPA counts as much as the position average.
# Estimated from the 2021-2025 skill-position data
K_PLAYS = {"QB": 271, "RB": 231, "WR": 31, "TE": 36}


def add_adj_ppa(df: pd.DataFrame, k_plays: dict = K_PLAYS) -> pd.DataFrame:
    """Add `plays` and `adjPPA` columns
    adjPPA = (plays * avgPPA + k * position_avg) / (plays + k)
    plays is approximated with totalPPA / avgPPA
    """
    df = df.copy()

    # Plays calc breaks down when avgPPA is near 0, so fall back to touches.
    touches = df[["passing_ATT", "rushing_CAR", "receiving_REC"]].fillna(0).sum(axis=1)
    play_ratio = (df["totalPPA_all"] / df["avgPPA_all"]).where(df["avgPPA_all"].abs() >= 0.02)
    df["plays"] = play_ratio.round().fillna(touches)

    # Position average weighted by plays
    rated = df[df["avgPPA_all"].notna() & (df["plays"] > 0)]
    position_avg = (
        (rated["avgPPA_all"] * rated["plays"]).groupby(rated["position"]).sum()
        / rated.groupby("position")["plays"].sum()
    )

    prior = df["position"].map(position_avg)
    k = df["position"].map(k_plays)
    df["adjPPA"] = (df["plays"] * df["avgPPA_all"] + k * prior) / (df["plays"] + k)
    return df
