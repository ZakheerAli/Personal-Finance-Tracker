import os
import questionary
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn

from features.transactions.transactions import load_transactions, EXPENSE_CATEGORIES, validate_amount
from features.budgets.budgets import load_budgets

console = Console()
GOALS_PATH = os.path.join("database", "goals.txt")

def load_goals():
    goals = []
    if not os.path.exists(GOALS_PATH):
        return goals
    with open(GOALS_PATH, "r") as f:
        for line in f:
            if line.strip():
                parts = line.strip().split("|")
                if len(parts) == 4:
                    goals.append({
                        "name": parts[0],
                        "target_paisa": int(parts[1]),
                        "saved_paisa": int(parts[2]),
                        "deadline": parts[3]
                    })
    return goals

def save_goals(goals):
    with open(GOALS_PATH, "w") as f:
        for g in goals:
            f.write(f"{g['name']}|{g['target_paisa']}|{g['saved_paisa']}|{g['deadline']}\n")

def manage_goals():
    while True:
        action = questionary.select(
            "Manage Goals:",
            choices=["Add Goal", "Update Progress", "View Goals", "Back"]
        ).ask()

        if action == "Back" or not action:
            break
        
        if action == "Add Goal":
            name = questionary.text("Goal Name (e.g., Emergency Fund):").ask()
            if not name: continue
            
            target_str = questionary.text("Target Amount:", validate=validate_amount).ask()
            if not target_str: continue
            
            deadline = questionary.text("Deadline (YYYY-MM-DD):", default=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")).ask()
            
            goals = load_goals()
            goals.append({
                "name": name,
                "target_paisa": int(float(target_str) * 100),
                "saved_paisa": 0,
                "deadline": deadline
            })
            save_goals(goals)
            console.print("[green]Goal added![/green]")

        elif action == "Update Progress":
            goals = load_goals()
            if not goals:
                console.print("[yellow]No goals set.[/yellow]")
                continue
            
            goal_name = questionary.select(
                "Select Goal:",
                choices=[g['name'] for g in goals]
            ).ask()
            
            if not goal_name: continue
            
            goal = next(g for g in goals if g['name'] == goal_name)
            current_saved = goal['saved_paisa'] / 100
            
            amount_str = questionary.text(
                f"Current saved amount (was {current_saved}):",
                validate=validate_amount
            ).ask()
            
            if amount_str:
                goal['saved_paisa'] = int(float(amount_str) * 100)
                save_goals(goals)
                console.print("[green]Progress updated![/green]")

        elif action == "View Goals":
            goals = load_goals()
            if not goals:
                console.print("[yellow]No goals found.[/yellow]")
            else:
                table = Table(title="Financial Goals")
                table.add_column("Goal")
                table.add_column("Target")
                table.add_column("Saved")
                table.add_column("Progress", width=20)
                table.add_column("Deadline")
                
                for g in goals:
                    pct = (g['saved_paisa'] / g['target_paisa']) * 100 if g['target_paisa'] > 0 else 0
                    bar_len = 10
                    filled = int(min(pct, 100) / 100 * bar_len)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    
                    table.add_row(
                        g['name'],
                        f"Rs {g['target_paisa']/100:.0f}",
                        f"Rs {g['saved_paisa']/100:.0f}",
                        f"[{'green' if pct >= 100 else 'cyan'}]{bar} {pct:.1f}%[/]",
                        g['deadline']
                    )
                console.print(table)


def daily_check():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    current_month_str = today.strftime("%Y-%m")
    
    transactions = load_transactions()
    budgets = load_budgets()
    
    # 1. Daily Spending
    today_txns = [t for t in transactions if t['date'] == today_str and t['type'] == 'Expense']
    today_spent = sum(t['amount_paisa'] for t in today_txns)
    
    # 2. Daily Budget Calculation
    month_budgets = [b for b in budgets if b['month_year'] == current_month_str]
    total_monthly_budget = sum(b['limit_paisa'] for b in month_budgets)
    
    if total_monthly_budget == 0:
        # Fallback if no budget: Estimate based on income or generic
        daily_budget_display = "Not Set"
        remaining_display = "N/A"
        status_icon = "⚪"
    else:
        days_in_month = 30 # Simplified
        daily_budget = total_monthly_budget / days_in_month
        daily_budget_display = f"Rs {daily_budget/100:.2f}"
        
        if today_spent <= daily_budget:
            status_icon = "✅"
            remaining_display = f"Rs {(daily_budget - today_spent)/100:.2f}"
        else:
            status_icon = "⚠️"
            remaining_display = f"-Rs {(today_spent - daily_budget)/100:.2f} (Over)"

    # 3. Alerts
    alerts = []
    
    # Budget Alerts
    category_spent = {}
    for t in transactions:
        if t['type'] == 'Expense' and t['date'].startswith(current_month_str):
            category_spent[t['category']] = category_spent.get(t['category'], 0) + t['amount_paisa']
            
            # Large Transaction Check (> Rs 5000)
            if t['date'] == today_str and t['amount_paisa'] > 500000:
                alerts.append(f"💸 Large transaction today: Rs {t['amount_paisa']/100:.0f} ({t['category']})")

    for b in month_budgets:
        spent = category_spent.get(b['category'], 0)
        pct = (spent / b['limit_paisa']) * 100
        if pct >= 85:
            alerts.append(f"⚠️  {b['category']} budget critical: {pct:.1f}% used")
    
    # 4. Tip
    if not alerts and today_spent == 0:
        tip = "💡 No spending yet today! Great day to save."
    elif today_spent > (total_monthly_budget / 30 if total_monthly_budget else 100000): 
        tip = "💡 High spending today. Try a 'No Spend Day' tomorrow."
    else:
        tip = "💡 You're on track! Consider moving Rs 500 to savings."

    # Render
    console.print(Panel.fit(
        f"Today's Spending: Rs {today_spent/100:.2f}\n"
        f"Daily Budget:     {daily_budget_display} {status_icon}\n"
        f"Remaining:        {remaining_display}\n\n" +
        (f"[bold red]Alerts:[/bold red]\n" + "\n".join(alerts) + "\n\n" if alerts else "") +
        f"[bold cyan]{tip}[/bold cyan]",
        title=f"📊 Daily Financial Check ({today_str})",
        subtitle="Smart Assistant"
    ))

def smart_recommendations():
    transactions = load_transactions()
    budgets = load_budgets()
    goals = load_goals()
    
    current_month_str = datetime.now().strftime("%Y-%m")
    
    recs = []
    
    # Analyze Income vs Expense
    income = sum(t['amount_paisa'] for t in transactions if t['type'] == 'Income' and t['date'].startswith(current_month_str))
    expenses = sum(t['amount_paisa'] for t in transactions if t['type'] == 'Expense' and t['date'].startswith(current_month_str))
    
    if income > 0:
        savings_rate = (income - expenses) / income * 100
        if savings_rate < 20:
            recs.append("📉 **Boost Savings**: Your savings rate is below 20%. Try the 50/30/20 rule.")
        elif savings_rate > 40:
            recs.append("🚀 **Invest More**: High savings rate! Consider moving excess cash to investments.")
    
    # Analyze Categories
    category_spent = {}
    for t in transactions:
        if t['type'] == 'Expense' and t['date'].startswith(current_month_str):
            category_spent[t['category']] = category_spent.get(t['category'], 0) + t['amount_paisa']
            
    sorted_cats = sorted(category_spent.items(), key=lambda x: x[1], reverse=True)
    if sorted_cats:
        top_cat, top_amt = sorted_cats[0]
        recs.append(f"💰 **Top Expense**: {top_cat} is your highest expense (Rs {top_amt/100:.0f}). Can you cut this by 10%?")
    
    # Analyze Budgets
    month_budgets = [b for b in budgets if b['month_year'] == current_month_str]
    if not month_budgets:
        recs.append("⚠️ **No Budgets**: Setting budgets reduces spending by ~15% on average. Set one now!")
        
    # Goals
    if not goals:
        recs.append("🎯 **Set Goals**: You haven't defined any financial goals. Start with an 'Emergency Fund'.")
    else:
        for g in goals:
            pct = (g['saved_paisa'] / g['target_paisa']) * 100
            if pct < 50:
                recs.append(f"🏁 **Focus on Goal**: '{g['name']}' is only {pct:.1f}% done. Add Rs 1000 this week.")
    
    console.print(Panel(
        "\n\n".join(recs),
        title="🤖 Smart Recommendations",
        border_style="blue"
    ))

def assistant_menu():
    while True:
        choice = questionary.select(
            "Smart Assistant:",
            choices=[
                "Daily Financial Check",
                "Smart Recommendations",
                "Manage Goals",
                "Back"
            ]
        ).ask()
        
        if choice == "Daily Financial Check":
            daily_check()
        elif choice == "Smart Recommendations":
            smart_recommendations()
        elif choice == "Manage Goals":
            manage_goals()
        elif choice == "Back" or not choice:
            break
