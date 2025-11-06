import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    amount REAL,
    category TEXT
)
""")
conn.commit()

# -----------------------------
# Helper functions
# -----------------------------
def suggest_category(description):
    desc = description.lower()
    if any(x in desc for x in ["pizza", "food", "coffee", "restaurant", "snack"]):
        return "Food"
    elif any(x in desc for x in ["uber", "bus", "train", "petrol", "cab"]):
        return "Travel"
    elif any(x in desc for x in ["bill", "recharge", "rent", "electricity"]):
        return "Bills"
    elif any(x in desc for x in ["doctor", "medicine", "hospital", "pharmacy"]):
        return "Health"
    elif any(x in desc for x in ["amazon", "clothes", "mall", "shopping"]):
        return "Shopping"
    else:
        return "Miscellaneous"


def add_expense(desc, amt, cat):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO expenses (date, description, amount, category) VALUES (?,?,?,?)",
                   (date, desc, amt, cat))
    conn.commit()


def delete_expense(expense_id):
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()


def get_all_expenses():
    df = pd.read_sql("SELECT * FROM expenses ORDER BY id DESC", conn)
    return df


# -----------------------------
# Streamlit interface
# -----------------------------
st.set_page_config(page_title="Smart Expense Tracker", layout="wide")

st.title("Inquis : A Personal Finance Tracker")
st.caption("Built with Streamlit | Single-user Personal Edition")

tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📄 View Expenses", "📊 Reports"])

# ---- Add Expense Tab ----
with tab1:
    st.subheader("Add a new expense")

    desc = st.text_input("Description")
    amt = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    suggested = suggest_category(desc) if desc else ""
    cat = st.text_input("Category", value=suggested)

    if st.button("Add Expense"):
        if desc and amt > 0:
            add_expense(desc, amt, cat)
            st.success("Expense added successfully!")
        else:
            st.warning("Enter valid description and amount.")

# ---- View Expenses Tab ----
with tab2:
    st.subheader("All Recorded Expenses")

    df = get_all_expenses()
    if df.empty:
        st.info("No expenses recorded yet.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        ids = df["id"].tolist()
        delete_id = st.selectbox("Select an expense ID to delete", ["None"] + [str(i) for i in ids])
        if st.button("Delete Selected"):
            if delete_id != "None":
                delete_expense(int(delete_id))
                st.success("Expense deleted successfully!")

# ---- Reports Tab ----
with tab3:
    st.subheader("Visual Reports")
    df = get_all_expenses()

    if df.empty:
        st.info("No data available for visualization.")
    else:
        total_spent = df["amount"].sum()
        daily_avg = df.groupby("date")["amount"].sum().mean()
        highest_cat = df.groupby("category")["amount"].sum().idxmax()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Spent", f"₹{total_spent:.2f}")
        col2.metric("Daily Average", f"₹{daily_avg:.2f}")
        col3.metric("Highest Spending Category", highest_cat)

        st.write("---")

        # Category-wise spending chart
        cat_data = df.groupby("category")["amount"].sum().sort_values(ascending=False)
        fig1, ax1 = plt.subplots()
        ax1.bar(cat_data.index, cat_data.values, color="#4a90e2")
        ax1.set_title("Category-wise Spending")
        ax1.set_ylabel("Total (₹)")
        st.pyplot(fig1)

        # Daily spending chart
        daily_data = df.groupby("date")["amount"].sum()
        fig2, ax2 = plt.subplots()
        ax2.bar(daily_data.index, daily_data.values, color="#50e3c2")
        ax2.set_title("Daily Spending")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Amount (₹)")
        plt.xticks(rotation=45)
        st.pyplot(fig2)

st.write("---")
st.caption("Data stored locally in expenses.db | Evolved from Tkinter version into a browser-friendly app.")
