
import time
import yfinance as yf
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class PriceFetcher:
    """
    Shared price fetcher with TTL cache. Use get_price(ticker).
    TTL default is 60 seconds but can be changed per instance.
    """
    def __init__(self, ttl=60):
        self.ttl = ttl
        self._cache = {}  # ticker -> {"price": float, "time": timestamp}
    
    def show_loader(self, ticker):
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Fetching {ticker}", total=None)
            time.sleep(1.2)

    def get_price(self, ticker):
        ticker = ticker.upper()
        now = time.time()
        cached = self._cache.get(ticker)
        if cached and now - cached["time"] < self.ttl:
            return cached["price"]

        try:
            self.show_loader(ticker)
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty or 'Close' not in hist or hist['Close'].empty:
                console.print(f"[bold red]Warning: No price data for {ticker} from yfinance.[/bold red]")
                return None
            price = float(round(hist['Close'].iloc[-1], 2))
            self._cache[ticker] = {"price": price, "time": now}
            return price
        except Exception as e:
            console.print(f"[bold red]Error fetching price for {ticker}: {e}[/bold red]")
            return None

    def invalidate(self, ticker=None):
        if ticker:
            self._cache.pop(ticker.upper(), None)
        else:
            self._cache.clear()
