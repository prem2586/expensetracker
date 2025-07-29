import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
import re

# --- DB Setup ---
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    category TEXT,
    description TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- Tool 1: Log Expense ---
@tool
def log_expense(entry: str) -> str:
    """Log an expense from a natural language entry. Example: 'I spent $20 on coffee'."""
    try:
        match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", entry)
        if not match:
            return "Couldn't extract amount from input."
        amount = float(match.group(1))

        # Very basic category detection
        category_keywords = {
            "food": ["restaurant", "lunch", "dinner", "snack", "groceries"],
            "transport": ["uber", "bus", "train", "taxi"],
            "coffee": ["coffee", "latte", "starbucks"],
            "shopping": ["clothes", "shopping", "amazon"],
        }
        category = "other"
        for cat, keywords in category_keywords.items():
            if any(k in entry.lower() for k in keywords):
                category = cat
                break

        cursor.execute("INSERT INTO expenses (amount, category, description) VALUES (?, ?, ?)",
                       (amount, category, entry))
        conn.commit()
        return f"Logged ${amount} under '{category}'"
    except Exception as e:
        return f"Error: {e}"

# --- Tool 2: Show Summary ---
@tool
def show_summary(input: str) -> str:
    """Show all logged expenses."""
    cursor.execute("SELECT amount, category, description FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()
    if not rows:
        return "No expenses logged yet."
    return "\n".join(f"${amt:.2f} on {cat} — {desc}" for amt, cat, desc in rows)

# --- Tool 3: Suggest Savings ---
@tool
def suggest_savings(input: str) -> str:
    """Suggest savings tips based on spending patterns."""
    cursor.execute("SELECT category FROM expenses")
    categories = [r[0] for r in cursor.fetchall()]
    tips = []
    if categories.count("coffee") > 3:
        tips.append("☕ Consider reducing coffee shop visits.")
    if categories.count("transport") > 3:
        tips.append("🚲 Try walking or biking instead of Uber.")
    if categories.count("shopping") > 3:
        tips.append("🛍️ Set a monthly shopping limit.")
    if not tips:
        tips.append("✅ No obvious savings suggestions — great job!")
    return "\n".join(tips)

# --- LLM Agent ---
llm = ChatOpenAI(temperature=0, openai_api_key=st.secrets["OPENAI_API_KEY"])
tools = [log_expense, show_summary, suggest_savings]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                         handle_parsing_errors=True, verbose=False)

# --- Streamlit UI ---
st.title("💸 Agentic Expense Tracker")

user_input = st.text_input("Enter an expense or ask for summary/savings tips:")
if st.button("Run"):
    if user_input.strip():
        with st.spinner("Thinking..."):
            try:
                response = agent.run(user_input)
                st.success("✅ Response:")
                st.write(response)
            except Exception as e:
                st.error(f"❌ Error: {e}")

# --- Pie Chart Visualization ---
st.divider()
st.subheader("📊 Spending Breakdown")
cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
chart_data = cursor.fetchall()

if chart_data:
    labels, values = zip(*chart_data)
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("No data to show yet.")

