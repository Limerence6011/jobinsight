from __future__ import annotations
import matplotlib.pyplot as plt
import pandas as pd

def plot_salary_hist(s: pd.Series, out_png: str) -> str:
    if s.empty:
        return out_png
    fig = plt.figure()
    s.plot(kind="bar")
    plt.title("Salary Distribution (avg)")
    plt.xlabel("Bucket")
    plt.ylabel("Count")
    plt.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png
