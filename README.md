# Binance Futures Testnet Trading Bot

A command-line and interactive trading bot for placing **MARKET** and **LIMIT** orders on the
[Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M perpetuals).

---

## Features

- Place **MARKET** and **LIMIT** futures orders via CLI or interactive Rich TUI
- Full input validation (symbol, side, quantity, step-size, price)
- Retry logic with exponential backoff for transient network errors
- Rotating log file (5 MB max, 5 backups)
- Beautiful console output via the [Rich](https://github.com/Textualize/rich) library
- API credentials loaded from `.env` (never hard-coded)

---

## Project Structure

```
trading_bot/
├── __init__.py          # Package metadata
├── cli.py               # Entry point – CLI + interactive mode
├── client.py            # Binance Futures REST API wrapper
├── orders.py            # High-level order placement logic
├── validators.py        # Input validation helpers
├── logging_config.py    # Rotating log file + console handler setup
└── logs/
    ├── market_order.log # Sample MARKET order log
    └── limit_order.log  # Sample LIMIT order log
requirements.txt
.env.example
README.md
```

---

## Setup

### 1. Clone / download the project

```bash
git clone <repo-url>
cd <project-folder>
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (cmd)
python -m venv .venv
.venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your testnet credentials:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

---

## How to get Binance Testnet API Credentials

1. Visit **[https://testnet.binancefuture.com](https://testnet.binancefuture.com)**
2. Click **Log In** and sign in with your GitHub account (no separate registration required)
3. After login, go to **API Management** in the top navigation
4. Click **Create API Key** and copy the **API Key** and **Secret Key**
5. Paste them into your `.env` file as shown above

> **Note:** Testnet credentials are separate from live Binance credentials. Testnet funds are
> virtual and have no real value.

---

## Running the Bot

### Interactive mode (Rich TUI)

Launch without arguments to start the guided interactive menu:

```bash
python -m trading_bot.cli
```

You will be prompted to select a symbol, side, order type, quantity, and (for LIMIT) price.

### CLI mode

Pass all required arguments directly:

#### MARKET Buy

```bash
python -m trading_bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.01
```

#### LIMIT Sell

```bash
python -m trading_bot.cli \
  --symbol ETHUSDT \
  --side SELL \
  --order-type LIMIT \
  --quantity 0.05 \
  --price 3500.00
```

#### Show help

```bash
python -m trading_bot.cli --help
```

---

## Supported Symbols

| Symbol    | Symbol    | Symbol    |
|-----------|-----------|-----------|
| BTCUSDT   | ETHUSDT   | BNBUSDT   |
| XRPUSDT   | SOLUSDT   | ADAUSDT   |
| DOGEUSDT  | MATICUSDT | LTCUSDT   |
| DOTUSDT   |           |           |

---

## Log Files

Logs are written to `trading_bot/logs/trading_bot.log`.

- Each file is capped at **5 MB** with up to **5 rotating backups**
- All API requests, responses, and errors are logged at DEBUG level
- The console only shows WARNING and above to keep the UI clean

---

## Assumptions

1. **Testnet only** – The bot is hard-coded to `https://testnet.binancefuture.com`. It will
   not work with live Binance credentials without code changes.

2. **BTCUSDT quantity constraints** are used as the default validation baseline for all symbols:
   - `min_qty = 0.001`
   - `step_size = 0.001`
   - `min_notional = 5.0 USD`

   In production, these values should be fetched dynamically via `GET /fapi/v1/exchangeInfo`.

3. **LIMIT orders** use `timeInForce = GTC` (Good Till Cancelled) by default.

4. **No position management** – The bot only places orders. It does not track open positions,
   PnL, or account balance.

5. **Synchronous requests** – All API calls are synchronous (`requests` library). Async
   execution (e.g. `aiohttp`) was intentionally excluded for simplicity.

6. **No leverage configuration** – Leverage must be set separately in the Testnet UI or via
   the `POST /fapi/v1/leverage` endpoint before trading.

---

## Dependencies

| Package        | Version  | Purpose                            |
|----------------|----------|------------------------------------|
| requests       | ≥ 2.31   | HTTP calls to Binance REST API     |
| python-dotenv  | ≥ 1.0    | Load credentials from `.env`       |
| rich           | ≥ 13.7   | Beautiful interactive console UI   |

---

## License

MIT
