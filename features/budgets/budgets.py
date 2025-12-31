import os
import questionary
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import BarColumn, Progress, TextColumn
from rich.panel import Panel

# Import shared resources
from features.transactions.transactions import load_transactions, EXPENSE_CATEGORIES, validate_amount

console = Console()
DB_PATH = os.path.join("database", "budgets.txt")

def load_budgets():
    """
    Returns a list of budget dicts:
    [{'category': 'Food', 'limit_paisa': 500000, 'month_year': '2023-10'}]
    """
    budgets = []
    if not os.path.exists(DB_PATH):
        return budgets

    with open(DB_PATH, "r") as f:
        for line in f:
            if line.strip():
                parts = line.strip().split("|")
                if len(parts) == 3:
                    budgets.append({
                        "category": parts[0],
                        "limit_paisa": int(parts[1]),
                        "month_year": parts[2]
                    })
    return budgets

def save_all_budgets(budgets):
    with open(DB_PATH, "w") as f:
        for b in budgets:
            f.write(f"{b['category']}|{b['limit_paisa']}|{b['month_year']}\n")

def set_budget():
    category = questionary.select(
        "Select Category to Budget:",
        choices=EXPENSE_CATEGORIES + ["Back"]
    ).ask()

    if category == "Back" or not category:
        return

    amount_str = questionary.text(
        f"Enter monthly budget for {category}:",
        validate=validate_amount
    ).ask()

    if not amount_str:
        return
    
    amount_paisa = int(round(float(amount_str) * 100))
    current_month = datetime.now().strftime("%Y-%m")

    # Load existing budgets to check for update
    budgets = load_budgets()
    
    # Check if budget already exists for this category/month
    existing_index = -1
    for i, b in enumerate(budgets):
        if b['category'] == category and b['month_year'] == current_month:
            existing_index = i
            break
    
    new_budget = {
        "category": category,
        "limit_paisa": amount_paisa,
        "month_year": current_month
    }

    if existing_index >= 0:
        # Update existing
        if questionary.confirm(f"Budget for {category} already exists. Overwrite?", default=True).ask():
            budgets[existing_index] = new_budget
        else:
            return
    else:
        # Add new
        budgets.append(new_budget)

    save_all_budgets(budgets)
    console.print(f"[bold green]Budget set for {category}: Rs {amount_paisa/100:.2f}[/bold green]")

def view_budget():
    current_month = datetime.now().strftime("%Y-%m")
    transactions = load_transactions()
    budgets = load_budgets()

    # Filter budgets for current month
    month_budgets = [b for b in budgets if b['month_year'] == current_month]

    if not month_budgets:
        console.print(f"[yellow]No budgets set for {datetime.now().strftime('%B %Y')}.[/yellow]")
        return

    # Calculate spending per category for current month
    spending = {cat: 0 for cat in EXPENSE_CATEGORIES}
    for t in transactions:
        if t['type'] == "Expense" and t['date'].startswith(current_month):
            if t['category'] in spending:
                spending[t['category']] += t['amount_paisa']
            else:
                # Handle categories that might not be in the default list or changed
                spending[t['category']] = spending.get(t['category'], 0) + t['amount_paisa']

    # Build Table
    table = Table(title=f"Budget Status - {datetime.now().strftime('%B %Y')}")
    table.add_column("Category", style="cyan")
    table.add_column("Budget", justify="right")
    table.add_column("Spent", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Utilization", justify="center", width=20) # Progress bar
    table.add_column("Status")

    total_budget = 0
    total_spent = 0

    for b in month_budgets:
        cat = b['category']
        limit = b['limit_paisa']
        spent = spending.get(cat, 0)
        remaining = limit - spent
        
        utilization = (spent / limit) * 100 if limit > 0 else 0
        
        total_budget += limit
        total_spent += spent

        # Determine Color/Status
        if utilization > 100:
            color = "red"
            status = "OVER"
        elif utilization >= 70:
            color = "yellow"
            status = "WARNING"
        else:
            color = "green"
            status = "OK"

        # Progress Bar visual
        # Simple text representation of progress bar since Rich Table cells expect strings or renderables
        # Using a simple ascii or block char logic for "Utilization" column if simple string
        # BUT Rich can render BarColumn if used in Progress, but here we are in a Table.
        # We can use a simple string formatting or a small nested table/panel, 
        # but let's stick to a colored percentage string + simple bar for clarity in a table cell.
        
        bar_length = 10
        filled_length = int(min(utilization, 100) / 100 * bar_length)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        table.add_row(
            cat,
            f"Rs {limit/100:.2f}",
            f"Rs {spent/100:.2f}",
            f"[{color}]Rs {remaining/100:.2f}[/{color}]",
            f"[{color}]{bar} {utilization:.1f}%[/{color}]",
            f"[{color}]{status}[/{color}]"
        )

    console.print(table)

    # Overall Summary
    console.print(Panel(
        f"Total Budget: [bold]Rs {total_budget/100:.2f}[/bold]\n"
        f"Total Spent:  [bold]Rs {total_spent/100:.2f}[/bold]\n"
        f"Remaining:    [bold]Rs {(total_budget - total_spent)/100:.2f}[/bold]",
        title="Monthly Summary",
        expand=False
    ))