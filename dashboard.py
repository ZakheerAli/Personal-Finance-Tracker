import streamlit as st
import pandas as pd
from datetime import datetime
from features.transactions.transactions import load_transactions
from features.budgets.budgets import load_budgets, EXPENSE_CATEGORIES

# --- Page Config ---
st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .block-container {
        max_width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .css-1r6slb0 { /* Metric label */
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("💰 Personal Finance Dashboard")
st.markdown("---")

# --- Data Loading ---
transactions = load_transactions()
budgets = load_budgets()
current_month = datetime.now().strftime("%Y-%m")

# --- Section 1: Balance & Overview ---
st.subheader("📊 Financial Overview")

income_txns = [t for t in transactions if t['type'] == 'Income' and t['date'].startswith(current_month)]
expense_txns = [t for t in transactions if t['type'] == 'Expense' and t['date'].startswith(current_month)]

total_income = sum(t['amount_paisa'] for t in income_txns)
total_expense = sum(t['amount_paisa'] for t in expense_txns)
current_balance = total_income - total_expense

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Current Balance", value=f"Rs {current_balance/100:,.2f}")

with col2:
    st.metric(label="Total Income (This Month)", value=f"Rs {total_income/100:,.2f}", delta_color="normal")

with col3:
    st.metric(label="Total Expenses (This Month)", value=f"Rs {total_expense/100:,.2f}", delta="-", delta_color="inverse")

st.markdown("---")

# --- Section 2: Budget Status ---
st.subheader("🎯 Budget Progress")

month_budgets = [b for b in budgets if b['month_year'] == current_month]

if not month_budgets:
    st.info("No budgets set for this month. Go to the CLI to set your budgets!")
else:
    # Calculate spending per category
    category_spending = {}
    for t in expense_txns:
        cat = t['category']
        category_spending[cat] = category_spending.get(cat, 0) + t['amount_paisa']

    cols = st.columns(3) # Display in a grid
    for i, budget in enumerate(month_budgets):
        cat = budget['category']
        limit = budget['limit_paisa']
        spent = category_spending.get(cat, 0)
        
        utilization = spent / limit if limit > 0 else 0
        pct = min(utilization, 1.0)
        
        # Color coding logic
        if utilization >= 1.0:
            bar_color = "red"
        elif utilization >= 0.7:
            bar_color = "yellow"
        else:
            bar_color = "green"
        
        # Display in columns
        with cols[i % 3]:
            st.markdown(f"**{cat}**")
            st.progress(pct)
            st.caption(f"Rs {spent/100:,.2f} / Rs {limit/100:,.2f} ({utilization*100:.1f}%)")
            
            if utilization >= 1.0:
                st.error("Over Budget!")
            elif utilization >= 0.7:
                st.warning("Approaching Limit")
            else:
                st.success("On Track")

st.markdown("---")

# --- Section 3: Recent Transactions ---
st.subheader("📝 Recent Transactions")

if not transactions:
    st.info("No transactions found.")
else:
    # Prepare DataFrame
    df = pd.DataFrame(transactions)
    
    # Sort by date descending
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date_dt', ascending=False).head(10)
    
    # Format for display
    display_df = pd.DataFrame()
    display_df['Date'] = df['date']
    display_df['Type'] = df['type']
    display_df['Category'] = df['category']
    display_df['Description'] = df['description']
    display_df['Amount'] = df['amount_paisa'].apply(lambda x: f"Rs {x/100:,.2f}")
    
    # Color highlighting function for the table
    def highlight_type(val):
        color = '#d4edda' if val == 'Income' else '#f8d7da' # Light green / Light red
        return f'background-color: {color}'

    st.dataframe(
        display_df.style.applymap(highlight_type, subset=['Type']),
        use_container_width=True,
        hide_index=True
    )
