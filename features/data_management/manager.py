import os
import csv
import json
import questionary
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from features.transactions.transactions import load_transactions
from features.budgets.budgets import load_budgets

console = Console()
EXPORT_DIR = "exports"

def ensure_export_dir():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

def export_transactions_csv():
    ensure_export_dir()
    transactions = load_transactions()
    
    filename = f"transactions_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date", "Type", "Category", "Amount (Rs)", "Description"])
            
            for t in transactions:
                writer.writerow([
                    t['id'],
                    t['date'],
                    t['type'],
                    t['category'],
                    f"{t['amount_paisa']/100:.2f}",
                    t['description']
                ])
        
        console.print(f"[green]Successfully exported transactions to:[/green] {filepath}")
    except Exception as e:
        console.print(f"[red]Error exporting CSV:[/red] {e}")

def export_transactions_json():
    ensure_export_dir()
    transactions = load_transactions()
    
    filename = f"transactions_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    filepath = os.path.join(EXPORT_DIR, filename)
    
    # Convert paisa to Rs for export or keep raw? Let's keep raw structure but maybe add formatted
    export_data = []
    for t in transactions:
        t_copy = t.copy()
        t_copy['amount_rs'] = t['amount_paisa'] / 100
        export_data.append(t_copy)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4)
            
        console.print(f"[green]Successfully exported transactions to:[/green] {filepath}")
    except Exception as e:
        console.print(f"[red]Error exporting JSON:[/red] {e}")

def export_budgets_csv():
    ensure_export_dir()
    budgets = load_budgets()
    
    filename = f"budgets_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Month", "Category", "Limit (Rs)"])
            
            for b in budgets:
                writer.writerow([
                    b['month_year'],
                    b['category'],
                    f"{b['limit_paisa']/100:.2f}"
                ])
                
        console.print(f"[green]Successfully exported budgets to:[/green] {filepath}")
    except Exception as e:
        console.print(f"[red]Error exporting Budgets:[/red] {e}")

def menu():
    while True:
        choice = questionary.select(
            "Data Management:",
            choices=[
                "Export Transactions (CSV)",
                "Export Transactions (JSON)",
                "Export Budgets (CSV)",
                "Back"
            ]
        ).ask()
        
        if choice == "Export Transactions (CSV)":
            export_transactions_csv()
        elif choice == "Export Transactions (JSON)":
            export_transactions_json()
        elif choice == "Export Budgets (CSV)":
            export_budgets_csv()
        elif choice == "Back" or not choice:
            break
