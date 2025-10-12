import yfinance as yf
import json
import time
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

def get_price(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='1d')
    if hist.empty or 'Close' not in hist or hist['Close'].empty:
        console.print(f"[bold red]Error: No price data found for {ticker}.[/bold red]")
        return None
    price = hist['Close'].iloc[0]
    return float(round(price, 2))

def buy():
    ticker = input("Enter ticker symbol to buy: ").strip().upper()
    price = get_price(ticker)
    if price is None:
        console.print("[bold red]Purchase aborted due to unavailable price.[/bold red]")
        return
    price = float(price)
    console.print(f"[bold white]Current Ticker Price:[/bold white] [bold cyan]{price}[/bold cyan]")
    qty = int(input("Enter quantity to buy: ").strip())
    
    try:
        stock = yf.Ticker(ticker)
        sector = stock.info.get('sector', 'Unknown')
    except Exception:
        sector = 'Unknown'
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)
        cash_balance = portfolio.get("cash_balance")
        holdings = portfolio.get("holdings")
    total_cost = price * qty
    if total_cost > cash_balance:
        console.print("[bold red]Insufficient funds to complete purchase.[/bold red]")
        return
    cash_balance -= total_cost
    
    if ticker not in holdings:
        holdings[ticker] = []
    holdings[ticker].append({"qty": int(qty), "price": float(price), "sector": sector})
    portfolio.update({"cash_balance": cash_balance, "holdings": holdings})
    with open('data/portfolio.json', 'w') as f:
        json.dump(portfolio, f, indent=4)
    input("Press Enter to return to main menu...")
    return

def sell():
    
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)
        cash_balance = portfolio.get("cash_balance")
        holdings = portfolio.get("holdings")
    if not holdings:
        console.print("[bold yellow]You have no assets to sell.[/bold yellow]")
        return
    console.print("[bold white]Your current assets:[/bold white]")
    for ticker, lots in holdings.items():
        total_qty = sum(int(lot['qty']) for lot in lots)
        avg_price = round(sum(int(lot['qty']) * float(lot['price']) for lot in lots) / total_qty, 2) if total_qty > 0 else 0
        sector = lots[0].get('sector', 'Unknown') if lots else 'Unknown'
        console.print(f"  [bold cyan]{ticker}[/bold cyan]: {total_qty} shares (Bought at: ${avg_price}, Sector: [bold cyan]{sector}[/bold cyan])")
    ticker = input("Enter ticker symbol to sell: ").strip().upper()
    if ticker not in holdings or sum(int(lot['qty']) for lot in holdings[ticker]) == 0:
        console.print("[bold red]Insufficient holdings to complete sale.[/bold red]")
        return
    price = get_price(ticker)
    if price is None:
        console.print("[bold red]Sale aborted due to unavailable price.[/bold red]")
        return
    price = float(round(price, 2))
    console.print(f"[bold white]Current Ticker Price:[/bold white] [bold cyan]{price}[/bold cyan]")
    qty = int(input("Enter quantity to sell: ").strip())
    total_qty = sum(int(lot['qty']) for lot in holdings[ticker])
    if qty > total_qty:
        console.print("[bold red]Insufficient holdings to complete sale.[/bold red]")
        return
    
    qty_to_sell = qty
    lots = holdings[ticker]
    sold_lots = []
    while qty_to_sell > 0 and lots:
        lot = lots[0]
        sell_qty = min(int(lot['qty']), qty_to_sell)
        sold_lots.append({'qty': sell_qty, 'buy_price': float(lot['price'])})
        lot['qty'] -= sell_qty
        qty_to_sell -= sell_qty
        if lot['qty'] == 0:
            lots.pop(0)
    total_revenue = price * qty
    cash_balance += total_revenue
    if not lots:
        del holdings[ticker]
    portfolio.update({"cash_balance": cash_balance, "holdings": holdings})
    with open('data/portfolio.json', 'w') as f:
        json.dump(portfolio, f, indent=4)
    
    console.print(f"[bold green]Sold {qty} shares of {ticker} at ${price} per share.[/bold green]")
    for lot in sold_lots:
        diff = round(price - lot['buy_price'], 2)
        color = "green" if diff >= 0 else "red"
        console.print(f"  - {lot['qty']} shares bought at ${lot['buy_price']} each | P/L per share: [{color}]${diff}[/{color}]")
    input("Press Enter to return to main menu...")
    return

def portfolio():
    from rich.table import Table
    from rich.text import Text

    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)
        holdings = portfolio.get("holdings")
        if not holdings:
            console.print("[bold yellow]You have no holdings.[/bold yellow]")
            time.sleep(2)
            return

        total_value = 0.0
        sector_alloc = {}
        rows = []
        for ticker, lots in holdings.items():
            total_qty = sum(int(lot['qty']) for lot in lots)
            avg_price = round(sum(int(lot['qty']) * float(lot['price']) for lot in lots) / total_qty, 2) if total_qty > 0 else 0
            current_price = get_price(ticker)
            if current_price is None:
                current_price = 0.0
            current_price = float(round(current_price, 2))
            value = round(current_price * total_qty, 2)
            total_value += value
            sector = lots[0].get('sector', 'Unknown') if lots else 'Unknown'
            sector_alloc[sector] = sector_alloc.get(sector, 0) + value
            rows.append({
                "ticker": ticker,
                "price": current_price,
                "qty": total_qty,
                "value": value,
                "sector": sector
            })

        
        for row in rows:
            row["alloc"] = round(row["value"] / total_value * 100, 2) if total_value > 0 else 0

        # Prepare table
        table = Table(title="Portfolio", box=None, show_edge=True, header_style="bold white")
        table.add_column("Ticker", style="bold cyan", justify="left")
        table.add_column("Price", style="bold green", justify="right")
        table.add_column("Alloc%", style="bold magenta", justify="right")
        table.add_column("Value", style="bold blue", justify="right")

        for row in rows:
            table.add_row(
                row["ticker"],
                f"${row['price']}",
                f"{row['alloc']}%",
                f"${row['value']:,}"
            )
        
        console.print("\n")
        console.print(table)

        top_sector = max(sector_alloc, key=sector_alloc.get) if sector_alloc else "N/A"
        top_sector_pct = round(sector_alloc[top_sector] / total_value * 100, 2) if total_value > 0 and top_sector != "N/A" else 0

        console.print("\n")
        console.print(f"[bold white]Total Value:[/bold white] [bold green]${total_value:,.2f}[/bold green]")
        console.print(f"[bold white]Top Sector:[/bold white] [bold cyan]{top_sector}[/bold cyan] [white]({top_sector_pct}%)[/white]")

        input("Press Enter to return to main menu...")
        return