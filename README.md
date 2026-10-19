# Portfolio Manager

A lightweight, object-oriented Python application for tracking personal financial portfolios, daily performance metrics, cash movements, and return on investment (ROI).



## Key Features

- **Multi-Portfolio Support**: Manage multiple investment portfolios within a single interface.
- **Fund Performance Metrics**: Tracks daily PnL (Profit and Loss), Capital, and ROI (Return on Investment) across all active funds.
- **Flexible Fund Types**:
  - **Amount-based**: Capital scales directly with account balance.
  - **Ratio-based**: Designed for strategy-based returns or relative yields.
- **Cash Flow Tracking**: Handles deposits, withdrawals, and capital adjustments with full historical record-keeping.
- **Data Persistence**: Automatically exports and syncs portfolio structures and transaction logs across JSON and CSV formats.
- **Export Capabilities**: Generate printable summaries or CSV files formatted for analysis.



## Tech Stack

- **Language**: Python 3.10+
- **Data Processing**: [pandas](https://pandas.pydata.org/)
- **Storage**: JSON / CSV



## Architecture Overview

The project is structured around two core domain models:
- Portfolio: Acts as a container for multiple funds. Handles matrix operations using pandas.DataFrame to calculate aggregated daily PnL, total daily capital, average returns, and overall portfolio ROI.
- Fund: Represents an individual asset or strategy. Manages transaction logs, daily series values, deactivations, and baseline capital calculations.



## Project Structure

```text
├── main.py                     # Primary execution script & CLI interface
├── portfolio_base_data.json    # JSON storage for portfolios, funds, and transaction history
├── <Portfolio_Name>.csv        # Individual portfolio historical daily data
└── exported/                   # Folder containing generated report CSV exports
