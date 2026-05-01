# Submission Email Template

> Copy the block below, fill in the bracketed placeholders, and send.

---

**Subject:** Binance Futures Trading Bot – Take-Home Assignment Submission – [Your Name]

---

Hi [Hiring Manager's Name],

Please find my completed take-home assignment attached (or linked below).

**GitHub Repository:** [https://github.com/YOUR_USERNAME/binance-trading-bot]
*(Alternatively, the project ZIP is attached to this email.)*

---

### What was implemented

- **MARKET & LIMIT order placement** on Binance Futures Testnet (USDT-M perpetuals) via the official REST API (`https://testnet.binancefuture.com`)
- **BUY / SELL support** for both order types
- **CLI interface** (`argparse`) with `--symbol`, `--side`, `--order-type`, `--quantity`, and `--price` flags
- **Layered architecture** — five dedicated modules: `client.py`, `orders.py`, `validators.py`, `logging_config.py`, and `cli.py`
- **Input validation** — symbol whitelist, step-size / minimum-quantity checks, required-price enforcement for LIMIT orders
- **Retry logic** — exponential backoff (up to 3 attempts) for transient network errors and 429/5xx responses
- **Rotating log files** — all API requests, responses, and errors logged to `trading_bot/logs/trading_bot.log` (5 MB cap, 5 backups)
- **Credential management** via `python-dotenv` — no secrets in source code
- **Comprehensive exception handling** covering validation errors, API errors, and network failures with user-friendly messages and detailed log entries
- **Full documentation** — `README.md` with setup steps, testnet credential guide, CLI examples, and assumptions; `CHECKLIST.md` for pre-submission verification

### Bonus feature — Rich interactive UI

In addition to CLI mode, the bot ships with a **full-colour interactive console menu** powered by the [Rich](https://github.com/Textualize/rich) library. Launching `python -m trading_bot.cli` without arguments opens a guided TUI that displays symbol selection, a colour-coded order summary table, and a formatted result panel — no command-line flags required.

---

I have tested the bot against the Binance Futures Testnet and confirmed successful MARKET and LIMIT order placement. Sample log output is included in `trading_bot/logs/`.

I am happy to **walk through the code or demo it live** on a call at your convenience — just let me know a time that works.

Thank you for the opportunity!

Best regards,
[Your Full Name]
[Your Email]
[Your Phone / LinkedIn (optional)]
