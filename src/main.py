from time import sleep
from os import name as os_name, system
import json
import utils
import analytics
import insights
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

PORTFOLIO_PATH = 'data/portfolio.json'
LAST_USER_PATH = 'data/last_user.json'
FIRST_RUN_PATH = 'data/first_run.json'

def load_portfolios():
    try:
        with open(PORTFOLIO_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_portfolios(portfolios):
    with open(PORTFOLIO_PATH, 'w') as f:
        json.dump(portfolios, f, indent=4)

def set_last_user(username):
    with open(LAST_USER_PATH, 'w') as f:
        json.dump({"last_user": username}, f, indent=4)

def get_last_user():
    try:
        with open(LAST_USER_PATH, 'r') as f:
            data = json.load(f)
            return data.get("last_user")
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def new_user():
    username = input("Enter a username for your account: ").strip()
    portfolios = load_portfolios()
    if username in portfolios:
        console.print(f"[yellow]User '{username}' already exists. Logging in...[/yellow]")
    else:
        portfolios[username] = {
            "name": username,
            "cash_balance": 10000,
            "holdings": {},
        }
        save_portfolios(portfolios)
        console.print(f"[green]New user '{username}' created![/green]")
    set_last_user(username)
    main_screen(username)

def login_user():
    portfolios = load_portfolios()
    username = input("Enter your username: ").strip()
    if username in portfolios:
        set_last_user(username)
        main_screen(username)
    else:
        console.print(f"[red]User '{username}' not found. Please create a new account.[/red]")
        sleep(2)
        new_user()

def reset_portfolio(username):
    portfolios = load_portfolios()
    portfolios[username] = {
        "name": username,
        "cash_balance": 10000,
        "holdings": {},
    }
    save_portfolios(portfolios)
    console.print(f"[bold yellow]Portfolio for '{username}' has been reset.[/bold yellow]")
    sleep(2)
    main_screen(username)

def main_screen(username):
    if os_name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

    portfolios = load_portfolios()
    portfolio = portfolios.get(username)
    if not portfolio:
        console.print(f"[red]Portfolio for user '{username}' not found.[/red]")
        sleep(2)
        login_user()
        return

    user_name = portfolio.get("name")
    value = portfolio.get("cash_balance")

    title = Text("TradeLab", style="bold magenta", justify="center")
    subtitle = Text("“Your personal investing terminal”", style="cyan", justify="center")
    welcome = Text(f"Welcome {user_name}", style="bold green", justify="center")
    console.print(Panel.fit(title + "\n" + subtitle + "\n" + welcome, box=box.DOUBLE, width=50), justify="center")

    table = Table(show_header=False, box=box.SIMPLE, width=100, padding=(1,1))
    table.add_row(
        Text("User:", style="bold red"),
        Text(user_name, style="bold"),
        Text("Portfolio Value:", style="bold red"),
        Text(f"${analytics.portfolio_value(username)}", style="bold green"),
    )
    table.add_row(
        Text("Cash Balance:", style="bold red"),
        Text(f"${value:,}", style="bold"),
        Text("Daily P/L:", style="bold red"),
        Text(f"{analytics.portfolio_pnl(username)}%", style="bold green"),
    )
    console.print(table, justify="center")
    console.rule("[bold blue]Commands[/bold blue]", style="blue",)

    commands = Text("[portfolio] [buy] [sell] [risk] [value] [insights] [reset] [logout] [exit] [help]")
    console.print(commands, style="yellow", justify="center", height=5)
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
                else:
                    commands[base_cmd](username)
                    main_screen(username)
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
        else:
            console.print("[yellow]Unknown command. Type 'help' for available options.[/yellow]")
            sleep(1)
            main_screen(username)
        

if __name__ == "__main__":
    if os_name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

    try:
        with open(FIRST_RUN_PATH, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"first_run": True}

    if data.get("first_run", True):
        console.print("[bold blue]Welcome to TradeLab![/bold blue]")
        console.print("[bold white]This seems to be your first time running the application.[/bold white]")
        console.print("[bold yellow]Please follow the setup instructions to configure your profile.[/bold yellow]")
        data["first_run"] = False
        with open(FIRST_RUN_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        sleep(3)
        new_user()
    else:
        last_user = get_last_user()
        if last_user and last_user in load_portfolios():
            console.print(f"[bold green]Auto-loading last user: {last_user}[/bold green]")
            sleep(1)
            main_screen(last_user)
        else:
            login_user()