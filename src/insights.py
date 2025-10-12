import json
from utils import get_price
from rich.console import Console

console = Console()

def generate_insights():
    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)
        holdings = portfolio.get("holdings", {})
    if not holdings:
        console.print("[bold yellow]No holdings in portfolio.[/bold yellow]")
        return

    total_value = 0.0
    sector_alloc = {}
    pe_sum = 0.0
    pe_weight = 0.0
    holding_values = {}

    for ticker, lots in holdings.items():
        qty = sum(lot['qty'] for lot in lots)
        price = get_price(ticker)
        if price is None or qty == 0:
            continue
        value = price * qty
        total_value += value
        holding_values[ticker] = value
        sector = lots[0].get('sector', 'Unknown') if lots else 'Unknown'
        sector_alloc[sector] = sector_alloc.get(sector, 0) + value

        pe = None
        for lot in lots:
            if 'pe' in lot and lot['pe'] is not None and lot['pe'] > 0:
                pe = lot['pe']
                break
        if pe is not None:
            pe_sum += pe * value
            pe_weight += value

    top_holdings = sorted(holding_values.items(), key=lambda x: x[1], reverse=True)
    avg_pe = round(pe_sum / pe_weight, 2) if pe_weight > 0 else 0

    sector_percent = {k: round(v / total_value * 100, 2) for k, v in sector_alloc.items() if total_value > 0}

    insights = []
    if sector_percent:
        max_sector = max(sector_percent, key=sector_percent.get)
        if sector_percent[max_sector] > 50:
            insights.append(f"Warning: High concentration in {max_sector} sector ({sector_percent[max_sector]}%). Consider diversifying.")

    if len(top_holdings) >= 2:
        top2_value = top_holdings[0][1] + top_holdings[1][1]
        if total_value > 0 and top2_value / total_value > 0.5:
            insights.append(f"Warning: Top 2 holdings ({top_holdings[0][0]}, {top_holdings[1][0]}) make up more than 50% of your portfolio.")

    sp500_pe = 22
    if avg_pe > sp500_pe:
        insights.append(f"Warning: Portfolio average P/E ({avg_pe}) is higher than S&P 500 ({sp500_pe}). Possible overvaluation.")

    if not insights:
        insights.append("Portfolio looks balanced.")

    console.print(f"[bold white]Total Portfolio Value:[/bold white] [bold green]${round(total_value,2)}[/bold green]")
    console.print(f"[bold white]Sector Allocation (%):[/bold white] [bold cyan]{sector_percent}[/bold cyan]")
    console.print(f"[bold white]Top Holdings:[/bold white] [bold magenta]{[h[0] for h in top_holdings[:3]]}[/bold magenta]")
    console.print(f"[bold white]Weighted Avg P/E:[/bold white] [bold green]{avg_pe}[/bold green]")
    console.print("\n[bold underline white]Insights:[/bold underline white]")
    for insight in insights:
        color = "yellow" if "Warning" in insight else "green"
        console.print(f"- [{color}]{insight}[/{color}]")
    input("\nPress Enter to return to main menu...")
    return