import questionary
from rich.console import Console
from rich.panel import Panel
from features.transactions import transactions
from features.budgets import budgets
from features.financial_analytics import analytics
from features.smart_assistant import assistant
from features.data_management import manager

console = Console()

def main():
    console.print(Panel.fit("[bold green]Personal Finance Tracker CLI[/bold green]", subtitle="Welcome"))

    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Manage Transactions",
                "Manage Budgets",
                "View Analytics",
                "Smart Assistant",
                "Data Management",
                "Exit"
            ]
        ).ask()

        if choice == "Manage Transactions":
            action = questionary.select(
                "Transaction Options:",
                choices=["Add Transaction", "View Transactions", "View Balance", "Back"]
            ).ask()
            if action == "Add Transaction":
                transactions.add_transaction()
            elif action == "View Transactions":
                transactions.view_transactions()
            elif action == "View Balance":
                transactions.show_balance()
        
        elif choice == "Manage Budgets":
            action = questionary.select(
                "Budget Options:",
                choices=["Set Budget", "View Budget", "Back"]
            ).ask()
            if action == "Set Budget":
                budgets.set_budget()
            elif action == "View Budget":
                budgets.view_budget()

        elif choice == "View Analytics":
            analytics.show_analytics()

        elif choice == "Smart Assistant":
            assistant.assistant_menu()

        elif choice == "Data Management":
            manager.menu()

        elif choice == "Exit":
            console.print("[bold red]Goodbye![/bold red]")
            break

if __name__ == "__main__":
    main()