"""
cli.py
------
Main entry point for the Binance Futures Trading Bot.

Supports two modes:
  1. CLI mode  – pass all arguments on the command line.
  2. Interactive mode – launch a Rich-powered TUI menu (default when no
                        required arguments are supplied).

Usage examples
--------------
  # Interactive mode
  python -m trading_bot.cli

  # CLI – market buy
  python -m trading_bot.cli --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01

  # CLI – limit sell
  python -m trading_bot.cli --symbol ETHUSDT --side SELL --order-type LIMIT \
      --quantity 0.05 --price 3500.00
"""

import argparse
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt
from rich.table import Table
from rich.text import Text
from rich import box

from .logging_config import setup_logging
from .orders import place_order, OrderResult
from .validators import SUPPORTED_SYMBOLS, VALID_SIDES, VALID_ORDER_TYPES, ValidationError

# ── Setup ────────────────────────────────────────────────────────────────────
logger = setup_logging()
console = Console()

APP_TITLE = "Binance Futures Testnet Trading Bot"
BANNER = f"""[bold cyan]
  ██████╗ ██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
  ██╔══██╗██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
  ██████╔╝██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗
  ██╔══██╗██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝
  ██████╔╝██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗
  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
[/bold cyan]
[bold yellow]        Futures Testnet Trading Bot  🤖[/bold yellow]
"""


# ── Shared display helpers ───────────────────────────────────────────────────

def _print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> None:
    """Print a formatted order summary table before submission."""
    table = Table(title="Order Summary", box=box.ROUNDED, show_header=True)
    table.add_column("Field", style="bold cyan", width=18)
    table.add_column("Value", style="white")

    side_color = "green" if side.upper() == "BUY" else "red"
    table.add_row("Symbol", symbol.upper())
    table.add_row("Side", f"[{side_color}]{side.upper()}[/{side_color}]")
    table.add_row("Order Type", order_type.upper())
    table.add_row("Quantity", str(quantity))
    if order_type.upper() == "LIMIT":
        table.add_row("Price (USDT)", str(price))
    else:
        table.add_row("Price (USDT)", "[dim]Market price[/dim]")

    console.print(table)


def _print_order_result(result: OrderResult) -> None:
    """Print a formatted result table after order submission."""
    if result.success:
        panel_title = "[bold green]Order Placed Successfully ✓[/bold green]"
        panel_border = "green"

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Field", style="bold cyan", width=18)
        table.add_column("Value", style="white")

        table.add_row("Order ID", str(result.order_id))
        table.add_row("Status", f"[yellow]{result.status}[/yellow]")
        table.add_row("Executed Qty", str(result.executed_qty))
        avg = result.avg_price
        table.add_row("Avg Fill Price", f"${avg}" if avg and float(avg) > 0 else "[dim]Pending[/dim]")

        console.print(Panel(table, title=panel_title, border_style=panel_border))
        console.print("\n[bold green]✅  Order submitted to Binance Testnet.[/bold green]\n")
    else:
        console.print(
            Panel(
                f"[bold red]{result.error}[/bold red]",
                title="[bold red]Order Failed ✗[/bold red]",
                border_style="red",
            )
        )
        console.print("\n[bold red]❌  Order could not be placed.[/bold red]\n")


# ── Interactive (Rich TUI) mode ──────────────────────────────────────────────

def _prompt_symbol() -> str:
    """Prompt the user to choose a trading symbol."""
    console.print("\n[bold cyan]Available symbols:[/bold cyan]")
    symbols = sorted(SUPPORTED_SYMBOLS)
    for i, sym in enumerate(symbols, 1):
        console.print(f"  [{i:2}] {sym}")
    choice = Prompt.ask(
        "\nEnter symbol number or type symbol directly",
        default="BTCUSDT",
    )
    # Allow numeric shortcut
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(symbols):
            return symbols[idx]
    return choice.upper()


def _prompt_side() -> str:
    """Prompt the user to choose BUY or SELL."""
    return Prompt.ask(
        "Side",
        choices=["BUY", "SELL"],
        default="BUY",
    ).upper()


def _prompt_order_type() -> str:
    """Prompt the user to choose MARKET or LIMIT."""
    return Prompt.ask(
        "Order type",
        choices=["MARKET", "LIMIT"],
        default="MARKET",
    ).upper()


def _prompt_quantity() -> float:
    """Prompt the user to enter order quantity."""
    return FloatPrompt.ask("Quantity (e.g., 0.001)")


def _prompt_price() -> float:
    """Prompt the user to enter limit price."""
    return FloatPrompt.ask("Limit price (USDT)")


def run_interactive() -> None:
    """
    Launch the Rich-based interactive menu for placing orders.

    Users can place multiple orders sequentially without restarting.
    """
    console.print(BANNER)
    console.print(
        Panel(
            "[bold white]Welcome! Follow the prompts to place a futures order "
            "on Binance Testnet.[/bold white]\n"
            "[dim]All orders are placed on the TESTNET – no real funds are used.[/dim]",
            title=f"[bold yellow]{APP_TITLE}[/bold yellow]",
            border_style="cyan",
        )
    )

    while True:
        console.rule("[bold cyan]New Order[/bold cyan]")

        try:
            symbol = _prompt_symbol()
            side = _prompt_side()
            order_type = _prompt_order_type()
            quantity = _prompt_quantity()
            price: Optional[float] = None
            if order_type == "LIMIT":
                price = _prompt_price()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session cancelled by user.[/yellow]")
            sys.exit(0)

        _print_order_summary(symbol, side, order_type, quantity, price)

        confirm = Prompt.ask(
            "\nConfirm order?", choices=["yes", "no"], default="yes"
        )

        if confirm.lower() != "yes":
            console.print("[yellow]Order cancelled.[/yellow]")
        else:
            with console.status("[bold green]Submitting order…[/bold green]"):
                result = place_order(symbol, side, order_type, quantity, price)
            _print_order_result(result)

        again = Prompt.ask(
            "Place another order?", choices=["yes", "no"], default="no"
        )
        if again.lower() != "yes":
            console.print("\n[bold cyan]Goodbye! Happy trading 🚀[/bold cyan]\n")
            break


# ── CLI mode ─────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description=f"{APP_TITLE} – place orders on Binance Futures Testnet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m trading_bot.cli                          # interactive mode\n"
            "  python -m trading_bot.cli --symbol BTCUSDT --side BUY \\\n"
            "      --order-type MARKET --quantity 0.01\n"
            "  python -m trading_bot.cli --symbol ETHUSDT --side SELL \\\n"
            "      --order-type LIMIT --quantity 0.05 --price 3500\n"
        ),
    )
    parser.add_argument("--symbol", type=str, help="Trading pair symbol (e.g., BTCUSDT)")
    parser.add_argument("--side", type=str, choices=["BUY", "SELL"], help="Order side")
    parser.add_argument(
        "--order-type", type=str, choices=["MARKET", "LIMIT"],
        dest="order_type", help="Order type",
    )
    parser.add_argument("--quantity", type=float, help="Order quantity")
    parser.add_argument("--price", type=float, default=None, help="Limit price (LIMIT orders only)")
    return parser


def run_cli(args: argparse.Namespace) -> None:
    """
    Execute an order from parsed CLI arguments.

    Args:
        args: Parsed argparse Namespace with symbol, side, order_type, quantity, price.
    """
    _print_order_summary(args.symbol, args.side, args.order_type, args.quantity, args.price)

    with console.status("[bold green]Submitting order…[/bold green]"):
        result = place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )

    _print_order_result(result)
    sys.exit(0 if result.success else 1)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Parse CLI arguments and decide between interactive and CLI mode.

    Falls back to interactive mode when required arguments are missing.
    """
    parser = build_parser()
    args = parser.parse_args()

    # If any required CLI argument is missing, launch interactive mode
    required_provided = all([
        args.symbol,
        args.side,
        args.order_type,
        args.quantity is not None,
    ])

    if required_provided:
        run_cli(args)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
