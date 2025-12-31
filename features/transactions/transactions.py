import os
import uuid
from datetime import datetime
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
DB_PATH = os.path.join("database", "transactions.txt")

EXPENSE_CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"]
INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]

def load_transactions():
    transactions = []
    if not os.path.exists(DB_PATH):
        return transactions
    
    with open(DB_PATH, "r") as f:
        for line in f:
            if line.strip():
                parts = line.strip().split("|")
                if len(parts) == 6:
                    transactions.append({
                        "id": parts[0],
                        "date": parts[1],
                        "type": parts[2],
                        "category": parts[3],
                        "amount_paisa": int(parts[4]),
                        "description": parts[5]
                    })
    return transactions

def save_transaction(t):
    with open(DB_PATH, "a") as f:
        line = f"{t['id']}|{t['date']}|{t['type']}|{t['category']}|{t['amount_paisa']}|{t['description']}\n"
        f.write(line)

def validate_amount(text):
    try:
        val = float(text)
        if val <= 0:
            return "Amount must be positive"
        return True
    except ValueError:
        return "Please enter a valid number"

def validate_date(text):
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return "Format must be YYYY-MM-DD"

def add_transaction():
    type = questionary.select(
        "Select transaction type:",
        choices=["Expense", "Income"]
    ).ask()

    if not type: return

    categories = EXPENSE_CATEGORIES if type == "Expense" else INCOME_CATEGORIES
    
    amount_str = questionary.text(
        f"Enter {type} amount:",
        validate=validate_amount
    ).ask()
    if not amount_str: return
    amount_paisa = int(round(float(amount_str) * 100))

    category = questionary.select(
        "Select category:",
        choices=categories
    ).ask()
    if not category: return

    description = questionary.text("Enter description:").ask()
    if description is None: return

    date_str = questionary.text(
        "Enter date (YYYY-MM-DD) [Default: Today]:",
        default=datetime.now().strftime("%Y-%m-%d"),
        validate=validate_date
    ).ask()
    if not date_str: return

    transaction = {
        "id": str(uuid.uuid4())[:8],
        "date": date_str,
        "type": type,
        "category": category,
        "amount_paisa": amount_paisa,
        "description": description
    }

    save_transaction(transaction)
    console.print(f"[bold green]Successfully added {type}![/bold green]")

def view_transactions():
    transactions = load_transactions()
    if not transactions:
        console.print("[yellow]No transactions found.[/yellow]")
        return

    filter_choice = questionary.select(
        "Filter transactions?",
        choices=["Show All", "Last 7 Days", "Expenses Only", "Income Only", "Back"]
    ).ask()

    if filter_choice == "Back" or not filter_choice:
        return

    filtered = transactions
    if filter_choice == "Last 7 Days":
        today = datetime.now()
        filtered = [
            t for t in transactions 
            if (today - datetime.strptime(t['date'], "%Y-%m-%d")).days <= 7
        ]
    elif filter_choice == "Expenses Only":
        filtered = [t for t in transactions if t['type'] == "Expense"]
    elif filter_choice == "Income Only":
        filtered = [t for t in transactions if t['type'] == "Income"]

    # Sort by date newest first
    filtered.sort(key=lambda x: x['date'], reverse=True)

    table = Table(title=f"Transactions ({filter_choice})")
    table.add_column("Date", style="cyan")
    table.add_column("Type")
    table.add_column("Category", style="magenta")
    table.add_column("Description")
    table.add_column("Amount", justify="right")

    for t in filtered:
        amount_display = f"Rs {t['amount_paisa'] / 100:.2f}"
        color = "red" if t['type'] == "Expense" else "green"
        table.add_row(
            t['date'],
            f"[{color}]{t['type']}[/{color}]",
            t['category'],
            t['description'],
            f"[{color}]{amount_display}[/{color}]"
        )

    console.print(table)

def show_balance():
    transactions = load_transactions()
    current_month = datetime.now().strftime("%Y-%m")
    
    total_income = sum(t['amount_paisa'] for t in transactions if t['type'] == "Income" and t['date'].startswith(current_month))
    total_expense = sum(t['amount_paisa'] for t in transactions if t['type'] == "Expense" and t['date'].startswith(current_month))
    balance = total_income - total_expense

    table = Table(title=f"Financial Summary - {datetime.now().strftime('%B %Y')}")
    table.add_column("Metric")
    table.add_column("Amount", justify="right")

    table.add_row("Total Income", f"[green]Rs {total_income / 100:.2f}[/green]")
    table.add_row("Total Expenses", f"[red]Rs {total_expense / 100:.2f}[/red]")
    
    balance_color = "green" if balance >= 0 else "red"
    table.add_row("Current Balance", f"[{balance_color}]Rs {balance / 100:.2f}[/{balance_color}]")

    console.print(table)