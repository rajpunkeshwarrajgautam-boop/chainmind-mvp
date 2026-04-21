from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_sales_frame(rows: list[dict[str, Any]]) -> dict[str, Any]:
    df = pd.DataFrame(rows)
    df.columns = [str(c).strip().lower() for c in df.columns]
    issues: list[dict[str, Any]] = []
    if "date" not in df.columns or "sales" not in df.columns:
        return {"valid": False, "issues": [{"code": "MISSING_COLUMNS", "detail": "Need date and sales"}]}
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    null_dates = int(df["date"].isna().sum())
    null_sales = int(df["sales"].isna().sum())
    if null_dates:
        issues.append({"code": "NULL_DATE", "count": null_dates})
    if null_sales:
        issues.append({"code": "NULL_SALES", "count": null_sales})
    dup_dates = int(df["date"].duplicated().sum())
    if dup_dates:
        issues.append({"code": "DUPLICATE_DATES", "count": dup_dates})
    return {
        "valid": len(issues) == 0 and null_dates == 0 and null_sales == 0,
        "row_count": len(df),
        "issues": issues,
        "date_dtype": str(df["date"].dtype),
        "sales_stats": {
            "min": float(df["sales"].min()) if not df["sales"].isna().all() else None,
            "max": float(df["sales"].max()) if not df["sales"].isna().all() else None,
        },
    }
