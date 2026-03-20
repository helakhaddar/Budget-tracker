import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

CSV_FILE = "transactions.csv"
COLUMNS = ["id", "date", "type", "category", "amount", "note"]

INCOME_CATS = [
    "Salary", "Freelance", "Business", "Investment",
    "Gift", "Rental", "Refund", "Other Income",
]
EXPENSE_CATS = [
    "Groceries", "Dining", "Transport", "Housing", "Utilities",
    "Healthcare", "Entertainment", "Shopping", "Education",
    "Travel", "Subscriptions", "Personal Care", "Other Expense",
]


def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(CSV_FILE, dtype={"note": str})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["amount"] = df["amount"].astype(float)
    return df


def save_transaction(tx_type, category, amount, tx_date, note):
    df = load_data()
    new_id = int(df["id"].max()) + 1 if not df.empty else 1
    new_row = pd.DataFrame([{
        "id": new_id,
        "date": str(tx_date),
        "type": tx_type,
        "category": category,
        "amount": round(float(amount), 2),
        "note": note.strip(),
    }])
    pd.concat([df, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)


def compute_summary(df: pd.DataFrame):
    income = df.loc[df["type"] == "Income", "amount"].sum()
    expenses = df.loc[df["type"] == "Expense", "amount"].sum()
    return income - expenses, income, expenses


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="wide")
st.title("Budget Tracker")
st.caption("Track your income and expenses, and see where your money goes.")

# ── Sidebar: Add Transaction ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Add Transaction")

    tx_type = st.selectbox("Type", ["Expense", "Income"])
    category = st.selectbox(
        "Category",
        EXPENSE_CATS if tx_type == "Expense" else INCOME_CATS,
    )
    amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, format="%.2f")
    tx_date = st.date_input("Date", value=date.today())
    note = st.text_input("Note (optional)", placeholder="e.g. Monthly salary")

    if st.button("Add Transaction", type="primary", use_container_width=True):
        if amount <= 0:
            st.error("Amount must be greater than 0.")
        else:
            save_transaction(tx_type, category, amount, tx_date, note)
            st.success(f"{tx_type} of ${amount:.2f} added!")
            st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_data()
balance, total_income, total_expenses = compute_summary(df)

# ── Metrics ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Current Balance", f"${balance:,.2f}")
col2.metric("Total Income", f"${total_income:,.2f}")
col3.metric("Total Expenses", f"${total_expenses:,.2f}")

st.divider()

# ── Chart ─────────────────────────────────────────────────────────────────────
st.subheader("Spending by Category")
expense_df = df[df["type"] == "Expense"]

if expense_df.empty:
    st.info("No expense data yet. Add some expenses to see the chart.")
else:
    by_cat = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    fig = px.bar(
        by_cat,
        x="category",
        y="amount",
        labels={"category": "Category", "amount": "Total ($)"},
        color="category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Transaction History ───────────────────────────────────────────────────────
st.subheader("Transaction History")

if df.empty:
    st.info("No transactions yet. Add one using the sidebar.")
else:
    all_categories = sorted(df["category"].unique().tolist())

    fcol1, fcol2, fcol3 = st.columns(3)
    filter_type = fcol1.selectbox("Filter by type", ["All", "Income", "Expense"])
    filter_cat = fcol2.selectbox("Filter by category", ["All"] + all_categories)
    sort_by = fcol3.selectbox("Sort by", ["date", "amount", "category", "type"])

    view = df.copy()
    if filter_type != "All":
        view = view[view["type"] == filter_type]
    if filter_cat != "All":
        view = view[view["category"] == filter_cat]
    view = view.sort_values(sort_by, ascending=False).drop(columns=["id"])

    st.dataframe(view, use_container_width=True, hide_index=True)
