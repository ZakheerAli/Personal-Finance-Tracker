# Data Management System

## Goal
Enable users to export their financial data for external use (Excel, Backup, etc.).

## Features to Build

### 1. Export Transactions
- Formats: CSV, JSON
- Columns (CSV): Date, Type, Category, Amount (Rs), Description, ID
- File naming: `exports/transactions_YYYY-MM-DD.csv`

### 2. Export Budgets
- Formats: CSV
- Columns: Month, Category, Limit, Status
- File naming: `exports/budgets_YYYY-MM-DD.csv`

### 3. Clear Data (Optional/Advanced)
- Option to reset database (with confirmation)

## Success Criteria
✅ Can export transactions to CSV
✅ Can export transactions to JSON
✅ Exports are saved in `exports/` folder
✅ User notified of file location
