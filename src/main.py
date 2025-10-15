
from time import sleep
from os import name as os_name, system
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from pyfiglet import Figlet
from rich.align import Align

import storage
from price_fetcher import PriceFetcher
import utils
import analytics
import insights

console = Console()
f = Figlet(font='standard')

PORTFOLIO_PATH = 'data/portfolio.json'
LAST_USER_PATH = 'data/last_user.json'
FIRST_RUN_PATH = 'data/first_run.json'

# initialize shared services
_store = storage.PortfolioStorage()
_price_fetcher = PriceFetcher(ttl=60)

# initialize modules to use central storage and price fetcher
utils.init(_store, _price_fetcher)
analytics.init(_store, _price_fetcher)
insights.init(_store, _price_fetcher)


def new_user():
    username = input("Enter a username for your account: ").strip()
    if not username:
        console.print("[red]Username cannot be empty.[/red]")
        return
    portfolios = _store.load_portfolios()
    if username in portfolios:
        console.print(f"[yellow]User '{username}' already exists. Logging in...[/yellow]")
    else:
        _store.create_user_if_missing(username)
        console.print(f"[green]New user '{username}' created![/green]")
    _store.set_last_user(username)
    main_screen(username)

def login_user():
    portfolios = _store.load_portfolios()
    username = input("Enter your username: ").strip()
    if username in portfolios:
        _store.set_last_user(username)
        main_screen(username)
    else:
        console.print(f"[red]User '{username}' not found. Please create a new account.[/red]")
        sleep(2)
        new_user()

def reset_portfolio(username):
    _store.reset_user(username)
    console.print(f"[bold yellow]Portfolio for '{username}' has been reset.[/bold yellow]")
    sleep(2)
    main_screen(username)

def main_screen(username):
    system('cls' if os_name == 'nt' else 'clear')

    portfolios = _store.load_portfolios()
    portfolio = portfolios.get(username)
    if not portfolio:
        console.print(f"[red]Portfolio for user '{username}' not found.[/red]")
        sleep(2)
        login_user()
        return

    user_name = portfolio.get("name")
    value = portfolio.get("cash_balance")

    banner = f.renderText('TradeLab')


    banner = Text(banner, style="cyan")
    subtitle = Text("“Your personal investing terminal”", style="cyan", justify="center")
    welcome = Text(f"Welcome {user_name}", style="bold green", justify="center")
    console.print(Align(banner, align="center"))
    console.print(subtitle + "\n" + welcome, justify="center")

    table = Table(show_header=False, box=box.SIMPLE, width=100, padding=(1,1))
    table.add_row(
        Text("User:", style="bold red"),
        Text(user_name, style="bold cyan"),
        Text("Portfolio Value:", style="bold red"),
        Text(f"${analytics.portfolio_value(username)}", style="bold green"),
    )

    portfolio_pnl = analytics.portfolio_pnl(username)
    pnl_color = "green" if portfolio_pnl >= 0 else "red"

    table.add_row(
        Text("Cash Balance:", style="bold red"),
        Text(f"${value:,}", style="bold"),
        Text("Daily P/L:", style="bold red"),
        Text(f"{portfolio_pnl}%", style=f"bold {pnl_color}"),
    )
    console.print(table, justify="center")
    console.rule("[bold blue]Commands[/bold blue]", style="blue",)

    commands_text = Text("[portfolio] [buy] [sell] [risk] [value] [insights] [reset] [logout] [exit] [help]")
    console.print(commands_text, style="yellow", justify="center", height=5)
    console.rule(style="grey50")

    commands = {
        "portfolio": utils.portfolio,
        "risk": analytics.portfolio_risk_metrics,
        "value": analytics.portfolio_valuation,
        "insights": insights.generate_insights,
        "buy": utils.buy,
        "sell": utils.sell,
        "reset": reset_portfolio,
        "logout": login_user,
        "help": None,
    }

    while True:
        cmd = console.input("[bold cyan]> [/bold cyan]").strip().lower()

        if cmd == "exit":
            console.print("[bold red]Exiting...[/bold red]")
            break

        if not cmd:
            continue

        base_cmd = cmd.split()[0]

        if base_cmd in commands:
            try:
                if base_cmd == "logout":
                    commands[base_cmd]()
                    break
                elif base_cmd == "reset":
                    commands[base_cmd](username)
                    break
                elif base_cmd == "help":
                    console.print("""
[bold cyan]Available Commands:[/bold cyan]
[white]Portfolio[/white] - View your current holdings
[white]Buy[/white] - Buy a stock
[white]Sell[/white] - Sell a stock
[white]Risk[/white] - Analyze portfolio risk metrics
[white]Value[/white] - View current portfolio valuation
[white]Insights[/white] - Get investment insights
[white]Reset[/white] - Reset your portfolio
[white]Logout[/white] - Log out of your account
[white]Exit[/white] - Close the program
                    """)
                    input("Press Enter to return to main screen...")
                    main_screen(username)
                    return
                else:
                    # preserve original behavior: pass username to functions that expect it
                    commands[base_cmd](username)
                    main_screen(username)
                    return
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
        else:
            console.print("[yellow]Unknown command. Type 'help' for available options.[/yellow]")
            sleep(1)
            main_screen(username)
            return

if __name__ == "__main__":
    system('cls' if os_name == 'nt' else 'clear')

    if _store.is_first_run():
        console.print("[bold blue]Welcome to TradeLab![/bold blue]")
        console.print("[bold white]This seems to be your first time running the application.[/bold white]")
        console.print("[bold yellow]Please follow the setup instructions to configure your profile.[/bold yellow]")
        _store.set_first_run_false()
        sleep(3)
        new_user()
    else:
        last_user = _store.get_last_user()
        if last_user and last_user in _store.load_portfolios():
            console.print(f"[bold green]Auto-loading last user: {last_user}[/bold green]")
            sleep(1)
            main_screen(last_user)
        else:
            login_user()
