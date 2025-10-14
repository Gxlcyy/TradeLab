import yfinance as yf
import json
import numpy as np
import json
import numpy as np
from rich.console import Console

console = Console()

def get_price(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='1d')
    if hist.empty or 'Close' not in hist or hist['Close'].empty:
        console.print(f"[bold red]Error: No price data found for {ticker}.[/bold red]")
        return None
    price = hist['Close'].iloc[0]
    return float(round(price, 2))

def portfolio_value(username):
    total = 0.0
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)

    holdings = portfolio[username].get("holdings", {})
    for ticker, lots in holdings.items():
        total_qty = sum(int(lot.get('qty', 0)) for lot in lots)
        price = get_price(ticker)
        if price is None or total_qty == 0:
            continue
        total += price * total_qty
    return round(total, 2)


def portfolio_pnl(username):
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)

    holdings = portfolio[username].get("holdings", {})
    if not holdings:
        return 0.0

    total_pnl = 0.0
    for ticker, lots in holdings.items():
        total_qty = sum(int(lot.get('qty', 0)) for lot in lots)
        if total_qty == 0:
            continue
        avg_buy_price = sum(int(lot['qty']) * float(lot['price']) for lot in lots) / total_qty
        current_price = get_price(ticker)
        if current_price is None:
            continue
        total_pnl += (current_price - avg_buy_price) * total_qty
    return round(total_pnl, 2)


def portfolio_valuation(username):
    sp500_pe = 22
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)

    holdings = portfolio[username].get("holdings", {})
    total_value = 0.0
    pe_sum = 0.0

    for ticker, lots in holdings.items():
        qty = sum(int(lot.get('qty', 0)) for lot in lots)
        price = get_price(ticker)
        if price is None or qty == 0:
            continue
        value = price * qty
        total_value += value
        try:
            stock = yf.Ticker(ticker)
            pe = stock.info.get('trailingPE')
            if pe is not None and pe > 0:
                pe_sum += pe * value
        except Exception:
            continue

    avg_pe = round(pe_sum / total_value, 2) if total_value > 0 else 0
    console.print(f"[bold white]Weighted Avg Portfolio P/E:[/bold white] [bold green]{avg_pe}[/bold green]")
    console.print(f"[bold white]S&P 500 P/E:[/bold white] [bold cyan]{sp500_pe}[/bold cyan]")

    if avg_pe > 0:
        pe_color = "green" if avg_pe < sp500_pe else "red"
        console.print(f"[bold white]Portfolio P/E is[/bold white] [{pe_color}]{'lower' if avg_pe < sp500_pe else 'higher'}[/{pe_color}] [bold white]than S&P 500.[/bold white]")
        dcf_upside = round((sp500_pe / avg_pe - 1) * 100, 2)
        console.print(f"[bold white]Simple DCF Upside vs S&P 500:[/bold white] [bold green]{dcf_upside}%[/bold green]")
    else:
        console.print("[bold red]Insufficient data for DCF calculation.[/bold red]")

    input("Press Enter to return to main screen...")
    return

def portfolio_risk_metrics(username):
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)

    holdings = portfolio[username].get("holdings", {})
    total_value = 0.0
    sector_alloc = {}
    betas = []
    weights = []
    returns = []

    for ticker, lots in holdings.items():
        qty = sum(int(lot.get('qty', 0)) for lot in lots)
        price = get_price(ticker)
        if price is None or qty == 0:
            continue
        value = price * qty
        total_value += value

        sector = lots[0].get('sector', 'Unknown') if lots else 'Unknown'
        sector_alloc[sector] = sector_alloc.get(sector, 0) + value

        beta = float(lots.get('beta', 1)) if 'beta' in lots[0] else 1
        betas.append(beta)
        weights.append(value)

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1y')
            if not hist.empty and 'Close' in hist:
                pct_returns = hist['Close'].pct_change().dropna()
                returns.extend(pct_returns.tolist())
        except Exception:
            continue

    weighted_beta = round(np.average(betas, weights=weights), 2) if betas and weights else 1.0
    volatility = round(np.std(returns), 4) if returns else 0.0
    sector_percent = [v / total_value for v in sector_alloc.values()] if total_value > 0 else []
    hhi = sum([p**2 for p in sector_percent])
    diversification_score = round((1 - hhi) * 100, 2) if sector_percent else 0.0

    console.print(f"[bold white]Portfolio Beta (weighted):[/bold white] [bold blue]{weighted_beta}[/bold blue]")
    console.print(f"[bold white]Portfolio Volatility (1y std):[/bold white] [bold magenta]{volatility}[/bold magenta]")
    console.print(f"[bold white]Diversification Score:[/bold white] [bold green]{diversification_score}[/bold green] [white](higher is better)[/white]")
    console.print(f"[bold white]Sector Allocation (%):[/bold white] [bold cyan]{ {k: round(v / total_value * 100, 2) for k, v in sector_alloc.items() if total_value > 0} }[/bold cyan]")

    input("Press Enter to return to main screen...")
    return