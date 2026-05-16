"""
SmartRetail India — Interactive EDA Dashboard
Run: streamlit run smartretail_dashboard.py
Dataset: SmartRetail_India_DataArchitecture.xlsx (place in same folder)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ── Backward-compatible cache decorator ──────────────────────────────────────
# st.cache_data was introduced in Streamlit 1.18.
# Older versions (< 1.18) only have st.cache.
import streamlit as _st
_st_version = tuple(int(x) for x in _st.__version__.split(".")[:2])

def _cache(func=None, **kwargs):
    """Wraps st.cache_data (≥1.18) or falls back to st.cache (< 1.18)."""
    if hasattr(_st, "cache_data"):
        # Drop show_spinner kwarg if it's a string — older cache_data builds
        # only accept bool; newest builds accept str. Keep it safe:
        if "show_spinner" in kwargs and not isinstance(kwargs["show_spinner"], bool):
            kwargs["show_spinner"] = True
        decorator = _st.cache_data(**kwargs)
    else:
        # st.cache doesn't support show_spinner as string either
        kwargs.pop("show_spinner", None)
        decorator = _st.cache(allow_output_mutation=True, **kwargs)
    if func is not None:
        return decorator(func)
    return decorator

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartRetail India EDA",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        border-left: 4px solid #FF6B35;
    }
    .metric-card h3 { margin: 0; font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card h1 { margin: 0.2rem 0 0; font-size: 1.8rem; color: #1a1a2e; }
    .section-header {
        font-size: 1.1rem; font-weight: 700; color: #1a1a2e;
        border-bottom: 2px solid #FF6B35; padding-bottom: 6px; margin-bottom: 1rem;
    }
    .validation-ok  { color: #28a745; font-weight: 600; }
    .validation-warn{ color: #fd7e14; font-weight: 600; }
    .validation-err { color: #dc3545; font-weight: 600; }
    [data-testid="stSidebar"] { background: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #f0f0f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
FILE = "SmartRetail_India_DataArchitecture.xlsx"

# st.divider() was added in Streamlit 1.16 — patch for older versions
if not hasattr(st, "divider"):
    def _divider():
        st.markdown("---")
    st.divider = _divider

import io

@_cache(show_spinner=True)
def load_data(path):
    # path may be a file-path string or BytesIO from uploader
    xl = pd.ExcelFile(path)
    sales    = pd.read_excel(xl, "A_Sales_Fact",    parse_dates=["Date"])
    inv      = pd.read_excel(xl, "B_Inventory",     parse_dates=["Date"])
    prod     = pd.read_excel(xl, "C_Product_Master")
    store    = pd.read_excel(xl, "D_Store_Master")
    pricing  = pd.read_excel(xl, "E_Pricing",       parse_dates=["Date"])
    promo    = pd.read_excel(xl, "F_Promotions",    parse_dates=["Promo Start", "Promo End"])
    ext      = pd.read_excel(xl, "G_External_Signals", parse_dates=["Date"])
    return sales, inv, prod, store, pricing, promo, ext

# ── File uploader (fallback) ──────────────────────────────────────────────────
try:
    sales, inv, prod, store, pricing, promo, ext = load_data(FILE)
    data_ok = True
except FileNotFoundError:
    data_ok = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 SmartRetail India")
    st.markdown("**EDA Dashboard · Jan 2022–Dec 2023**")
    st.divider()

    if not data_ok:
        uploaded = st.file_uploader("Upload SmartRetail Excel", type=["xlsx"])
        if uploaded:
            # Wrap in BytesIO so older pandas/xlrd versions can read it
            file_bytes = io.BytesIO(uploaded.read())
            sales, inv, prod, store, pricing, promo, ext = load_data(file_bytes)
            data_ok = True
        else:
            st.warning("Please upload the Excel file to continue.")
            st.stop()

    pages = [
        "📋 Data Validation",
        "📊 Sales Overview",
        "🏪 Store Performance",
        "📦 Inventory Analysis",
        "💰 Pricing & Margins",
        "🎉 Promotions",
        "🌦️ External Signals",
    ]
    page = st.radio("Navigation", pages)
    st.divider()

    # Global filters (used across pages)
    st.markdown("**Global Filters**")
    all_stores  = sorted(store["Store Id"].unique())
    sel_stores  = st.multiselect("Stores", all_stores, default=all_stores)
    date_range  = st.date_input(
        "Date Range",
        value=[sales["Date"].min(), sales["Date"].max()],
        min_value=sales["Date"].min(),
        max_value=sales["Date"].max(),
    )

# ── Filter helper ─────────────────────────────────────────────────────────────
def filter_sales(df):
    mask = (
        df["Store Id"].isin(sel_stores) &
        (df["Date"] >= pd.Timestamp(date_range[0])) &
        (df["Date"] <= pd.Timestamp(date_range[1]))
    )
    return df[mask]

def filter_by_date(df):
    mask = (df["Date"] >= pd.Timestamp(date_range[0])) & (df["Date"] <= pd.Timestamp(date_range[1]))
    return df[mask]

# Merged helpers
@_cache(show_spinner=False)
def enrich_sales(sales, prod, store):
    df = sales.merge(prod[["Product Id", "Category", "Subcategory", "Brand", "Cost Price", "Mrp"]], on="Product Id", how="left")
    df = df.merge(store[["Store Id", "City", "Region", "Store Type"]], on="Store Id", how="left")
    return df

rich = enrich_sales(sales, prod, store)

COLORS = px.colors.qualitative.Bold

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📋 Data Validation":
    st.title("📋 Data Validation Report")
    st.caption("Automated quality checks across all 7 dataset sheets")

    def check_badge(ok, warn=False):
        if ok and not warn:  return "✅ PASS"
        if warn:             return "⚠️ WARN"
        return "❌ FAIL"

    checks = []

    # Sales
    s = sales.copy()
    checks += [
        ("A_Sales_Fact", "No null values", check_badge(s.isnull().sum().sum() == 0)),
        ("A_Sales_Fact", "No negative Revenue", check_badge((s["Revenue"] < 0).sum() == 0)),
        ("A_Sales_Fact", "Revenue=0 rows (may be returns/data gap)",
            check_badge(True, warn=(s["Revenue"] == 0).sum() > 1000),
            f"{(s['Revenue']==0).sum():,} rows ({(s['Revenue']==0).mean()*100:.1f}%)"),
        ("A_Sales_Fact", "No negative Units Sold", check_badge((s["Units Sold"] < 0).sum() == 0)),
        ("A_Sales_Fact", "Date range completeness",
            check_badge((s["Date"].max() - s["Date"].min()).days >= 700),
            f"{s['Date'].min().date()} → {s['Date'].max().date()}"),
    ]

    # Inventory
    i = inv.copy()
    checks += [
        ("B_Inventory", "No null values", check_badge(i.isnull().sum().sum() == 0)),
        ("B_Inventory", "No negative Inventory On Hand", check_badge((i["Inventory On Hand"] < 0).sum() == 0)),
        ("B_Inventory", "Reorder Point > 0 for all rows", check_badge((i["Reorder Point"] <= 0).sum() == 0)),
    ]

    # Pricing
    p = pricing.copy()
    null_promo = p["Promotion Type"].isnull().sum()
    checks += [
        ("E_Pricing", "Selling Price > 0", check_badge((p["Selling Price"] <= 0).sum() == 0)),
        ("E_Pricing", "Discount Pct in [0,100]",
            check_badge(p["Discount Pct"].between(0, 100).all())),
        ("E_Pricing", "Promotion Type nulls (expected: no promo rows)",
            check_badge(True, warn=null_promo > 0),
            f"{null_promo:,} nulls — rows with no active promotion"),
        ("E_Pricing", "Margin values present", check_badge(p["Margin"].isnull().sum() == 0)),
    ]

    # Product master
    pm = prod.copy()
    checks += [
        ("C_Product_Master", "MRP > Cost Price for all products",
            check_badge((pm["Mrp"] > pm["Cost Price"]).all())),
        ("C_Product_Master", "No duplicate Product Ids",
            check_badge(pm["Product Id"].duplicated().sum() == 0)),
        ("C_Product_Master", "No null values", check_badge(pm.isnull().sum().sum() == 0)),
    ]

    # Store master
    sm = store.copy()
    checks += [
        ("D_Store_Master", "No duplicate Store Ids", check_badge(sm["Store Id"].duplicated().sum() == 0)),
        ("D_Store_Master", "All stores have City & Region", check_badge(sm[["City","Region"]].isnull().sum().sum() == 0)),
    ]

    # Referential integrity
    sales_stores  = set(sales["Store Id"].unique())
    master_stores = set(store["Store Id"].unique())
    sales_prods   = set(sales["Product Id"].unique())
    master_prods  = set(prod["Product Id"].unique())
    checks += [
        ("Referential Integrity", "All Sales Store Ids exist in Store Master",
            check_badge(sales_stores.issubset(master_stores)),
            f"Sales has {len(sales_stores)} unique stores; Master has {len(master_stores)}"),
        ("Referential Integrity", "All Sales Product Ids exist in Product Master",
            check_badge(sales_prods.issubset(master_prods)),
            f"Sales has {len(sales_prods)} unique products; Master has {len(master_prods)}"),
    ]

    # Build dataframe
    rows = []
    for c in checks:
        sheet, check, status = c[0], c[1], c[2]
        note = c[3] if len(c) > 3 else ""
        rows.append({"Sheet": sheet, "Check": check, "Status": status, "Note": note})
    vdf = pd.DataFrame(rows)

    pass_n  = (vdf["Status"] == "✅ PASS").sum()
    warn_n  = (vdf["Status"] == "⚠️ WARN").sum()
    fail_n  = (vdf["Status"] == "❌ FAIL").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Checks", len(vdf))
    c2.metric("✅ Passed",  pass_n)
    c3.metric("⚠️ Warnings", warn_n)
    c4.metric("❌ Failed",  fail_n)

    st.divider()

    def color_status(val):
        if "PASS" in val: return "color: #28a745; font-weight:700"
        if "WARN" in val: return "color: #fd7e14; font-weight:700"
        return "color: #dc3545; font-weight:700"

    st.dataframe(
        vdf.style.map(color_status, subset=["Status"]),
        use_container_width=True, hide_index=True, height=520
    )

    st.divider()
    st.markdown("### 📐 Dataset Summary")
    summary_rows = [
        {"Sheet": "A_Sales_Fact",       "Rows": f"{len(sales):,}",   "Columns": len(sales.columns),   "Date Span": "Jan 2022–Dec 2023"},
        {"Sheet": "B_Inventory",        "Rows": f"{len(inv):,}",     "Columns": len(inv.columns),     "Date Span": "Jan 2022–Dec 2023"},
        {"Sheet": "C_Product_Master",   "Rows": f"{len(prod):,}",    "Columns": len(prod.columns),    "Date Span": "—"},
        {"Sheet": "D_Store_Master",     "Rows": f"{len(store):,}",   "Columns": len(store.columns),   "Date Span": "—"},
        {"Sheet": "E_Pricing",          "Rows": f"{len(pricing):,}", "Columns": len(pricing.columns), "Date Span": "Jan 2022–Dec 2023"},
        {"Sheet": "F_Promotions",       "Rows": f"{len(promo):,}",   "Columns": len(promo.columns),   "Date Span": "Campaign-level"},
        {"Sheet": "G_External_Signals", "Rows": f"{len(ext):,}",     "Columns": len(ext.columns),     "Date Span": "Jan 2022–Dec 2023"},
    ]
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SALES OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Sales Overview":
    st.title("📊 Sales Overview")
    df = filter_sales(rich)

    total_rev     = df["Revenue"].sum()
    total_units   = df["Units Sold"].sum()
    total_trans   = df["Transactions"].sum()
    total_returns = df["Returns"].sum()
    return_rate   = total_returns / total_units * 100 if total_units else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Total Revenue",    f"₹{total_rev/1e6:.2f}M")
    c2.metric("📦 Units Sold",       f"{total_units:,}")
    c3.metric("🧾 Transactions",     f"{total_trans:,}")
    c4.metric("↩️ Returns",          f"{total_returns:,}")
    c5.metric("📉 Return Rate",      f"{return_rate:.2f}%")

    st.divider()

    # Revenue trend
    st.markdown('<div class="section-header">Monthly Revenue Trend</div>', unsafe_allow_html=True)
    monthly = df.groupby(df["Date"].dt.to_period("M")).agg(Revenue=("Revenue","sum"), Units=("Units Sold","sum")).reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=monthly["Date"], y=monthly["Revenue"], name="Revenue (₹)", marker_color="#FF6B35", opacity=0.85), secondary_y=False)
    fig.add_trace(go.Scatter(x=monthly["Date"], y=monthly["Units"], name="Units Sold", line=dict(color="#1a1a2e", width=2), mode="lines+markers"), secondary_y=True)
    fig.update_layout(height=320, margin=dict(t=10,b=10), legend=dict(orientation="h", y=1.1), plot_bgcolor="white", paper_bgcolor="white")
    fig.update_yaxes(title_text="Revenue (₹)", secondary_y=False)
    fig.update_yaxes(title_text="Units Sold", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Revenue by Category</div>', unsafe_allow_html=True)
        cat_rev = df.groupby("Category")["Revenue"].sum().reset_index().sort_values("Revenue", ascending=False)
        fig2 = px.bar(cat_rev, x="Revenue", y="Category", orientation="h",
                      color="Category", color_discrete_sequence=COLORS,
                      text_auto=".2s")
        fig2.update_layout(showlegend=False, height=280, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Units Sold by Category</div>', unsafe_allow_html=True)
        cat_units = df.groupby("Category")["Units Sold"].sum().reset_index()
        fig3 = px.pie(cat_units, names="Category", values="Units Sold",
                      color_discrete_sequence=COLORS, hole=0.45)
        fig3.update_layout(height=280, margin=dict(t=10,b=10), paper_bgcolor="white")
        st.plotly_chart(fig3, use_container_width=True)

    # Heatmap: weekday x month
    st.markdown('<div class="section-header">Revenue Heatmap — Day of Week × Month</div>', unsafe_allow_html=True)
    hm = df.copy()
    hm["DOW"]   = hm["Date"].dt.day_name()
    hm["Month"] = hm["Date"].dt.strftime("%b %Y")
    hm_pivot = hm.groupby(["DOW","Month"])["Revenue"].sum().reset_index()
    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    hm_pivot["DOW"] = pd.Categorical(hm_pivot["DOW"], categories=dow_order, ordered=True)
    hm_wide = hm_pivot.pivot(index="DOW", columns="Month", values="Revenue").fillna(0)
    fig4 = px.imshow(hm_wide, color_continuous_scale="OrRd", aspect="auto",
                     labels=dict(color="Revenue (₹)"))
    fig4.update_layout(height=280, margin=dict(t=10,b=10), paper_bgcolor="white")
    st.plotly_chart(fig4, use_container_width=True)

    # Top products
    st.markdown('<div class="section-header">Top 10 Products by Revenue</div>', unsafe_allow_html=True)
    top_prod = df.groupby(["Product Id","Subcategory","Brand"]).agg(
        Revenue=("Revenue","sum"), Units=("Units Sold","sum"), Transactions=("Transactions","sum")
    ).reset_index().sort_values("Revenue", ascending=False).head(10)
    st.dataframe(top_prod.style.format({"Revenue":"₹{:,.0f}", "Units":"{:,}", "Transactions":"{:,}"}),
                 use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: STORE PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏪 Store Performance":
    st.title("🏪 Store Performance")
    df = filter_sales(rich)

    by_store = df.merge(store[["Store Id","City","Region","Store Type","Footfall Capacity"]], on=["Store Id","City","Region","Store Type"], how="left")
    print(by_store.columns.tolist())
    store_kpi = by_store.groupby(["Store Id","City","Region","Store Type","Footfall Capacity"]).agg(
        Revenue=("Revenue","sum"),
        Units=("Units Sold","sum"),
        Transactions=("Transactions","sum"),
        Returns=("Returns","sum"),
    ).reset_index()
    store_kpi["Rev/Transaction"] = store_kpi["Revenue"] / store_kpi["Transactions"]
    store_kpi["Return Rate %"]   = store_kpi["Returns"] / store_kpi["Units"] * 100

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Revenue by Store</div>', unsafe_allow_html=True)
        fig = px.bar(store_kpi.sort_values("Revenue", ascending=False),
                     x="City", y="Revenue", color="Store Type", text_auto=".2s",
                     color_discrete_sequence=COLORS)
        fig.update_layout(height=320, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Revenue by Region (Pie)</div>', unsafe_allow_html=True)
        reg_rev = store_kpi.groupby("Region")["Revenue"].sum().reset_index()
        fig2 = px.pie(reg_rev, names="Region", values="Revenue",
                      color_discrete_sequence=COLORS, hole=0.4)
        fig2.update_layout(height=320, margin=dict(t=10,b=10), paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Revenue vs Footfall Capacity</div>', unsafe_allow_html=True)
    fig3 = px.scatter(store_kpi, x="Footfall Capacity", y="Revenue",
                      color="Store Type", size="Transactions", hover_name="City",
                      color_discrete_sequence=COLORS, text="City")
    fig3.update_traces(textposition="top center")
    fig3.update_layout(height=360, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

    # Monthly trend by store
    st.markdown('<div class="section-header">Monthly Revenue Trend by Store</div>', unsafe_allow_html=True)
    df2 = by_store.copy()
    df2["Month"] = df2["Date"].dt.to_period("M").dt.to_timestamp()
    trend = df2.groupby(["Month","City"])["Revenue"].sum().reset_index()
    fig4 = px.line(trend, x="Month", y="Revenue", color="City",
                   color_discrete_sequence=COLORS, markers=True)
    fig4.update_layout(height=360, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white",
                       legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-header">Store KPI Scorecard</div>', unsafe_allow_html=True)
    disp = store_kpi[["City","Region","Store Type","Revenue","Transactions","Rev/Transaction","Return Rate %"]].sort_values("Revenue", ascending=False)
    st.dataframe(disp.style.format({"Revenue":"₹{:,.0f}","Transactions":"{:,}","Rev/Transaction":"₹{:,.1f}","Return Rate %":"{:.2f}%"}),
                 use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INVENTORY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📦 Inventory Analysis":
    st.title("📦 Inventory Analysis")
    df_inv = filter_by_date(inv[inv["Store Id"].isin(sel_stores)]).merge(
        prod[["Product Id","Category","Subcategory"]], on="Product Id", how="left"
    )

    avg_oh   = df_inv["Inventory On Hand"].mean()
    avg_wh   = df_inv["Warehouse Stock"].mean()
    reorder_alerts = (df_inv["Inventory On Hand"] < df_inv["Reorder Point"]).sum()
    avg_lead = df_inv["Lead Time Days"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Avg On-Hand Stock", f"{avg_oh:,.0f} units")
    c2.metric("🏭 Avg Warehouse Stock", f"{avg_wh:,.0f} units")
    c3.metric("🚨 Below Reorder Point", f"{reorder_alerts:,} records")
    c4.metric("⏱️ Avg Lead Time", f"{avg_lead:.1f} days")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Avg Inventory On-Hand by Category</div>', unsafe_allow_html=True)
        cat_inv = df_inv.groupby("Category")["Inventory On Hand"].mean().reset_index().sort_values("Inventory On Hand")
        fig = px.bar(cat_inv, x="Inventory On Hand", y="Category", orientation="h",
                     color="Category", color_discrete_sequence=COLORS, text_auto=".0f")
        fig.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Below Reorder Point — by Store</div>', unsafe_allow_html=True)
        alert_store = df_inv[df_inv["Inventory On Hand"] < df_inv["Reorder Point"]].merge(
            store[["Store Id","City"]], on="Store Id", how="left"
        ).groupby("City").size().reset_index(name="Alert Count").sort_values("Alert Count", ascending=False)
        fig2 = px.bar(alert_store, x="City", y="Alert Count", color="Alert Count",
                      color_continuous_scale="Reds", text_auto=True)
        fig2.update_layout(height=300, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Inventory trend over time
    st.markdown('<div class="section-header">Avg On-Hand Inventory Trend (Monthly)</div>', unsafe_allow_html=True)
    df_inv["Month"] = df_inv["Date"].dt.to_period("M").dt.to_timestamp()
    inv_trend = df_inv.groupby(["Month","Category"]).agg(AvgOH=("Inventory On Hand","mean")).reset_index()
    fig3 = px.line(inv_trend, x="Month", y="AvgOH", color="Category",
                   color_discrete_sequence=COLORS, markers=True)
    fig3.update_layout(height=340, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white",
                       legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig3, use_container_width=True)

    # Lead time distribution
    st.markdown('<div class="section-header">Lead Time Distribution by Product</div>', unsafe_allow_html=True)
    fig4 = px.box(df_inv.merge(prod[["Product Id","Brand"]], on="Product Id", how="left"),
                  x="Category", y="Lead Time Days", color="Category",
                  color_discrete_sequence=COLORS, points="suspectedoutliers")
    fig4.update_layout(showlegend=False, height=320, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PRICING & MARGINS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Pricing & Margins":
    st.title("💰 Pricing & Margins")
    df_p = filter_by_date(pricing[pricing["Store Id"].isin(sel_stores)]).merge(
        prod[["Product Id","Category","Subcategory","Cost Price","Mrp"]], on="Product Id", how="left"
    )

    avg_margin    = df_p["Margin"].mean()
    avg_discount  = df_p["Discount Pct"].mean()
    price_premium = ((df_p["Selling Price"] - df_p["Competitor Price"]) / df_p["Competitor Price"] * 100).mean()
    promo_pct     = df_p["Promotion Type"].notna().mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 Avg Margin %",      f"{avg_margin:.1f}%")
    c2.metric("🏷️ Avg Discount %",   f"{avg_discount:.1f}%")
    c3.metric("🆚 vs Competitor",     f"{price_premium:+.1f}%")
    c4.metric("🎁 % Rows with Promo", f"{promo_pct:.1f}%")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Margin Distribution by Category</div>', unsafe_allow_html=True)
        fig = px.violin(df_p, x="Category", y="Margin", color="Category",
                        color_discrete_sequence=COLORS, box=True, points=False)
        fig.update_layout(showlegend=False, height=320, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Discount % by Promotion Type</div>', unsafe_allow_html=True)
        disc_promo = df_p[df_p["Promotion Type"].notna()].groupby("Promotion Type")["Discount Pct"].mean().reset_index()
        fig2 = px.bar(disc_promo, x="Promotion Type", y="Discount Pct",
                      color="Promotion Type", text_auto=".1f", color_discrete_sequence=COLORS)
        fig2.update_layout(showlegend=False, height=320, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    # Selling price vs competitor price
    st.markdown('<div class="section-header">Selling Price vs Competitor Price by Category</div>', unsafe_allow_html=True)
    scatter_d = df_p.groupby(["Product Id","Category"]).agg(
        SellingPrice=("Selling Price","mean"),
        CompetitorPrice=("Competitor Price","mean"),
    ).reset_index()
    fig3 = px.scatter(scatter_d, x="CompetitorPrice", y="SellingPrice",
                      color="Category", hover_name="Product Id",
                      color_discrete_sequence=COLORS, trendline="ols")
    # Reference line y=x
    max_val = max(scatter_d[["SellingPrice","CompetitorPrice"]].max())
    fig3.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                   line=dict(color="gray", dash="dot"))
    fig3.update_layout(height=360, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

    # Monthly margin trend
    st.markdown('<div class="section-header">Monthly Avg Margin % Trend</div>', unsafe_allow_html=True)
    df_p["Month"] = df_p["Date"].dt.to_period("M").dt.to_timestamp()
    margin_trend = df_p.groupby(["Month","Category"])["Margin"].mean().reset_index()
    fig4 = px.line(margin_trend, x="Month", y="Margin", color="Category",
                   color_discrete_sequence=COLORS, markers=True)
    fig4.update_layout(height=340, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white",
                       legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PROMOTIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎉 Promotions":
    st.title("🎉 Promotions Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric("📣 Total Campaigns", len(promo))
    c2.metric("💸 Total Promo Budget", f"₹{promo['Promo Budget Inr'].sum()/1e6:.2f}M")
    c3.metric("📅 Avg Campaign Duration",
              f"{((promo['Promo End'] - promo['Promo Start']).dt.days.mean()):.0f} days")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Budget by Promo Channel</div>', unsafe_allow_html=True)
        ch_budget = promo.groupby("Promo Channel")["Promo Budget Inr"].sum().reset_index().sort_values("Promo Budget Inr", ascending=False)
        fig = px.bar(ch_budget, x="Promo Budget Inr", y="Promo Channel",
                     orientation="h", color="Promo Channel",
                     color_discrete_sequence=COLORS, text_auto=".2s")
        fig.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Budget Share by Channel</div>', unsafe_allow_html=True)
        fig2 = px.pie(ch_budget, names="Promo Channel", values="Promo Budget Inr",
                      color_discrete_sequence=COLORS, hole=0.4)
        fig2.update_layout(height=300, margin=dict(t=10,b=10), paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    # Campaign Gantt
    st.markdown('<div class="section-header">Campaign Timeline (Gantt)</div>', unsafe_allow_html=True)
    fig3 = px.timeline(promo, x_start="Promo Start", x_end="Promo End",
                        y="Campaign Name", color="Promo Channel",
                        color_discrete_sequence=COLORS,
                        hover_data=["Promo Budget Inr"])
    fig3.update_yaxes(autorange="reversed")
    fig3.update_layout(height=420, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

    # Promotion type impact on margin (from pricing sheet)
    st.markdown('<div class="section-header">Promotion Type vs Avg Margin & Discount</div>', unsafe_allow_html=True)
    promo_impact = pricing[pricing["Promotion Type"].notna()].groupby("Promotion Type").agg(
        Avg_Margin=("Margin","mean"),
        Avg_Discount=("Discount Pct","mean"),
        Count=("Selling Price","count"),
    ).reset_index()
    fig4 = px.bar(promo_impact, x="Promotion Type", y=["Avg_Margin","Avg_Discount"],
                  barmode="group", color_discrete_sequence=[COLORS[0], COLORS[2]],
                  labels={"value":"Value (%)","variable":"Metric"})
    fig4.update_layout(height=320, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-header">All Promotions</div>', unsafe_allow_html=True)
    display_promo = promo.copy()
    display_promo["Duration (days)"] = (display_promo["Promo End"] - display_promo["Promo Start"]).dt.days
    st.dataframe(display_promo.style.format({"Promo Budget Inr":"₹{:,}"}),
                 use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: EXTERNAL SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🌦️ External Signals":
    st.title("🌦️ External Signals")
    df_ext = filter_by_date(ext)
    df_ext["Month"] = df_ext["Date"].dt.to_period("M").dt.to_timestamp()

    festival_days = df_ext["Festival Flag"].sum()
    holiday_days  = df_ext["Holiday Name"].notna().sum()
    event_days    = df_ext["Event Flag"].sum()
    avg_temp      = df_ext["Temperature C"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎊 Festival Days",  f"{festival_days}")
    c2.metric("🗓️ Holiday Days",  f"{holiday_days}")
    c3.metric("📅 Event Days",    f"{event_days}")
    c4.metric("🌡️ Avg Temp",     f"{avg_temp:.1f}°C")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Weather Condition Distribution</div>', unsafe_allow_html=True)
        weather_cnt = df_ext["Weather"].value_counts().reset_index()
        weather_cnt.columns = ["Weather","Count"]
        fig = px.pie(weather_cnt, names="Weather", values="Count",
                     color_discrete_sequence=COLORS, hole=0.4)
        fig.update_layout(height=300, margin=dict(t=10,b=10), paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Monthly Avg Temperature & Rainfall</div>', unsafe_allow_html=True)
        clim = df_ext.groupby("Month").agg(Temp=("Temperature C","mean"), Rain=("Rainfall Mm","mean")).reset_index()
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(x=clim["Month"], y=clim["Rain"], name="Rainfall (mm)", marker_color="#4CC9F0", opacity=0.7), secondary_y=False)
        fig2.add_trace(go.Scatter(x=clim["Month"], y=clim["Temp"], name="Temp (°C)", line=dict(color="#FF6B35", width=2), mode="lines+markers"), secondary_y=True)
        fig2.update_layout(height=300, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)

    # Sales lift on festival/holiday days
    st.markdown('<div class="section-header">Revenue Impact — Festival & Holiday Days</div>', unsafe_allow_html=True)
    df_impact = filter_sales(rich).merge(
        ext[["Date","Festival Flag","Holiday Name","Event Flag","Weather"]], on="Date", how="left"
    )
    df_impact["Day Type"] = "Normal"
    df_impact.loc[df_impact["Festival Flag"] == 1, "Day Type"] = "Festival"
    df_impact.loc[df_impact["Holiday Name"].notna(), "Day Type"] = "Holiday"
    df_impact.loc[df_impact["Event Flag"] == 1, "Day Type"] = "Event"

    impact = df_impact.groupby("Day Type").agg(
        Avg_Daily_Revenue=("Revenue","mean"),
        Avg_Units=("Units Sold","mean"),
    ).reset_index()
    fig3 = px.bar(impact, x="Day Type", y="Avg_Daily_Revenue",
                  color="Day Type", text_auto=".2s", color_discrete_sequence=COLORS)
    fig3.update_layout(showlegend=False, height=320, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

    # Revenue by weather
    st.markdown('<div class="section-header">Avg Revenue by Weather Condition</div>', unsafe_allow_html=True)
    weather_rev = df_impact.groupby("Weather")["Revenue"].mean().reset_index().sort_values("Revenue", ascending=False)
    fig4 = px.bar(weather_rev, x="Weather", y="Revenue", color="Weather",
                  text_auto=".2s", color_discrete_sequence=COLORS)
    fig4.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig4, use_container_width=True)

    # Holiday calendar
    st.markdown('<div class="section-header">Holiday & Festival Calendar</div>', unsafe_allow_html=True)
    holidays_df = df_ext[df_ext["Holiday Name"].notna()][["Date","Holiday Name","Festival Flag","Event Flag","Weather"]].copy()
    st.dataframe(holidays_df.reset_index(drop=True), use_container_width=True, hide_index=True)