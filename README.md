# 💰 FinTrack Pro: Personal Finance Tracker

FinTrack Pro is a dual-interface financial management system featuring a powerful **Interactive CLI** and a modern **Streamlit Web Dashboard**. It helps you track expenses, manage budgets, analyze spending patterns, and reach your financial goals with intelligent recommendations.

## 🚀 Features

### 💻 Interactive CLI
- **Transaction Management**: Add income and expenses with real-time validation.
- **Budget Tracking**: Set monthly limits and monitor category-wise spending.
- **Financial Analytics**: View reports and financial health scores directly in the terminal.
- **Rich UI**: Beautiful tables, panels, and progress bars powered by the `Rich` library.

### 🌐 Web Dashboard (Streamlit)
- **Financial Overview**: High-level metrics for balance, income, and expenses.
- **Interactive Charts**: Visual breakdown of spending by category and daily trends.
- **Budget Progress**: Real-time progress bars with color-coded alerts (Green/Yellow/Red).
- **Goal Manager**: Track long-term financial goals like Emergency Funds or Savings.
- **Data Export**: One-click downloads of your data in CSV or JSON formats.

---

## 🛠️ Tech Stack
- **Language**: Python 3.11+
- **Web Framework**: Streamlit
- **CLI Framework**: Questionary & Rich
- **Data Handling**: Pandas
- **Package Manager**: [UV](https://github.com/astral-sh/uv) (Fast Python package installer)

---

## 📥 Installation

This project uses `uv` for lightning-fast dependency management.

1. **Install uv** (if you haven't):
   ```powershell
   powershell -c "irm https://astral-sh/uv/install.ps1 | iex"
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/ZakheerAli/Personal-Finance-Tracker.git
   cd Personal-Finance-Tracker
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

---

## 🏃 How to Run

### 1. Launch the CLI Application
The CLI is the primary interactive tool for quick data entry and terminal-based management.
```bash
uv run main.py
```

### 2. Launch the Web Dashboard
The Streamlit app provides a visual, graphical overview of your finances.
```bash
uv run streamlit run app.py
```

---

## 📂 Project Structure
```
Personal-Finance-Tracker/
├── app.py                 # Streamlit Web Application
├── main.py                # CLI Entry Point
├── database/              # Flat-file storage (TXT)
│   ├── transactions.txt
│   ├── budgets.txt
│   └── goals.txt
├── features/              # Modular feature logic
│   ├── transactions/
│   ├── budgets/
│   ├── financial_analytics/
│   ├── smart_assistant/
│   └── data_management/
├── exports/               # Generated CSV/JSON exports
└── pyproject.toml         # Project dependencies
```

---

## ☁️ Deployment on Streamlit Cloud

1. Push your code to a GitHub repository (already done!).
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account.
4. Select this repository and the `app.py` file.
5. Click **Deploy**!

> **Note**: Since this app uses local text files for storage, data will reset if the Streamlit Cloud instance restarts. For permanent cloud storage, consider connecting a database like Supabase or Google Sheets.

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
