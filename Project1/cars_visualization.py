import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path

BASE = Path(__file__).parent          
CSV = BASE / "cars_test.csv"          
OUT = str(BASE / "output") + "/"      
Path(OUT).mkdir(exist_ok=True)        

df = pd.read_csv(CSV)
names = {"پارس": "Peugeot Pars", "206": "Peugeot 206", "207": "Peugeot 207",
         "G": "Shahin G", "V4": "Tara V4"}
df["car"] = df["model"].map(names)
df["price_b"] = df["price_toman"] / 1e9            
valid = df[df["price_valid"]].copy()               
order = ["Peugeot 206", "Peugeot Pars", "Shahin G", "Peugeot 207", "Tara V4"]
colors = dict(zip(order, ["#4C78A8", "#72B7B2", "#F58518", "#B279A2", "#E45756"]))
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})

# ---------- 1) number of samples ----------
fig, ax = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.3, 1]})
cnt = df["car"].value_counts().reindex(order)
cnt_valid = valid["car"].value_counts().reindex(order)
x = np.arange(len(order))
b1 = ax[0].bar(x - 0.2, cnt.values, 0.4, label="All ads found", color=[colors[o] for o in order])
b2 = ax[0].bar(x + 0.2, cnt_valid.values, 0.4, label="Ads with valid price", color=[colors[o] for o in order], alpha=0.45, hatch="//")
for b in list(b1) + list(b2):
    ax[0].text(b.get_x() + b.get_width() / 2, b.get_height() + 0.2, int(b.get_height()), ha="center")
ax[0].set_xticks(x); ax[0].set_xticklabels(order, rotation=15)
ax[0].set_ylabel("Number of samples"); ax[0].set_title("Samples per car model"); ax[0].set_ylim(0, 13); ax[0].legend(loc="upper center", ncol=2, frameon=False)
steps = [("Total ads scraped", len(df)),
         ("Price present", int(df["price_toman"].notna().sum())),
         ("Price valid", int(df["price_valid"].sum())),
         ("Used cars (km>0) with valid price", int(((~df["is_zero_km"]) & df["price_valid"]).sum()))]
labels, vals = zip(*steps)
bars = ax[1].barh(labels[::-1], vals[::-1], color="#54A24B")
for b in bars:
    ax[1].text(b.get_width() + 0.5, b.get_y() + b.get_height() / 2, int(b.get_width()), va="center")
ax[1].set_title("Sample count after each filter"); ax[1].set_xlim(0, 52)
fig.suptitle(f"Number of samples found: {len(df)}", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT + "01_sample_counts.png", dpi=150); plt.close(fig)

# ---------- helper: histogram + box plot sharing one axis ----------
def hist_box(series, title, xlabel, fname, bins=10, color="#4C78A8", fmt=None):
    s = series.dropna()
    fig, (axb, axh) = plt.subplots(2, 1, sharex=True, figsize=(9, 6),
                                   gridspec_kw={"height_ratios": [1, 3], "hspace": 0.05})
    axb.boxplot(s, vert=False, widths=0.6, patch_artist=True, showmeans=True,
                boxprops=dict(facecolor=color, alpha=0.6),
                flierprops=dict(marker="o", markerfacecolor="red", markeredgecolor="red"),
                medianprops=dict(color="black"),
                meanprops=dict(marker="D", markerfacecolor="white", markeredgecolor="black"))
    axb.set_yticks([]); axb.spines["left"].set_visible(False)
    axb.set_title(f"{title}  (n = {len(s)})", fontweight="bold")
    axh.hist(s, bins=bins, color=color, edgecolor="white", alpha=0.85)
    axh.axvline(s.median(), color="black", ls="--", label=f"Median = {s.median():,.2f}")
    axh.axvline(s.mean(), color="orange", ls="-", label=f"Mean = {s.mean():,.2f}")
    axh.set_xlabel(xlabel); axh.set_ylabel("Frequency"); axh.legend()
    fig.savefig(OUT + fname, dpi=150, bbox_inches="tight"); plt.close(fig)

hist_box(valid["price_b"], "Price distribution", "Price (billion Toman)", "02_price_hist_box.png", bins=10)
hist_box(df["mileage_km"] / 1000, "Mileage distribution", "Mileage (thousand km)", "03_mileage_hist_box.png", bins=10, color="#F58518")
hist_box(df["year_jalali"], "Model year distribution (Jalali)", "Model year (Jalali)", "04_year_hist_box.png", bins=12, color="#54A24B")

# ---------- 5) box plot of price per model (+ points) ----------
fig, ax = plt.subplots(figsize=(10, 6))
data = [valid.loc[valid["car"] == o, "price_b"] for o in order]
bp = ax.boxplot(data, tick_labels=[f"{o}\n(n={len(d)})" for o, d in zip(order, data)],
                patch_artist=True, showmeans=True, widths=0.55,
                medianprops=dict(color="black"),
                meanprops=dict(marker="D", markerfacecolor="white", markeredgecolor="black"))
for p, o in zip(bp["boxes"], order):
    p.set_facecolor(colors[o]); p.set_alpha(0.6)
rng = np.random.default_rng(0)
for i, d in enumerate(data, 1):
    ax.scatter(rng.normal(i, 0.05, len(d)), d, color="black", s=14, zorder=3)
ax.set_ylabel("Price (billion Toman)"); ax.set_title("Price by car model", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT + "05_price_by_model_box.png", dpi=150); plt.close(fig)

# ---------- 6) price vs mileage scatter ----------
fig, ax = plt.subplots(figsize=(9, 6))
for o in order:
    d = valid[valid["car"] == o]
    ax.scatter(d["mileage_km"] / 1000, d["price_b"], label=o, color=colors[o], s=55, edgecolor="white")
r = valid[["price_b", "mileage_km"]].corr().iloc[0, 1]
ax.set_xlabel("Mileage (thousand km)"); ax.set_ylabel("Price (billion Toman)")
ax.set_title(f"Price vs mileage (Pearson r = {r:.2f})", fontweight="bold"); ax.legend()
fig.tight_layout(); fig.savefig(OUT + "06_price_vs_mileage.png", dpi=150); plt.close(fig)
print("done")
