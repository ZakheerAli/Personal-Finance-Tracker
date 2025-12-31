from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.bar import Bar
from rich.columns import Columns
from rich.text import Text

# Import shared resources
# Note: Adjust imports based on project structure
from features.transactions.transactions import load_transactions, EXPENSE_CATEGORIES
from features.budgets.budgets import load_budgets

console = Console()

def get_month_transactions(transactions, year, month):
    prefix = f"{year}-{month:02d}"
    return [t for t in transactions if t['date'].startswith(prefix)]

def calculate_totals(transactions):
    income = sum(t['amount_paisa'] for t in transactions if t['type'] == 'Income')
    expenses = sum(t['amount_paisa'] for t in transactions if t['type'] == 'Expense')
    return income, expenses

def get_category_breakdown(transactions):
    breakdown = {}
    total = 0
    for t in transactions:
        if t['type'] == 'Expense':
            cat = t['category']
            breakdown[cat] = breakdown.get(cat, 0) + t['amount_paisa']
            total += t['amount_paisa']
    
    # Sort by amount desc
    sorted_breakdown = sorted(breakdown.items(), key=lambda item: item[1], reverse=True)
    return sorted_breakdown, total

def render_ascii_chart(title, data, total_amount):
    if total_amount == 0:
        return Panel("No data for chart", title=title)
    
    lines = []
    max_label_len = max([len(k) for k, v in data] + [0])
    
    for category, amount in data:
        percent = (amount / total_amount) * 100
        bar_len = int(percent / 2) # 50 chars = 100%
        bar = "█" * bar_len
        lines.append(f"{category.ljust(max_label_len)} {bar} {percent:.1f}% (Rs {amount/100:.0f})")
    
    return Panel("\n".join(lines), title=title)

def calculate_health_score(income, expenses, budgets, month_expenses_breakdown):
    score = 0
    breakdown = []

    # 1. Savings Rate (30 pts)
    savings = income - expenses
    savings_rate = (savings / income * 100) if income > 0 else 0
    
    if savings_rate >= 20:
        s_score = 30
    elif savings_rate >= 10:
        s_score = 20
    elif savings_rate > 0:
        s_score = 10
    else:
        s_score = 0
    
    score += s_score
    breakdown.append(f"Savings Rate ({savings_rate:.1f}%): {s_score}/30")

    # 2. Budget Adherence (25 pts)
    # Check if total expenses are within total budget (if budgets exist)
    total_budget = sum(b['limit_paisa'] for b in budgets)
    
    if total_budget > 0:
        budget_utilization = (expenses / total_budget) * 100
        if budget_utilization <= 100:
            b_score = 25
        elif budget_utilization <= 110:
            b_score = 15
        else:
            b_score = 0
    else:
        # If no budget set, give neutral points or assume based on income
        b_score = 25 if expenses < income else 0
    
    score += b_score
    breakdown.append(f"Budget Adherence: {b_score}/25")

    # 3. Cash Flow (25 pts)
    if income > expenses:
        c_score = 25
    elif income == expenses:
        c_score = 15
    else:
        c_score = 0
    
    score += c_score
    breakdown.append(f"Cash Flow (Income vs Exp): {c_score}/25")

    # 4. Debt/Risk Management (20 pts) - Simplified
    # Assume 20 if valid data exists and positive balance
    if savings >= 0:
        d_score = 20
    else:
        d_score = 0
    
    score += d_score
    breakdown.append(f"Sustainability: {d_score}/20")

    return score, breakdown

def show_analytics():
    all_transactions = load_transactions()
    all_budgets = load_budgets()

    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    last_month_date = now.replace(day=1) - timedelta(days=1)
    last_month_str = last_month_date.strftime("%Y-%m")

    # Current Month Data
    curr_txns = get_month_transactions(all_transactions, now.year, now.month)
    curr_inc, curr_exp = calculate_totals(curr_txns)
    curr_breakdown, curr_exp_total = get_category_breakdown(curr_txns)
    curr_budgets = [b for b in all_budgets if b['month_year'] == current_month_str]

    # Last Month Data
    last_txns = get_month_transactions(all_transactions, last_month_date.year, last_month_date.month)
    last_inc, last_exp = calculate_totals(last_txns)

    console.print(Panel.fit(f"[bold blue]Financial Analytics Report: {now.strftime('%B %Y')}[/bold blue]"))

    # 1. Overview Table
    ov_table = Table(title="Monthly Overview")
    ov_table.add_column("Metric")
    ov_table.add_column("Current Month", justify="right")
    ov_table.add_column("Last Month", justify="right")
    ov_table.add_column("Change", justify="right")

    def get_change_str(curr, last):
        if last == 0: return "-"
        diff = curr - last
        pct = (diff / last) * 100
        color = "green" if (diff >= 0 and "Income" in metric) or (diff <= 0 and "Expense" in metric) else "red"
        return f"[{color}]{pct:+.1f}%[/{color}]"

    metrics = [
        ("Total Income", curr_inc, last_inc),
        ("Total Expenses", curr_exp, last_exp),
        ("Savings", curr_inc - curr_exp, last_inc - last_exp)
    ]

    for metric, c_val, l_val in metrics:
        change = ""
        if l_val != 0:
            diff = c_val - l_val
            pct = (diff / l_val) * 100
            # Contextual coloring
            if "Expenses" in metric:
                color = "green" if diff <= 0 else "red"
            else:
                color = "green" if diff >= 0 else "red"
            change = f"[{color}]{pct:+.1f}%[/{color}]"
        
        ov_table.add_row(
            metric, 
            f"Rs {c_val/100:.2f}", 
            f"Rs {l_val/100:.2f}", 
            change
        )

    console.print(ov_table)

    # 2. Spending Analysis (Ascii Chart)
    if curr_exp_total > 0:
        console.print(render_ascii_chart("Spending by Category", curr_breakdown, curr_exp_total))
        
        # Burn Rate
        days_passed = now.day
        burn_rate = curr_exp / days_passed
        console.print(f"[bold]Daily Burn Rate:[/bold] Rs {burn_rate/100:.2f} / day")
    else:
        console.print("[yellow]No expenses recorded this month.[/yellow]")

    # 3. Health Score
    score, breakdown = calculate_health_score(curr_inc, curr_exp, curr_budgets, curr_breakdown)
    
    score_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
    
    health_panel = Panel(
        f"[bold {score_color} size=20]Score: {score}/100[/bold {score_color} size=20]\n\n" +
        "\n".join([f"- {item}" for item in breakdown]),
        title="Financial Health Score"
    )
    console.print(health_panel)

    # Recommendations
    recs = []
    savings_rate = ((curr_inc - curr_exp) / curr_inc * 100) if curr_inc > 0 else 0
    if savings_rate < 20:
        recs.append("📉 [bold red]Low Savings:[/bold red] Try to save at least 20% of income.")
    if curr_exp > curr_inc:
        recs.append("⚠️ [bold red]Deficit:[/bold red] You are spending more than you earn!")
    if not curr_budgets:
        recs.append("💡 [bold yellow]No Budgets:[/bold yellow] Set category budgets to control spending.")
    
    if recs:
        console.print(Panel("\n".join(recs), title="Recommendations", style="bold white"))
    else:
        console.print(Panel("🎉 Great job! Your finances look healthy.", title="Recommendations", style="bold green"))