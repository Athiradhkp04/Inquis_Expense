import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# -----------------------------
# Database Connection
# -----------------------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# Database Setup
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    amount REAL,
    category TEXT,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY,
    monthly_budget REAL
)
""")

conn.commit()

# -----------------------------
# Helper Functions
# -----------------------------
def suggest_category(description):
    desc = description.lower()

    if any(x in desc for x in ["pizza","food","coffee","restaurant","snack"]):
        return "Food"

    elif any(x in desc for x in ["uber","bus","train","petrol","cab"]):
        return "Travel"

    elif any(x in desc for x in ["bill","recharge","rent","electricity"]):
        return "Bills"

    elif any(x in desc for x in ["doctor","medicine","hospital","pharmacy"]):
        return "Health"

    elif any(x in desc for x in ["amazon","clothes","mall","shopping"]):
        return "Shopping"

    return "Miscellaneous"


def add_expense(desc, amt, cat, notes):
    date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
    INSERT INTO expenses
    (date, description, amount, category, notes)
    VALUES (?, ?, ?, ?, ?)
    """,
    (date, desc, amt, cat, notes))

    conn.commit()


def delete_expense(expense_id):
    cursor.execute(
        "DELETE FROM expenses WHERE id=?",
        (expense_id,)
    )
    conn.commit()


def get_all_expenses():
    return pd.read_sql(
        "SELECT * FROM expenses ORDER BY id DESC",
        conn
    )


def set_budget(amount):
    cursor.execute("""
    INSERT OR REPLACE INTO budget
    (id, monthly_budget)
    VALUES (1, ?)
    """,
    (amount,)
    )
    conn.commit()


def get_budget():
    cursor.execute("""
    SELECT monthly_budget
    FROM budget
    WHERE id = 1
    """)

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


# -----------------------------
# Streamlit Setup
# -----------------------------
st.set_page_config(
    page_title="Inquis",
    layout="wide"
)

st.title("💰 Inquis")
st.caption(
    "Personal Finance Analytics Platform"
)

# -----------------------------
# Budget Sidebar
# -----------------------------
st.sidebar.header("Monthly Budget")

current_budget = get_budget()

budget_input = st.sidebar.number_input(
    "Set Budget (₹)",
    min_value=0.0,
    value=float(current_budget)
)

if st.sidebar.button("Save Budget"):
    set_budget(budget_input)
    st.sidebar.success("Budget Updated")

# -----------------------------
# Tabs
# -----------------------------
tab_dashboard, tab_add, tab_view, tab_analytics = st.tabs([
    "🏠 Dashboard",
    "➕ Add Expense",
    "📄 Transactions",
    "📊 Analytics"
])
# -----------------------------
# Dashboard
# -----------------------------
with tab_dashboard:

    st.subheader("Financial Overview")

    df = get_all_expenses()

    budget = get_budget()

    if df.empty:

        st.info("No expenses recorded yet.")

    else:

        total_spent = df["amount"].sum()

        remaining_budget = budget - total_spent

        highest_cat = (
            df.groupby("category")["amount"]
            .sum()
            .idxmax()
        )

        daily_avg = (
            df.groupby("date")["amount"]
            .sum()
            .mean()
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Spent",
            f"₹{total_spent:.2f}"
        )

        col2.metric(
            "Budget",
            f"₹{budget:.2f}"
        )

        col3.metric(
            "Remaining",
            f"₹{remaining_budget:.2f}"
        )

        col4.metric(
            "Top Category",
            highest_cat
        )

        # -----------------------------
        # Financial Health Score
        # -----------------------------
        score = 100

        if budget > 0 and total_spent > budget:
            score -= 25

        elif budget > 0 and total_spent > budget * 0.8:
            score -= 10

        score = max(score, 0)

        st.divider()

        st.subheader("Financial Health Score")

        st.metric(
            "Score",
            f"{score}/100"
        )

        st.progress(score / 100)

        # -----------------------------
        # Smart Insights
        # -----------------------------
        st.subheader("Smart Insights")

        category_df = (
            df.groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        if "Food" in category_df["category"].values:

            food_spend = category_df[
                category_df["category"] == "Food"
            ]["amount"].iloc[0]

            food_pct = (
                food_spend / total_spent
            ) * 100

            st.info(
                f"🍔 Food accounts for {food_pct:.1f}% of your spending."
            )

        if budget > 0:

            utilization = (
                total_spent / budget
            ) * 100

            st.info(
                f"💰 You have used {utilization:.1f}% of your monthly budget."
            )

        if remaining_budget > 0:

            st.success(
                f"✅ ₹{remaining_budget:.2f} remains in your budget."
            )

        else:

            st.error(
                f"⚠️ Budget exceeded by ₹{abs(remaining_budget):.2f}"
            )

        # -----------------------------
        # Spending Distribution
        # -----------------------------
        st.divider()

        fig = px.pie(
            category_df,
            names="category",
            values="amount",
            hole=0.4,
            title="Spending Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# -----------------------------
# Add Expense
# -----------------------------
with tab_add:

    st.subheader("Add Expense")

    desc = st.text_input(
        "Description"
    )

    amt = st.number_input(
        "Amount (₹)",
        min_value=0.0,
        step=10.0
    )

    suggested = (
        suggest_category(desc)
        if desc else "Miscellaneous"
    )

    categories = [
        "Food",
        "Travel",
        "Bills",
        "Health",
        "Shopping",
        "Miscellaneous"
    ]

    default_index = (
        categories.index(suggested)
        if suggested in categories
        else 5
    )

    cat = st.selectbox(
        "Category",
        categories,
        index=default_index
    )

    notes = st.text_area(
        "Notes"
    )

    if st.button("Add Expense"):

        if desc and amt > 0:

            add_expense(
                desc,
                amt,
                cat,
                notes
            )

            st.success(
                "Expense Added Successfully!"
            )

        else:

            st.warning(
                "Enter valid description and amount."
            )
# -----------------------------
# Transactions
# -----------------------------
with tab_view:

    st.subheader("Transactions")

    df = get_all_expenses()

    if df.empty:

        st.info(
            "No expenses recorded yet."
        )

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        ids = df["id"].tolist()

        delete_id = st.selectbox(
            "Select Expense ID",
            ["None"] + [str(i) for i in ids]
        )

        if st.button("Delete Selected"):

            if delete_id != "None":

                delete_expense(
                    int(delete_id)
                )

                st.success(
                    "Expense Deleted"
                )

# -----------------------------
# Analytics
# -----------------------------
with tab_analytics:

    st.subheader("Analytics")

    df = get_all_expenses()

    if df.empty:

        st.info(
            "No data available."
        )

    else:

        category_df = (
            df.groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig1 = px.bar(
            category_df,
            x="category",
            y="amount",
            title="Category-wise Spending"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        daily_df = (
            df.groupby("date")["amount"]
            .sum()
            .reset_index()
        )

        fig2 = px.line(
            daily_df,
            x="date",
            y="amount",
            markers=True,
            title="Daily Spending Trend"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

# -----------------------------
# Footer
# -----------------------------
st.divider()

st.caption(
    "Inquis | Personal Finance Analytics Platform"
)
