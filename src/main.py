from time import sleep
from os import name, system
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

def new_user():
    name = input("Enter a username for your account: ")
    new_user_dict = {
        "name": f"{name}",
        "cash_balance": 10000,
        "holdings": {},
    }
    with open('data/portfolio.json', 'w') as f:
        json.dump(new_user_dict, f, indent=4)
    
    main_screen()

def main_screen():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

    with open('data/portfolio.json', 'r') as f:
        portfolio = json.load(f)
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
        Text(f"${analytics.portfolio_value()}", style="bold green"),
    )
    table.add_row(
        Text("Cash Balance:", style="bold red"),
        Text(f"${value:,}", style="bold"),
        Text("Daily P/L:", style="bold red"),
        Text(f"{analytics.portfolio_pnl()}%", style="bold green"),
    )
    console.print(table, justify="center")
    console.rule("[bold blue]Commands[/bold blue]", style="blue",)

    commands = Text("[portfolio] [buy] [sell] [risk] [value] [insights] [exit]")
    console.print(commands, style="yellow", justify="center", height=5)
    console.rule(style="grey50")

    while True:
        cmd = console.input("[bold cyan]> [/bold cyan]").strip().lower()
        if cmd == "portfolio":
            try:
                utils.portfolio()
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
            main_screen()
        elif cmd == "risk":
            try:
                analytics.portfolio_risk_metrics()
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
            main_screen()
        elif cmd == "value":
            try:
                analytics.portfolio_valuation()
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
            main_screen()
        elif cmd == "insights":
            try:
                insights.generate_insights()
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
            main_screen()
        elif cmd.startswith("buy"):
            try:
                utils.buy()
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
            main_screen()
        elif cmd.startswith("sell"):
            try:
                utils.sell()
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            sleep(1)
            main_screen()
        elif cmd == "exit":
            break
        else:
            console.print("[yellow]Unknown command. Returning to main screen...[/yellow]")
            sleep(1)
            main_screen()

if __name__ == "__main__":
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

    with open('data/first_run.json', 'r') as f:
        data = json.load(f)
    
    if data.get("first_run", True):
        console.print("[bold blue]Welcome to TradeLab![/bold blue]")
        console.print("[bold white]This seems to be your first time running the application.[/bold white]")
        console.print("[bold yellow]Please follow the setup instructions to configure your profile.[/bold yellow]")
        data["first_run"] = False
        with open('src/first_run.json', 'w') as f:
            json.dump(data, f, indent=4)
        sleep(3)
        new_user()
    else:
        main_screen()