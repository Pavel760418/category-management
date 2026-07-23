import numpy as np
import pandas as pd
from app.core.status import status_by_ratio
from app.services.config_service import load_yaml
from app.services.schema_service import get_schema_service


class CalculationService:
    def __init__(self):
        self.kpi_cfg = load_yaml("kpi_config.yaml")
        self.norms = self.kpi_cfg["norms"]
        self.schema = get_schema_service()

    def enrich_base(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df.copy()
        for col in ["sales_value", "sales_qty", "cogs_value", "stock_qty", "purchase_price", "shelf_meters", "prior_sales_value", "prior_sales_qty", "prior_gp_value", "period_months"]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")
        out["gross_profit"] = out.get("sales_value", 0) - out.get("cogs_value", 0)
        out["margin_pct"] = np.where(out.get("sales_value", 0) > 0, out["gross_profit"] / out["sales_value"], np.nan)
        months = out.get("period_months", pd.Series([6] * len(out)))
        out["inventory_turnover"] = np.where(out.get("stock_qty", 0) * out.get("purchase_price", 0) > 0,
                                              out.get("cogs_value", 0) / (out.get("stock_qty", 0) * out.get("purchase_price", 0)), np.nan)
        out["stock_days"] = np.where(out.get("sales_qty", 0) > 0,
                                      out.get("stock_qty", 0) / (out.get("sales_qty", 0) / months.replace(0, np.nan) / 30), np.nan)
        out["revenue_per_shelf"] = np.where(out.get("shelf_meters", 0) > 0, out.get("sales_value", 0) / out.get("shelf_meters", 0), np.nan)
        out["gp_per_shelf"] = np.where(out.get("shelf_meters", 0) > 0, out.get("gross_profit", 0) / out.get("shelf_meters", 0), np.nan)
        out["lfl_sales_pct"] = np.where(out.get("prior_sales_value", 0) > 0,
                                         (out.get("sales_value", 0) - out.get("prior_sales_value", 0)) / out.get("prior_sales_value", 0), np.nan)
        return out

    def build_kpis(self, df: pd.DataFrame, goals: pd.DataFrame | None = None):
        if df.empty:
            return pd.DataFrame(columns=["code", "name", "actual", "target", "ratio", "status"])
        targets = {
            "turnover": df["sales_value"].sum() * 1.05,
            "gross_profit": df["gross_profit"].sum() * 1.05,
            "margin_pct": 0.30,
            "stock_days": self.norms["stock_days_target"],
            "sku_count": 50,
            "lfl_sales": 0.10,
            "inventory_turnover": self.norms["turnover_target"],
            "revenue_per_shelf": df["revenue_per_shelf"].median() if "revenue_per_shelf" in df else None,
        }
        if goals is not None and not goals.empty and "metric_name" in goals.columns:
            for _, row in goals.iterrows():
                raw_metric = row.get("metric_name", "")
                metric = self.schema.resolve_metric_code(raw_metric) or str(raw_metric).strip().lower()
                if metric in targets and pd.notna(row.get("target_6m")):
                    targets[metric] = row.get("target_6m")
        actuals = {
            "turnover": df["sales_value"].sum(),
            "gross_profit": df["gross_profit"].sum(),
            "margin_pct": df["gross_profit"].sum() / df["sales_value"].sum() if df["sales_value"].sum() else None,
            "stock_days": df["stock_days"].replace([np.inf, -np.inf], np.nan).mean(),
            "sku_count": df["sku_code"].astype(str).nunique() if "sku_code" in df else None,
            "lfl_sales": ((df["sales_value"].sum() - df["prior_sales_value"].sum()) / df["prior_sales_value"].sum()) if "prior_sales_value" in df and df["prior_sales_value"].sum() else None,
            "inventory_turnover": df["inventory_turnover"].replace([np.inf, -np.inf], np.nan).mean(),
            "revenue_per_shelf": df["sales_value"].sum() / df["shelf_meters"].sum() if "shelf_meters" in df and df["shelf_meters"].sum() else None,
        }
        rows = []
        directions = {k: v["direction"] for k, v in self.kpi_cfg["kpis"].items()}
        names = {k: v["name"] for k, v in self.kpi_cfg["kpis"].items()}
        for code, actual in actuals.items():
            target = targets.get(code)
            risk_mult = self.kpi_cfg["thresholds"].get("stock_days_risk_multiplier", 1.3) if code == "stock_days" else self.kpi_cfg["thresholds"].get("sku_risk_multiplier", 1.15) if code == "sku_count" else 1.0
            ratio, status = status_by_ratio(actual, target, directions.get(code, "up"), risk_multiplier=risk_mult)
            rows.append({"code": code, "name": names.get(code, code), "actual": actual, "target": target, "ratio": ratio, "status": status, "direction": directions.get(code, "up")})
        return pd.DataFrame(rows)

    def abc_analysis(self, df: pd.DataFrame, metric: str = "sales_value"):
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        g = df.groupby(["sku_code", "sku_name"], dropna=False)[metric].sum().reset_index()
        g = g.sort_values(metric, ascending=False).reset_index(drop=True)
        total = g[metric].sum()
        g["cum_share"] = g[metric].cumsum() / total if total else np.nan
        g["abc_class"] = np.select([g["cum_share"] <= 0.8, g["cum_share"] <= 0.95], ["A", "B"], default="C")
        return g

    def shelf_efficiency(self, df: pd.DataFrame):
        if df.empty or "shelf_meters" not in df.columns:
            return pd.DataFrame()
        grp_cols = [c for c in ["store_name", "format_name", "subcategory"] if c in df.columns]
        if not grp_cols:
            grp_cols = ["category"] if "category" in df.columns else []
        if not grp_cols:
            return pd.DataFrame()
        g = df.groupby(grp_cols, dropna=False).agg(
            sales_value=("sales_value", "sum"),
            gross_profit=("gross_profit", "sum"),
            shelf_meters=("shelf_meters", "sum")
        ).reset_index()
        g["sales_per_meter"] = np.where(g["shelf_meters"] > 0, g["sales_value"] / g["shelf_meters"], np.nan)
        g["gp_per_meter"] = np.where(g["shelf_meters"] > 0, g["gross_profit"] / g["shelf_meters"], np.nan)
        return g

    def purchase_plan(self, df: pd.DataFrame):
        if df.empty:
            return pd.DataFrame()
        out = df.copy()
        months = out.get("period_months", pd.Series([6] * len(out))).replace(0, 6)
        target_days = self.norms["stock_days_target"]
        out["target_stock_qty"] = np.where(out["sales_qty"] > 0, np.ceil(out["sales_qty"] / months / 30 * target_days), np.nan)
        out["purchase_qty_needed"] = np.where(out["target_stock_qty"].notna(), np.maximum(out["target_stock_qty"] - out["stock_qty"], 0), np.nan)
        out["purchase_budget"] = out["purchase_qty_needed"] * out["purchase_price"]
        return out[[c for c in ["sku_code", "sku_name", "subcategory", "purchase_qty_needed", "purchase_budget", "target_stock_qty"] if c in out.columns]]
