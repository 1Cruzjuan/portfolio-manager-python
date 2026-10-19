from datetime import date
import pandas as pd
import os
import json

JSON_FILE = "portfolio_base_data.json"

# VALIDATION HELPER FUNCTIONS (TRY/EXCEPT)

def get_number(message):
    while True:
        try:
            return float(input(message))
        except ValueError:
            print("❌ Error: Please enter a valid number (e.g., 100 or 150.5).")

def get_integer_in_range(message, min_val, max_val):
    while True:
        try:
            value = int(input(message))
            if min_val <= value <= max_val:
                return value
            else:
                print(f"❌ Error: Choose an option between {min_val} and {max_val}.")
        except ValueError:
            print("❌ Error: Please enter an integer.")

def get_date(message="Date (YYYY-MM-DD) [Enter for today]: "):
    while True:
        date_str = input(message).strip()
        if not date_str:
            return date.today().isoformat()
        try:
            pd.to_datetime(date_str, format='%Y-%m-%d')
            return date_str
        except ValueError:
            print("❌ Error: Incorrect format. Must be YYYY-MM-DD (e.g., 2026-10-18).")

def get_fund_type(message):
    while True:
        try:
            fund_type = input(message).strip().capitalize()
            if fund_type not in ["Amount", "Ratio"]:
                raise ValueError
            return fund_type
        except ValueError:
            print("❌ Error: Fund type can only be 'Amount' or 'Ratio'.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# CLASSES

class Portfolio:
    def __init__(self, name):
        self.name = name
        self.funds = []

    def add_fund(self, fund):
        self.funds.append(fund)

    def import_data(self):
        if not os.path.exists(f'{self.name}.csv'):
            return 
            
        df = pd.read_csv(f'{self.name}.csv', index_col='Date', parse_dates=['Date'])
        
        for fund in self.funds:
            if fund.name in df.columns:
                fund.daily_data = df[fund.name].dropna().sort_index()

    def get_daily_pnl_df(self):
        df = pd.DataFrame({fund.name: fund.get_daily_pnl() for fund in self.funds})
        df[self.name] = df.sum(axis=1)
        return df

    def get_daily_capital_df(self):
        df = pd.DataFrame({fund.name: fund.get_daily_capital() for fund in self.funds})
        df[self.name] = df.sum(axis=1)
        return df

    def get_daily_roi_df(self):
        df = pd.DataFrame({fund.name: fund.get_daily_roi() for fund in self.funds})
        df_pnl = self.get_daily_pnl_df()
        
        df_base_cap = pd.DataFrame()
        for fund in self.funds:
            if fund.fund_type.capitalize() == "Amount":
                df_base_cap[fund.name] = fund.get_daily_base_capital()
            else:
                df_base_cap[fund.name] = fund.get_daily_capital()
                
        if not df_base_cap.empty:
            total_cap = df_base_cap.sum(axis=1)
            total_roi = df_pnl[self.name] / total_cap
            df[self.name] = total_roi.replace([float('inf'), -float('inf')], 0).fillna(0)
        else:
            df[self.name] = 0
            
        return df

    def get_avg_daily_pnl(self):
        return self.get_daily_pnl_df().mean().to_dict()

    def get_avg_daily_roi(self):
        return self.get_daily_roi_df().mean().to_dict()

    def get_total_pnl(self):
        daily_df = pd.DataFrame({f.name: f.daily_data for f in self.funds})
        if daily_df.empty:
            totals = {f.name: 0 for f in self.funds}
            totals[self.name] = 0
            return totals
            
        totals = daily_df.iloc[-1].fillna(0).to_dict()
        totals[self.name] = sum(totals.values())
        return totals

    def get_total_roi(self):
        total_roi = {}
        total_base_capital = 0
        
        for fund in self.funds:
            total_roi[fund.name] = fund.get_total_roi()[0]
            
            if fund.fund_type.capitalize() == "Amount":
                total_base_capital += float(fund.initial_capital)
            else:
                total_base_capital += float(fund.initial_capital) + fund.get_total_pnl()
            
        overall_total_pnl = self.get_total_pnl()[self.name]
        total_roi[self.name] = overall_total_pnl / total_base_capital if total_base_capital else 0
        return total_roi

class Fund:
    def __init__(self, name, capital, fund_type, active=True, movements=None):
        self.name = name
        self.initial_capital = float(capital)
        self.fund_type = fund_type
        self.active = active
        self.daily_data = pd.Series(dtype=float)
        
        movs = movements if movements is not None else {}
        self.movements = pd.Series(movs, dtype=float)
        if not self.movements.empty:
            self.movements.index = pd.to_datetime(self.movements.index)
            self.movements = self.movements.sort_index()

    def get_daily_pnl(self):
        if self.daily_data.empty:
            return pd.Series(dtype=float)
        pnl = self.daily_data.diff()
        pnl.iloc[0] = self.daily_data.iloc[0]
        return pnl

    def add_daily_data(self, date_val, num):
        dt_date = pd.to_datetime(date_val)
        self.daily_data.loc[dt_date] = float(num)
        self.daily_data = self.daily_data.sort_index()

    def register_movement(self, date_val, num):
        self.movements.loc[pd.to_datetime(date_val)] = float(num)
        self.movements = self.movements.sort_index()

    def deactivate_fund(self, date_val):
        self.active = False
        self.register_movement(date_val, - self.get_total_pnl())

    def get_daily_base_capital(self):
        if self.daily_data.empty:
            return pd.Series(dtype=float)
        all_dates = self.daily_data.index.union(self.movements.index).sort_values()
        reindexed_movs = self.movements.reindex(all_dates, fill_value=0)
        accumulated_capital = reindexed_movs.cumsum() + self.initial_capital
        return accumulated_capital.reindex(self.daily_data.index, method='ffill')

    def get_daily_capital(self):
        if self.daily_data.empty:
            return pd.Series(dtype=float)
        return self.get_daily_base_capital() + self.daily_data

    def get_daily_roi(self):
        pnl = self.get_daily_pnl()
        if self.fund_type.capitalize() == "Amount":
            cap = self.get_daily_base_capital()
        else:
            cap = self.get_daily_capital()
            
        roi = pnl / cap
        return roi.replace([float('inf'), -float('inf')], 0).fillna(0)

    def get_total_pnl(self):
        return self.daily_data.iloc[-1] if not self.daily_data.empty else 0

    def get_total_roi(self):
        certainty = self.movements.empty
        total_pnl = self.get_total_pnl()
        
        if self.fund_type.capitalize() == "Amount":
            base = self.initial_capital
        else:
            base = self.initial_capital + total_pnl
            
        return (total_pnl / base if base else 0, certainty)

# USER INTERFACE (UI)

def create_fund_ui(current_portfolio):
    print("\n--- CREATE NEW FUND ---")
    name = input("Fund name: ")
    capital = get_number("Initial capital: ")
    fund_type = get_fund_type("Type (Amount/Ratio): ")
    new_fund = Fund(name, capital, fund_type)
    current_portfolio.add_fund(new_fund)
    print(f"✅ Fund '{name}' successfully created.")

def add_daily_data_ui(current_portfolio):
    print("\n--- ADD DAILY DATA ---")
    date_val = get_date()
    active_funds = [f for f in current_portfolio.funds if f.active]
    
    if not active_funds:
        print("⚠️ There are no active funds in this portfolio.")
        return
        
    for fund in active_funds:
        num = get_number(f"Value for {fund.name}: ")
        fund.add_daily_data(date_val, num)
    print(f"✅ Data for {date_val} successfully saved.")

def show_data_ui(current_portfolio):
    print("\n--- SHOW DATA ---")
    print("1. Daily PNL")
    print("2. Daily Capital")
    print("3. Daily ROI")
    print("4. Averages and Totals")
    option = str(get_integer_in_range("Choose an option (1-4): ", 1, 4))
    
    print("\nGenerating table...\n" + "-"*40)
    
    print_format = None
    csv_format = None

    match option:
        case "1":
            df = current_portfolio.get_daily_pnl_df()
            print_format = lambda x: f"{x:.2f}"
            csv_format = '%.2f'
            path = f'exported/{current_portfolio.name}_daily_pnl.csv'
        case "2":
            df = current_portfolio.get_daily_capital_df()
            print_format = lambda x: f"{x:.2f}"
            csv_format = '%.2f'
            path = f'exported/{current_portfolio.name}_daily_capital.csv'
        case "3":
            df = current_portfolio.get_daily_roi_df()
            print_format = lambda x: f"{x * 100:.2f}%"
            csv_format = '%.4f'
            path = f'exported/{current_portfolio.name}_daily_roi.csv'
        case "4":
            data = {
                "Avg Daily PNL" : current_portfolio.get_avg_daily_pnl(),
                "Avg Daily ROI" : current_portfolio.get_avg_daily_roi(),
                "Total PNL" : current_portfolio.get_total_pnl(),
                "Total ROI" : current_portfolio.get_total_roi(),
            }
            df = pd.DataFrame(data).T
            df = df.astype(object) 
            for idx in df.index:
                if "ROI" in idx:
                    df.loc[idx] = df.loc[idx].apply(lambda x: f"{x * 100:.3f}%" if pd.notnull(x) else "0.000%")
                else:
                    df.loc[idx] = df.loc[idx].apply(lambda x: f"{float(x):.3f}" if pd.notnull(x) else "0.000")
            path = f'exported/{current_portfolio.name}_averages_and_totals.csv'

    inactive_funds = [f.name for f in current_portfolio.funds if not f.active]
    visible_columns = [col for col in df.columns if col not in inactive_funds]
    
    if option in {"1", "2", "3"}:
        print(df[visible_columns].to_string(float_format=print_format))
    else:
        print(df[visible_columns].to_string())
        
    print("-" * 40)
    
    print("Do you want to export the complete table? Y/N")
    answer = input().strip().upper()
    if answer == "Y":
        os.makedirs('exported', exist_ok=True)
        
        if option in {"1", "2", "3"}:
            df.index = df.index.strftime('%Y-%m-%d')
            df.to_csv(path, index_label='Date', encoding='utf-8', float_format=csv_format)
        else:
            df.to_csv(path, index_label='Metric', encoding='utf-8')
        print(f"📁 Data exported to: {path}")

def close_fund_ui(current_portfolio):
    print("\n--- CLOSE FUND ---")
    date_val = get_date()
    for i, fund in enumerate(current_portfolio.funds):
        print(f"{i}: Fund {fund.name}")
    option = get_integer_in_range("Index of the fund to close: ", 0, len(current_portfolio.funds) -1)
    fund = current_portfolio.funds[option]
    fund.deactivate_fund(date_val)
    print(f"✅ Fund '{fund.name}' deactivated.")

def modify_capital_ui(current_portfolio):
    print("\n--- MODIFY CAPITAL (Deposit/Withdrawal) ---")
    date_val = get_date()
    for i, fund in enumerate(current_portfolio.funds):
        print(f"{i}: Fund {fund.name}")
    option = get_integer_in_range("Index of the fund: ", 0, len(current_portfolio.funds) -1)
    fund = current_portfolio.funds[option]
    num = get_number("Amount (positive for deposit, negative for withdrawal): ")
    fund.register_movement(date_val, num)
    print(f"✅ Movement of {num} registered on {date_val}.")

def create_portfolio_ui(portfolio_list):
    print("\n--- CREATE PORTFOLIO ---")
    name = input("Portfolio name: ")
    portfolio_list.append(Portfolio(name))
    print(f"✅ Portfolio '{name}' created.")

def save_data_csv(portfolio_list):
    for port in portfolio_list:
        data = {fund.name: fund.daily_data for fund in port.funds if not fund.daily_data.empty}
        if data:
            df = pd.DataFrame(data)
            df.index = df.index.strftime('%Y-%m-%d')
            df.to_csv(f'{port.name}.csv', index_label='Date', encoding='utf-8')

def save_data_json(portfolio_list):
    portfolio_data = {}
    for port in portfolio_list:
        funds_data_per_port = {}
        for fund in port.funds:
            movements_str = {k.strftime('%Y-%m-%d'): v for k, v in fund.movements.items()}
            
            funds_data_per_port[fund.name] = {
                "type" : fund.fund_type, 
                "capital" : fund.initial_capital,
                "active" : fund.active,
                "movements": movements_str
            }
        portfolio_data[port.name] = funds_data_per_port
    
    with open(JSON_FILE, 'w', encoding='utf-8') as file:
        json.dump(portfolio_data, file, indent=4, ensure_ascii=False)


# MAIN EXECUTION BLOCK
portfolio_list = []

if os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for key, value in data.items():
        created = Portfolio(key)
        for fund_key, fund in value.items():
            movements = fund.get("movements", {})
            new_fund = Fund(fund_key, fund["capital"], fund["type"], fund["active"], movements=movements)
            created.add_fund(new_fund)

        created.import_data()
        portfolio_list.append(created)

exit_flag = False
while not exit_flag:
    clear_screen()
    print("="*50)
    print(" 📊 PORTFOLIO MANAGER ".center(50))
    print("="*50)
    
    if not portfolio_list:
        print("\n⚠️ No portfolios found. You must create one first.")
        create_portfolio_ui(portfolio_list)
        input("\nPress Enter to continue...")
        continue
        
    print("\n" + " MAIN MENU ".center(50, "-"))
    print("1. Create new fund")
    print("2. Add daily data")
    print("3. Show data")
    print("4. Close fund")
    print("5. Modify capital (movements)")
    print("6. Create new portfolio")
    print("0. Save and Exit")
    print("-" * 50)
    
    option = str(get_integer_in_range("Choose an option: ", 0, 6))

    if option == "0":
        exit_flag = True
        break

    idx = 0
    if option != "6" and len(portfolio_list) > 1:
        print("\n--- PORTFOLIO SELECTION ---")
        for i, p in enumerate(portfolio_list):
            print(f"[{i}] {p.name}")
        idx = get_integer_in_range(f"Choose the index (0 to {len(portfolio_list)-1}): ", 0, len(portfolio_list)-1)
    current_portfolio = portfolio_list[idx]

    match option:
        case "1": create_fund_ui(current_portfolio)
        case "2": add_daily_data_ui(current_portfolio)
        case "3": show_data_ui(current_portfolio)
        case "4": close_fund_ui(current_portfolio)
        case "5": modify_capital_ui(current_portfolio)
        case "6": create_portfolio_ui(portfolio_list)
            
    input("\nPress Enter to return to the menu...")

print("\nSaving data...")
save_data_csv(portfolio_list)
save_data_json(portfolio_list)
print("✅ Data saved.")