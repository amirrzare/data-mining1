#!/usr/bin/env python3
"""Visualization of Sheypoor real-estate ads (sale / rent).

Usage:
    python realestate_visualization.py                      # reads data/sheypoor_all.csv
    python realestate_visualization.py --csv data/sale.csv --csv data/rent.csv

Outputs (PNG + summary.txt) go to the `output/` folder next to this script.
Labels are in English (no Persian font / reshaping needed).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).parent
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)
SUMMARY: list[str] = []

MIN_N_GROUP = 5  

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    plt.rcParams["font.family"] = ["Tahoma", "Arial", "DejaVu Sans"]  

    def fa(text: str) -> str:
        return get_display(arabic_reshaper.reshape(str(text)))

    HAS_FA = True
except ImportError:  
    HAS_FA = False

    def fa(text: str) -> str:
        return str(text)


# ------------------------------------------------------------------ helpers
def log(line: str = "") -> None:
    print(line)
    SUMMARY.append(line)


def describe(s: pd.Series, name: str, unit: str) -> None:
    s = s.dropna()
    if s.empty:
        log(f"{name}: no data")
        return
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((s < lo) | (s > hi)).sum())
    log(f"{name} ({unit}): n={len(s)} mean={s.mean():.2f} median={s.median():.2f} "
        f"std={s.std():.2f} min={s.min():.2f} max={s.max():.2f} "
        f"skew={s.skew():.2f} IQR-outliers={n_out}")


def hist_box(s: pd.Series, title: str, xlabel: str, fname: str, color: str = "#4C72B0") -> None:
    s = s.dropna()
    if len(s) < 3:
        log(f"[skip] {fname}: not enough data")
        return
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ax1.hist(s, bins=min(30, max(8, int(np.sqrt(len(s))) * 2)), color=color, edgecolor="white")
    ax1.axvline(s.mean(), color="red", ls="--", label=f"mean = {s.mean():.2f}")
    ax1.axvline(s.median(), color="green", ls="-", label=f"median = {s.median():.2f}")
    ax1.set_ylabel("Count")
    ax1.set_title(f"{title}  (n = {len(s)})")
    ax1.legend()
    ax2.boxplot(s, vert=False, widths=0.6, patch_artist=True,
                boxprops=dict(facecolor=color, alpha=0.6))
    ax2.set_yticks([])
    ax2.set_xlabel(xlabel)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=150)
    plt.close(fig)


def group_box(df: pd.DataFrame, col: str, by: str, title: str, ylabel: str,
              fname: str, top: int = 10, horizontal: bool = True, min_n: int = MIN_N_GROUP) -> None:
    counts = df.groupby(by)[col].count()
    keep = counts[counts >= min_n].sort_values(ascending=False).head(top).index.tolist()
    if len(keep) < 2:
        log(f"[skip] {fname}: fewer than 2 groups with n >= {min_n}")
        return
    data = [df.loc[df[by] == k, col].dropna() for k in keep]
    order = np.argsort([d.median() for d in data])
    keep = [keep[i] for i in order]
    data = [data[i] for i in order]
    fig, ax = plt.subplots(figsize=(10, max(4, 0.5 * len(keep) + 2)))
    ax.boxplot(data, vert=not horizontal, patch_artist=True,
               boxprops=dict(facecolor="#55A868", alpha=0.6))
    if HAS_FA:
        labels = [f"{fa(k)} (n={len(d)})" for k, d in zip(keep, data)]
    else:
        labels = [f"group {i + 1} (n={len(d)})" for i, d in enumerate(data)]
    if horizontal:
        ax.set_yticklabels(labels)
        ax.set_xlabel(ylabel)
    else:
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=150)
    plt.close(fig)

    log(f"  mapping for {fname} (low -> high median):")
    for i, (k, d) in enumerate(zip(keep, data), 1):
        log(f"    group {i}: {k}  n={len(d)}  median={d.median():.2f}")


def scatter(df: pd.DataFrame, x: str, y: str, title: str, xl: str, yl: str,
            fname: str, flag: str | None = None) -> None:
    d = df[[x, y] + ([flag] if flag else [])].dropna()
    if len(d) < 5:
        log(f"[skip] {fname}: not enough data")
        return
    fig, ax = plt.subplots(figsize=(8, 6))
    if flag:
        ok, bad = d[~d[flag]], d[d[flag]]
        ax.scatter(ok[x], ok[y], s=18, alpha=0.6, label=f"normal (n={len(ok)})")
        ax.scatter(bad[x], bad[y], s=40, color="red", marker="x", label=f"anomalous (n={len(bad)})")
        ax.legend()
    else:
        ax.scatter(d[x], d[y], s=18, alpha=0.6)
    r = d[x].corr(d[y])
    ax.set_title(f"{title}  (n = {len(d)}, r = {r:.2f})")
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=150)
    plt.close(fig)
    log(f"correlation {x} vs {y}: r = {r:.2f} (n={len(d)})")


# ------------------------------------------------------------------ loading
def load(paths: list[Path]) -> pd.DataFrame:
    frames = [pd.read_csv(p, encoding="utf-8-sig") for p in paths]
    df = pd.concat(frames, ignore_index=True).drop_duplicates("ad_id")
    for c in ["area_sqm", "rooms", "year_built", "sale_price_toman", "deposit_toman",
              "monthly_rent_toman", "daily_rent_toman"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["price_agreed"] = df["price_agreed"].astype(str).str.lower().eq("true")
    # cleaning: posted-time text ("ساعاتی پیش") sometimes leaks into `city` (card without location)
    for c in ("city", "neighborhood"):
        leak = df[c].astype(str).str.contains("پیش", na=False)
        df.loc[leak, c] = np.nan
    return df


def flag_anomalies(d: pd.DataFrame, col: str, min_n: int = 8, thr: float = 3.5,
                   ratio: float = 3.0) -> pd.Series:
    """Flag ads whose price per sqm is unusual *relative to their own city*.

    An ad is anomalous if either rule fires (cities with n >= min_n only):
      1) modified z-score on log(col):  |0.6745 * (x - median) / MAD| > 3.5
      2) ratio rule: value < median / 3  or  value > median * 3

    Rule 2 is needed because with small, mixed samples (e.g. 13 Tehran ads
    from 13 different neighborhoods) the MAD is large and rule 1 alone misses
    obvious cases such as 18 vs. a median of 205 million toman per sqm.
    Cities with fewer than `min_n` usable ads are not evaluated (no reliable
    baseline), so their ads are never flagged.
    """
    lg = np.log(d[col])
    flag = pd.Series(False, index=d.index)
    for _, idx in d.groupby("city").groups.items():
        if len(idx) < min_n:
            continue
        x = lg.loc[idx]
        med = x.median()
        mad = (x - med).abs().median()
        z_rule = (0.6745 * (x - med) / mad).abs() > thr if mad > 0 else pd.Series(False, index=idx)
        r_rule = (x < med - np.log(ratio)) | (x > med + np.log(ratio))
        flag.loc[idx] = z_rule | r_rule
    return flag


def evaluated_count(d: pd.DataFrame, min_n: int = 8) -> int:
    return int((d["city"].map(d["city"].value_counts()) >= min_n).sum())


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="append", help="CSV file(s) from sheypoor_scraper.py")
    args = ap.parse_args()
    paths = [Path(p) if Path(p).is_absolute() else BASE / p
             for p in (args.csv or ["data/sheypoor_all.csv"])]
    df = load(paths)

    # ---- 01: sample counts and filters
    log("=== Sample counts ===")
    log(f"total unique ads: {len(df)}")
    by_type = df["listing_type"].value_counts()
    for k, v in by_type.items():
        log(f"  {k}: {v}")
    log(f"price_agreed ads: {int(df['price_agreed'].sum())}")
    log(f"land/garden ads: {int((df['property_type'] == 'land').sum())}")

    res = df[df["property_type"] == "residential"].copy()
    # implausible placeholder prices (e.g. deposit = 200 toman, rent = 10 toman) -> invalid
    bad_dep = res["deposit_toman"].notna() & (res["deposit_toman"] < 1_000_000)
    bad_rent = res["monthly_rent_toman"].notna() & (res["monthly_rent_toman"] < 100_000)
    bad_sale = res["sale_price_toman"].notna() & (res["sale_price_toman"] < 500_000_000)
    invalid = res[bad_dep | bad_rent | bad_sale]
    log(f"ads with implausible placeholder prices: {len(invalid)} "
        f"(deposit<1M: {int(bad_dep.sum())}, rent<100k: {int(bad_rent.sum())}, sale<500M: {int(bad_sale.sum())})")
    invalid[["ad_id", "url", "title", "listing_type", "city", "area_sqm", "sale_price_toman",
             "deposit_toman", "monthly_rent_toman"]].to_csv(
        OUT / "invalid_price_ads.csv", index=False, encoding="utf-8-sig")
    res.loc[bad_dep, "deposit_toman"] = np.nan
    res.loc[bad_rent, "monthly_rent_toman"] = np.nan
    res.loc[bad_sale, "sale_price_toman"] = np.nan
    sale = res[(res["listing_type"] == "sale") & res["sale_price_toman"].gt(0) & res["area_sqm"].between(15, 2000)].copy()
    rent = res[(res["listing_type"] == "rent") & res["area_sqm"].between(15, 2000)
               & (res["monthly_rent_toman"].gt(0) | res["deposit_toman"].gt(0))].copy()
    sale["price_per_sqm"] = sale["sale_price_toman"] / sale["area_sqm"]
    rent["rent_per_sqm"] = rent["monthly_rent_toman"] / rent["area_sqm"]
    rent["rent_type"] = np.where(rent["monthly_rent_toman"].gt(0), "deposit + monthly rent", "full deposit (no rent)")
    log(f"usable residential sale ads (price>0, 15<=area<=2000): {len(sale)}")
    log(f"usable residential rent ads (rent or deposit>0, 15<=area<=2000): {len(rent)}")

    stages = {
        "all ads": len(df),
        "residential": len(res),
        "placeholder price": len(invalid),
        "sale (price agreed)": int(((df["listing_type"] == "sale") & df["price_agreed"]).sum()),
        "sale usable": len(sale),
        "rent usable": len(rent),
        "daily rent": int((df["listing_type"] == "daily_rent").sum()),
        "land": int((df["property_type"] == "land").sum()),
    }
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(stages.keys(), stages.values(), color="#4C72B0")
    ax.bar_label(bars)
    ax.set_ylabel("Number of ads")
    ax.set_title("Sample counts after each filter")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "01_sample_counts.png", dpi=150)
    plt.close(fig)

    # ---- 02..: sale
    log("\n=== SALE ===")
    if len(sale):
        sale["price_bn"] = sale["sale_price_toman"] / 1e9
        sale["ppsqm_m"] = sale["price_per_sqm"] / 1e6
        describe(sale["price_bn"], "sale price", "billion toman")
        describe(sale["area_sqm"], "area", "sqm")
        describe(sale["ppsqm_m"], "price per sqm", "million toman")
        hist_box(sale["price_bn"], "Sale price", "Price (billion toman)", "02_sale_price_hist_box.png")
        hist_box(sale["area_sqm"], "Area (sale ads)", "Area (sqm)", "03_sale_area_hist_box.png", "#DD8452")
        hist_box(sale["ppsqm_m"], "Sale price per sqm", "Price per sqm (million toman)",
                 "04_sale_ppsqm_hist_box.png", "#55A868")
        scatter(sale, "area_sqm", "price_bn", "Sale price vs area", "Area (sqm)",
                "Price (billion toman)", "05_sale_price_vs_area.png")
        group_box(sale, "ppsqm_m", "city", "Price per sqm by city (top by count)",
                  "Price per sqm (million toman)", "06_sale_ppsqm_by_city.png")
        sale["city_hood"] = sale["city"].fillna("?") + " / " + sale["neighborhood"].fillna("?")
        sale.loc[sale["neighborhood"].isna() | sale["city"].isna(), "city_hood"] = np.nan
        group_box(sale, "ppsqm_m", "city_hood", "Price per sqm by city / neighborhood (n >= 3)",
                  "Price per sqm (million toman)", "07_sale_ppsqm_by_neighborhood.png", min_n=3)
        r = sale.dropna(subset=["rooms"])
        r = r[r["rooms"] <= 6]
        if len(r) >= 5:
            group_box(r.assign(rooms=r["rooms"].astype(int).astype(str)), "price_bn", "rooms",
                      "Sale price by number of rooms", "Price (billion toman)",
                      "08_sale_price_by_rooms.png", top=7, horizontal=False)
        yr = sale["year_built"].dropna()
        yr = yr[yr.between(1330, 1410)]
        hist_box(yr, "Year built (Jalali)", "Year", "09_sale_year_hist_box.png", "#8172B3")

        # anomalies
        sale["anomaly"] = flag_anomalies(sale, "price_per_sqm")
        log(f"anomalous sale ads (z-score or 3x-median rule within city, n>=8): "
            f"{int(sale['anomaly'].sum())} of {evaluated_count(sale)} evaluated ads")
        scatter(sale, "area_sqm", "ppsqm_m", "Price per sqm vs area - anomalies in red",
                "Area (sqm)", "Price per sqm (million toman)", "10_sale_anomalies.png", flag="anomaly")
        cols = ["ad_id", "url", "city", "neighborhood", "area_sqm", "sale_price_toman", "price_per_sqm"]
        sale[sale["anomaly"]][cols].to_csv(OUT / "sale_anomalies.csv", index=False, encoding="utf-8-sig")

        # neighborhood table
        g = sale.groupby(["city", "neighborhood"])["price_per_sqm"].agg(["count", "median"])
        g = g[g["count"] >= 3].sort_values("median", ascending=False)
        g["median"] = (g["median"] / 1e6).round(2)
        g.rename(columns={"median": "median_ppsqm_million_toman"}).to_csv(
            OUT / "sale_neighborhood_table.csv", encoding="utf-8-sig")
        log(f"neighborhoods with n>=3: {len(g)} (saved sale_neighborhood_table.csv)")
    else:
        log("no usable sale ads")

    # ---- rent
    log("\n=== RENT ===")
    if len(rent):
        rent["deposit_m"] = rent["deposit_toman"] / 1e6
        rent["rent_m"] = rent["monthly_rent_toman"] / 1e6
        describe(rent["deposit_m"], "deposit", "million toman")
        describe(rent["rent_m"], "monthly rent", "million toman")
        describe(rent["area_sqm"], "area (rent)", "sqm")
        hist_box(rent["deposit_m"], "Deposit (rahn)", "Deposit (million toman)",
                 "11_rent_deposit_hist_box.png", "#C44E52")
        hist_box(rent["rent_m"], "Monthly rent", "Monthly rent (million toman)",
                 "12_rent_monthly_hist_box.png", "#DD8452")
        log("rent types: " + ", ".join(f"{k}={v}" for k, v in rent["rent_type"].value_counts().items()))
        fig, ax = plt.subplots(figsize=(7, 5))
        data = [rent.loc[rent["rent_type"] == k, "deposit_m"].dropna() for k in rent["rent_type"].unique()]
        ax.boxplot(data, patch_artist=True, boxprops=dict(facecolor="#C44E52", alpha=0.6))
        ax.set_xticklabels([f"{k}\n(n={len(d)})" for k, d in zip(rent["rent_type"].unique(), data)])
        ax.set_ylabel("Deposit (million toman)")
        ax.set_title("Deposit by rent type")
        fig.tight_layout()
        fig.savefig(OUT / "17_rent_deposit_by_type.png", dpi=150)
        plt.close(fig)
        for k, d in zip(rent["rent_type"].unique(), data):
            describe(d, f"deposit [{k}]", "million toman")
        both = rent[rent["monthly_rent_toman"].gt(0) & rent["deposit_toman"].gt(0)]
        if len(both) >= 5:
            describe(both["deposit_m"] / both["rent_m"], "deposit / monthly rent ratio", "x")
        scatter(rent, "area_sqm", "rent_m", "Monthly rent vs area", "Area (sqm)",
                "Monthly rent (million toman)", "13_rent_vs_area.png")
        scatter(rent, "deposit_m", "rent_m", "Monthly rent vs deposit", "Deposit (million toman)",
                "Monthly rent (million toman)", "14_rent_vs_deposit.png")
        group_box(rent, "rent_m", "city", "Monthly rent by city (top by count)",
                  "Monthly rent (million toman)", "15_rent_by_city.png")
        rr = rent.dropna(subset=["rent_per_sqm"])
        rr = rr[rr["rent_per_sqm"] > 0]
        if len(rr) >= 20:
            rr = rr.assign(anomaly=flag_anomalies(rr, "rent_per_sqm"))
            log(f"anomalous rent ads (z-score or 3x-median rule within city, n>=8): "
                f"{int(rr['anomaly'].sum())} of {evaluated_count(rr)} evaluated ads")
            rr[rr["anomaly"]][["ad_id", "url", "city", "neighborhood", "area_sqm",
                               "deposit_toman", "monthly_rent_toman"]].to_csv(
                OUT / "rent_anomalies.csv", index=False, encoding="utf-8-sig")
    else:
        log("no usable rent ads")

    # ---- correlation heatmap (sale)
    if len(sale) >= 10:
        cm = sale[["sale_price_toman", "area_sqm", "rooms", "year_built", "price_per_sqm"]].corr()
        fig, ax = plt.subplots(figsize=(6.5, 5.5))
        im = ax.imshow(cm, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(cm)), cm.columns, rotation=40, ha="right")
        ax.set_yticks(range(len(cm)), cm.columns)
        for i in range(len(cm)):
            for j in range(len(cm)):
                ax.text(j, i, f"{cm.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
        fig.colorbar(im)
        ax.set_title("Correlation matrix (sale ads)")
        fig.tight_layout()
        fig.savefig(OUT / "16_sale_correlation_heatmap.png", dpi=150)
        plt.close(fig)

    (OUT / "summary.txt").write_text("\n".join(SUMMARY), encoding="utf-8")
    print(f"\nDone. Charts and summary.txt are in: {OUT}")


if __name__ == "__main__":
    main()
