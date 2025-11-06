import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("expenses.db")
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
# Category suggestion logic
# -----------------------------
def suggest_category(description):
    desc = description.lower()
    if any(word in desc for word in ["pizza", "food", "coffee", "lunch", "restaurant"]):
        return "Food"
    elif any(word in desc for word in ["uber", "bus", "train", "petrol", "cab"]):
        return "Travel"
    elif any(word in desc for word in ["rent", "bill", "recharge", "electricity"]):
        return "Bills"
    elif any(word in desc for word in ["doctor", "pharmacy", "medicine", "hospital"]):
        return "Health"
    elif any(word in desc for word in ["amazon", "clothes", "mall", "shopping"]):
        return "Shopping"
    else:
        return "Miscellaneous"


# -----------------------------
# Add expense
# -----------------------------
def add_expense():
    desc = desc_entry.get()
    amt = amt_entry.get()
    cat = cat_entry.get()

    if not desc or not amt:
        messagebox.showwarning("Warning", "Description and amount are required.")
        return

    try:
        amt = float(amt)
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number.")
        return

    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO expenses (date, description, amount, category) VALUES (?, ?, ?, ?)",
                   (date, desc, amt, cat))
    conn.commit()
    desc_entry.delete(0, tk.END)
    amt_entry.delete(0, tk.END)
    cat_entry.delete(0, tk.END)
    cat_entry.insert(0, suggest_category(desc))
    refresh_table()


# -----------------------------
# Delete selected expense
# -----------------------------
def delete_expense():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Warning", "Select an expense to delete.")
        return
    item = tree.item(selected)
    expense_id = item["values"][0]
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    refresh_table()


# -----------------------------
# Refresh table data
# -----------------------------
def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM expenses ORDER BY id DESC")
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)
    update_summary()


# -----------------------------
# Show spending chart
# -----------------------------
def show_chart():
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cursor.fetchall()
    if not data:
        messagebox.showinfo("Info", "No data to display.")
        return

    categories = [d[0] for d in data]
    amounts = [d[1] for d in data]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(categories, amounts, color="#4a90e2")
    ax.set_xlabel("Category")
    ax.set_ylabel("Total Spent (₹)")
    ax.set_title("Category-wise Spending")
    plt.tight_layout()

    chart_window = tk.Toplevel(root)
    chart_window.title("Spending Chart")
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# -----------------------------
# Update summary info
# -----------------------------
def update_summary():
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]
    total_label.config(text=f"Total Spent: ₹{total if total else 0:.2f}")


# -----------------------------
# GUI layout
# -----------------------------
root = tk.Tk()
root.title("Smart Expense Tracker")
root.geometry("700x500")
root.configure(bg="#f5f6fa")

# Input frame
input_frame = tk.Frame(root, bg="#f5f6fa")
input_frame.pack(pady=10)

tk.Label(input_frame, text="Description:", bg="#f5f6fa").grid(row=0, column=0, padx=5)
desc_entry = tk.Entry(input_frame, width=25)
desc_entry.grid(row=0, column=1, padx=5)

tk.Label(input_frame, text="Amount:", bg="#f5f6fa").grid(row=0, column=2, padx=5)
amt_entry = tk.Entry(input_frame, width=10)
amt_entry.grid(row=0, column=3, padx=5)

tk.Label(input_frame, text="Category:", bg="#f5f6fa").grid(row=0, column=4, padx=5)
cat_entry = tk.Entry(input_frame, width=15)
cat_entry.grid(row=0, column=5, padx=5)
cat_entry.insert(0, "Miscellaneous")

tk.Button(input_frame, text="Add", command=add_expense, bg="#4a90e2", fg="white").grid(row=0, column=6, padx=5)
tk.Button(input_frame, text="Delete", command=delete_expense, bg="#e84118", fg="white").grid(row=0, column=7, padx=5)
tk.Button(input_frame, text="Show Chart", command=show_chart, bg="#44bd32", fg="white").grid(row=0, column=8, padx=5)

# Table frame
table_frame = tk.Frame(root)
table_frame.pack(pady=10)

columns = ("ID", "Date", "Description", "Amount", "Category")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=100, anchor="center")

tree.pack(fill=tk.BOTH, expand=True)


total_label = tk.Label(root, text="Total Spent: ₹0.00", bg="#f5f6fa", font=("Arial", 12, "bold"))
total_label.pack(pady=10)


refresh_table()

root.mainloop()
conn.close()

