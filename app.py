import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool

# 🧠 Memory to store expenses (can replace with SQLite or pandas)
expense_log = []

# 🔧 LangChain Tools
@tool
def log_expense(entry: str) -> str:
    """Log an expense in natural language. Example: 'Spent $50 on groceries'."""
    expense_log.append(entry)
    return f"Logged: {entry}"

@tool
def show_summary(_: str = "") -> str:
    """Show a summary of all logged expenses."""
    if not expense_log:
        return "No expenses logged yet."
    return "\n".join(f"{i+1}. {e}" for i, e in enumerate(expense_log))

@tool
def suggest_savings(_: str = "") -> str:
    """Suggest basic savings tips based on logged expenses."""
    tips = []
    for e in expense_log:
        if "coffee" in e.lower() or "latte" in e.lower():
            tips.append("☕ Consider cutting back on coffee shop visits.")
        if "uber" in e.lower():
            tips.append("🚗 Try using public transport instead of rideshares.")
        if "eating out" in e.lower() or "restaurant" in e.lower():
            tips.append("🍽️ Limit restaurant expenses by cooking at home.")
    if not tips:
        tips.append("✅ You're doing great! No major spending issues detected.")
    return "\n".join(set(tips))

# 🤖 Initialize Agent
llm = ChatOpenAI(temperature=0, openai_api_key=st.secrets["OPENAI_API_KEY"])
tools = [log_expense, show_summary, suggest_savings]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# 🖼️ Streamlit UI
st.title("💸 Agentic Expense Tracker")

query = st.text_input("Tell me about your expense or ask for a summary/suggestion:")
if st.button("Run"):
    if query.strip():
        with st.spinner("Thinking..."):
            response = agent.run(query)
            st.success("✅ Response")
            st.write(response)
    else:
        st.warning("Please enter something.")

