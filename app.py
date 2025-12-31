import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime, timedelta

# Import backend logic (reusing existing modules)
from features.transactions.transactions import (
    load_transactions, save_transaction, EXPENSE_CATEGORIES, INCOME_CATEGORIES
)
from features.budgets.budgets import load_budgets, save_all_budgets
from features.smart_assistant.assistant import load_goals, save_goals
from features.data_management import manager

# --- Page Configuration ---
st.set_page_config(page_title="FinTrack Pro", page_icon="💰", layout="wide")

# --- Custom Styling ---
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- Navigation ---
st.sidebar.title("💰 FinTrack Pro")
page = st.sidebar.radio("Navigation", [
    "Dashboard", 
    "Transactions", 
    "Budgets", 
    "Analytics", 
    "Smart Assistant", 
    "Data Management"
])

# ==========================================
# PAGE: DASHBOARD
# ==========================================
if page == "Dashboard":
    st.title("📊 Financial Dashboard")
    
    transactions = load_transactions()
    budgets = load_budgets()
    current_month = datetime.now().strftime("%Y-%m")
    
    # -- Summary Metrics --
    income_txns = [t for t in transactions if t['type'] == 'Income' and t['date'].startswith(current_month)]
    expense_txns = [t for t in transactions if t['type'] == 'Expense' and t['date'].startswith(current_month)]

    total_income = sum(t['amount_paisa'] for t in income_txns)
    total_expense = sum(t['amount_paisa'] for t in expense_txns)
    balance = total_income - total_expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Balance", f"Rs {balance/100:,.2f}")
    col2.metric("Monthly Income", f"Rs {total_income/100:,.2f}")
    col3.metric("Monthly Expenses", f"Rs {total_expense/100:,.2f}", delta=-total_expense/100, delta_color="inverse")

    # -- Recent Activity --
    st.subheader("Recent Activity")
    if transactions:
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False).head(5)
        
        for index, row in df.iterrows():
            amt = row['amount_paisa'] / 100
            color = "green" if row['type'] == "Income" else "red"
            icon = "↗️" if row['type'] == "Income" else "↘️"
            
            st.markdown(f"""
            <div style="padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1em;">{icon} <b>{row['category']}</b></span><br>
                    <span style="color: gray; font-size: 0.9em;">{row['description']} • {row['date'].strftime('%Y-%m-%d')}</span>
                </div>
                <div style="color: {color}; font-weight: bold;">
                    Rs {amt:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent transactions.")


# ==========================================
# PAGE: TRANSACTIONS
# ==========================================
elif page == "Transactions":
    st.title("💳 Transactions")
    
    tab1, tab2 = st.tabs(["View Transactions", "Add New"])
    
    # -- Tab 1: View --
    with tab1:
        transactions = load_transactions()
        if not transactions:
            st.info("No transactions found.")
        else:
            df = pd.DataFrame(transactions)
            
            # Filters
            col_f1, col_f2 = st.columns(2)
            filter_type = col_f1.multiselect("Filter by Type", ["Income", "Expense"])
            filter_cat = col_f2.multiselect("Filter by Category", list(set(df['category'])))
            
            if filter_type:
                df = df[df['type'].isin(filter_type)]
            if filter_cat:
                df = df[df['category'].isin(filter_cat)]
                
            # Display
            df['Amount (Rs)'] = df['amount_paisa'] / 100
            st.dataframe(
                df[['date', 'type', 'category', 'description', 'Amount (Rs)']].sort_values('date', ascending=False),
                use_container_width=True,
                hide_index=True
            )

    # -- Tab 2: Add --
    with tab2:
        st.subheader("Add Transaction")
        with st.form("add_txn_form"):
            col1, col2 = st.columns(2)
            t_type = col1.selectbox("Type", ["Expense", "Income"])
            
            cats = EXPENSE_CATEGORIES if t_type == "Expense" else INCOME_CATEGORIES
            t_cat = col2.selectbox("Category", cats)
            
            t_amt = st.number_input("Amount (Rs)", min_value=0.01, step=10.0)
            t_desc = st.text_input("Description")
            t_date = st.date_input("Date", datetime.now())
            
            submitted = st.form_submit_button("Save Transaction")
            
            if submitted:
                new_txn = {
                    "id": str(uuid.uuid4())[:8],
                    "date": t_date.strftime("%Y-%m-%d"),
                    "type": t_type,
                    "category": t_cat,
                    "amount_paisa": int(t_amt * 100),
                    "description": t_desc
                }
                save_transaction(new_txn)
                st.success("Transaction added successfully!")
                st.rerun()


# ==========================================
# PAGE: BUDGETS
# ==========================================
elif page == "Budgets":
    st.title("🎯 Budget Management")
    
    tab1, tab2 = st.tabs(["Overview", "Set Budgets"])
    
    current_month = datetime.now().strftime("%Y-%m")
    budgets = load_budgets()
    month_budgets = [b for b in budgets if b['month_year'] == current_month]
    
    transactions = load_transactions()
    
    # -- Tab 1: Overview --
    with tab1:
        if not month_budgets:
            st.warning("No budgets set for this month.")
        else:
            # Calculate spending
            spending = {}
            for t in transactions:
                if t['type'] == 'Expense' and t['date'].startswith(current_month):
                    spending[t['category']] = spending.get(t['category'], 0) + t['amount_paisa']

            for b in month_budgets:
                cat = b['category']
                limit = b['limit_paisa']
                spent = spending.get(cat, 0)
                util = spent / limit if limit > 0 else 0
                
                # Visual Card
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.subheader(cat)
                        color = "red" if util > 1.0 else "orange" if util > 0.8 else "green"
                        st.progress(min(util, 1.0))
                    with col_b:
                        st.write(f"**Rs {spent/100:,.0f}** / {limit/100:,.0f}")
                        st.caption(f"{util*100:.1f}% Used")
                    st.divider()

    # -- Tab 2: Set --
    with tab2:
        st.subheader("Set Monthly Budget")
        with st.form("budget_form"):
            b_cat = st.selectbox("Category", EXPENSE_CATEGORIES)
            b_amt = st.number_input("Monthly Limit (Rs)", min_value=100.0, step=500.0)
            
            submitted = st.form_submit_button("Set Budget")
            
            if submitted:
                # Logic to update/append (simplified for streamlit re-run)
                new_budget = {
                    "category": b_cat,
                    "limit_paisa": int(b_amt * 100),
                    "month_year": current_month
                }
                # Remove existing for same cat/month
                budgets = [b for b in budgets if not (b['category'] == b_cat and b['month_year'] == current_month)]
                budgets.append(new_budget)
                save_all_budgets(budgets)
                st.success(f"Budget set for {b_cat}!")
                st.rerun()


# ==========================================
# PAGE: ANALYTICS
# ==========================================
elif page == "Analytics":
    st.title("📈 Financial Analytics")
    
    transactions = load_transactions()
    if not transactions:
        st.info("Need more data for analytics.")
    else:
        df = pd.DataFrame(transactions)
        df['amount'] = df['amount_paisa'] / 100
        
        # Income vs Expense Pie Chart
        st.subheader("Income vs Expenses")
        total_by_type = df.groupby('type')['amount'].sum()
        st.bar_chart(total_by_type, horizontal=True) # Simple bar chart
        
        # Category Breakdown
        st.subheader("Spending by Category")
        expenses = df[df['type'] == 'Expense']
        if not expenses.empty:
            cat_breakdown = expenses.groupby('category')['amount'].sum()
            st.bar_chart(cat_breakdown)
        
        # Daily Trend
        st.subheader("Daily Spending Trend")
        if not expenses.empty:
            daily = expenses.groupby('date')['amount'].sum()
            st.line_chart(daily)


# ==========================================
# PAGE: SMART ASSISTANT
# ==========================================
elif page == "Smart Assistant":
    st.title("🤖 Smart Assistant")
    
    goals = load_goals()
    transactions = load_transactions()
    budgets = load_budgets()
    
    # -- Daily Check --
    st.subheader("Daily Snapshot")
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_spent = sum(t['amount_paisa'] for t in transactions if t['date'] == today_str and t['type'] == 'Expense')
    
    col1, col2 = st.columns(2)
    col1.metric("Today's Spending", f"Rs {today_spent/100:,.2f}")
    
    if today_spent == 0:
        col2.success("💡 Tip: Great start! No spending yet today.")
    elif today_spent > 200000: # 2000 Rs
        col2.warning("💡 Tip: High spending today. Check your budget!")
    else:
        col2.info("💡 Tip: You're on track.")

    st.divider()

    # -- Goals Management --
    st.subheader("🎯 Financial Goals")
    
    # Display Goals
    if goals:
        for g in goals:
            target = g['target_paisa'] / 100
            saved = g['saved_paisa'] / 100
            progress = saved / target if target > 0 else 0
            
            st.write(f"**{g['name']}** (Deadline: {g['deadline']})")
            st.progress(min(progress, 1.0))
            st.caption(f"Rs {saved:,.0f} / Rs {target:,.0f} ({progress*100:.1f}%)")
    else:
        st.info("No goals set yet.")

    # Add Goal Expander
    with st.expander("➕ Add New Goal"):
        with st.form("goal_form"):
            g_name = st.text_input("Goal Name")
            g_target = st.number_input("Target Amount (Rs)", min_value=1000.0)
            g_deadline = st.date_input("Deadline")
            
            sub_g = st.form_submit_button("Create Goal")
            if sub_g:
                goals.append({
                    "name": g_name,
                    "target_paisa": int(g_target * 100),
                    "saved_paisa": 0,
                    "deadline": g_deadline.strftime("%Y-%m-%d")
                })
                save_goals(goals)
                st.success("Goal Created!")
                st.rerun()
                
    # Update Goal Expander
    with st.expander("✏️ Update Goal Progress"):
        if goals:
            with st.form("update_goal_form"):
                g_select = st.selectbox("Select Goal", [g['name'] for g in goals])
                g_added = st.number_input("Total Saved Amount (Rs)", min_value=0.0)
                
                sub_u = st.form_submit_button("Update Progress")
                if sub_u:
                    for g in goals:
                        if g['name'] == g_select:
                            g['saved_paisa'] = int(g_added * 100)
                    save_goals(goals)
                    st.success("Updated!")
                    st.rerun()


# ==========================================
# PAGE: DATA MANAGEMENT
# ==========================================
elif page == "Data Management":
    st.title("💾 Data Management")
    
    transactions = load_transactions()
    budgets = load_budgets()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Transactions")
        if transactions:
            df_t = pd.DataFrame(transactions)
            df_t['amount_rs'] = df_t['amount_paisa'] / 100
            csv_t = df_t.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "📥 Download CSV",
                csv_t,
                "transactions.csv",
                "text/csv",
                key='download-csv'
            )
            
            json_t = df_t.to_json(orient="records").encode('utf-8')
            st.download_button(
                "📥 Download JSON",
                json_t,
                "transactions.json",
                "application/json",
                key='download-json'
            )
    
    with col2:
        st.subheader("Export Budgets")
        if budgets:
            df_b = pd.DataFrame(budgets)
            df_b['limit_rs'] = df_b['limit_paisa'] / 100
            csv_b = df_b.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "📥 Download CSV",
                csv_b,
                "budgets.csv",
                "text/csv",
                key='download-budgets'
            )

