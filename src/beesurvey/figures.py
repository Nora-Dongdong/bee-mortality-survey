"""One chart style for both reports. Every figure is saved to figures/<season>/
under a fixed file name, and both reports link to that file."""
import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .config import CODEBOOKS, VARIABLE_LABELS, Season  # noqa: E402

INK = "#1f2933"
MUTED = "#7b8794"
BAR = "#2c6b8e"
HIGHLIGHT = "#d1495b"
GRID = "#e4e7eb"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
})


def _save(fig, s: Season, name: str):
    s.figures_dir.mkdir(parents=True, exist_ok=True)
    path = s.figures_dir / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def mortality_bars(table: pd.DataFrame, s: Season, var: str, overall_pct: float,
                   name: str, title: str = None):
    """Horizontal bars of hive-weighted mortality per group, with N per bar and
    the overall rate as a reference line. `table` comes from descriptive.by_group."""
    t = table.sort_values("mortality_pct")
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(t) + 1.4))
    ax.barh(t["label"], t["mortality_pct"], color=BAR, height=0.6)
    ax.axvline(overall_pct, color=MUTED, ls="--", lw=1)
    ax.text(overall_pct, -0.75, f" all apiaries {overall_pct:.1f}%",
            color=MUTED, fontsize=9, va="center")
    ax.set_ylim(-1, len(t) - 0.5)
    for i, (_, r) in enumerate(t.iterrows()):
        ax.text(r["mortality_pct"] + 0.4, i,
                f"{r['mortality_pct']:.1f}%   (n = {r['apiaries']} apiaries, {r['hives_in']:,} hives)",
                va="center", fontsize=9, color=INK)
    ax.set_xlim(0, max(t["mortality_pct"].max() * 1.6, overall_pct * 1.2))
    ax.set_xlabel("Winter loss (% of colonies, hive-weighted)")
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.set_title(title or f"Winter loss by {VARIABLE_LABELS.get(var, var).lower()}")
    return _save(fig, s, name)


def heatmap(cells: pd.DataFrame, s: Season, value: str, name: str, title: str,
            rows: str = "varroa_treatment", cols: str = "winter_food"):
    """Grid of mortality per rows x cols cell. Cells with fewer than
    s.min_apiaries_per_cell apiaries are greyed and labelled."""
    grid = cells.pivot(index=rows, columns=cols, values=value)
    n = cells.pivot(index=rows, columns=cols, values="apiaries").reindex_like(grid)
    fig, ax = plt.subplots(figsize=(8, 0.9 * len(grid) + 1.6))
    im = ax.imshow(grid.to_numpy(dtype=float), cmap="RdYlGn_r", vmin=0,
                   vmax=np.nanmax(grid.to_numpy(dtype=float)), aspect="auto")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v, k = grid.iat[i, j], n.iat[i, j]
            if pd.isna(v):
                continue
            small = k < s.min_apiaries_per_cell
            if small:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color="white", alpha=0.65))
            ax.text(j, i, f"{v:.1f}%\n{int(k)} apiaries" + ("\n(too few)" if small else ""),
                    ha="center", va="center", fontsize=9, color=INK)
    ax.set_xticks(range(grid.shape[1]), [CODEBOOKS[cols][c] for c in grid.columns])
    ax.set_yticks(range(grid.shape[0]), [CODEBOOKS[rows][r] for r in grid.index])
    ax.set_xlabel(VARIABLE_LABELS[cols])
    ax.set_ylabel(VARIABLE_LABELS[rows])
    ax.spines[:].set_visible(False)
    fig.colorbar(im, ax=ax, label="Winter loss (%)", shrink=0.8)
    ax.set_title(title)
    return _save(fig, s, name)


def odds_ratio_forest(table: pd.DataFrame, s: Season, name: str, title: str):
    """Odds ratios with 95% CI on a log axis; 1 = same as the reference group."""
    t = table.loc[table["term"].ne("Intercept")].iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.4 * len(t) + 1.4))
    y = np.arange(len(t))
    sig = t["p_value"] < s.alpha
    ax.errorbar(t["odds_ratio"], y,
                xerr=[t["odds_ratio"] - t["ci_low"], t["ci_high"] - t["odds_ratio"]],
                fmt="none", ecolor=MUTED, lw=1.2)
    ax.scatter(t["odds_ratio"], y, c=np.where(sig, HIGHLIGHT, BAR), zorder=3)
    ax.axvline(1, color=INK, lw=0.8)
    ax.set_xscale("log")
    ticks = [t_ for t_ in (0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8)
             if t["ci_low"].min() * 0.9 <= t_ <= t["ci_high"].max() * 1.1]
    ax.set_xticks(ticks, [f"{t_:g}" for t_ in ticks])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_yticks(y, t["label"])
    ax.set_xlabel("Odds ratio vs reference group (log scale, 95% CI)")
    ax.xaxis.grid(True, color=GRID)
    ax.set_title(title)
    return _save(fig, s, name)


def predicted_bars(pred: pd.DataFrame, s: Season, name: str, title: str):
    """Model-predicted vs observed loss per group (practical report)."""
    t = pred.sort_values("predicted_mortality_pct")
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(7.5, 0.6 * len(t) + 1.4))
    ax.barh(y, t["predicted_mortality_pct"], color=BAR, height=0.55, label="Same apiaries, only this practice changed")
    ax.scatter(t["observed_mortality_pct"], y, color=INK, marker="|", s=200, label="Observed in this group")
    for i, v in enumerate(t["predicted_mortality_pct"]):
        ax.text(max(v, t["observed_mortality_pct"].iat[i]) + 0.6, i, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_yticks(y, t["label"])
    ax.set_xlabel("Winter loss (%)")
    ax.set_xlim(0, max(t["predicted_mortality_pct"].max(), t["observed_mortality_pct"].max()) * 1.2)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=9)
    ax.set_title(title)
    return _save(fig, s, name)
