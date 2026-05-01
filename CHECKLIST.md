# Pre-Submission Verification Checklist

Work through each section top-to-bottom. Check off every item before submitting.

---

## 1. Environment Setup

### 1.1 Python version
```bash
python3 --version
```
**Expected:** `Python 3.10.x` or higher (3.10+ required for `set[str]` type hints)

---

### 1.2 Virtual environment created and activated
```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat     # Windows cmd
# .venv\Scripts\Activate.ps1     # Windows PowerShell
```
**Expected:** Shell prompt now shows `(.venv)` prefix.

---

### 1.3 Dependencies installed
```bash
pip install -r requirements.txt
```
**Expected:** No errors. Confirm with:
```bash
pip show requests python-dotenv rich
```
Expected output (versions may differ):
```
Name: requests
Version: 2.31.x
...
Name: python-dotenv
Version: 1.0.x
...
Name: rich
Version: 13.x.x
```

---

### 1.4 Project structure intact
```bash
find trading_bot -type f | sort
```
**Expected output:**
```
trading_bot/__init__.py
trading_bot/cli.py
trading_bot/client.py
trading_bot/logging_config.py
trading_bot/logs/limit_order.log
trading_bot/logs/market_order.log
trading_bot/orders.py
trading_bot/validators.py
```

---

## 2. API Credential Validation

### 2.1 .env file exists
```bash
ls -la .env
```
**Expected:** File listed (not a symlink to `.env.example`).

### 2.2 Credentials are non-empty
```bash
python3 -c "
from dotenv import load_dotenv; import os; load_dotenv()
key = os.getenv('BINANCE_API_KEY', '')
secret = os.getenv('BINANCE_API_SECRET', '')
print('API_KEY set:   ', bool(key) and key != 'your_testnet_api_key_here')
print('API_SECRET set:', bool(secret) and secret != 'your_testnet_api_secret_here')
"
```
**Expected:**
```
API_KEY set:    True
API_SECRET set: True
```

### 2.3 Testnet connectivity
```bash
python3 -c "
import requests
r = requests.get('https://testnet.binancefuture.com/fapi/v1/ping', timeout=5)
print('Testnet reachable:', r.status_code == 200)
"
```
**Expected:** `Testnet reachable: True`

---

## 3. Functional Tests

### Test A — MARKET BUY (CLI mode)

**Command:**
```bash
python3 -m trading_bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.01
```

**Expected console output (key elements):**
```
┌─────────────────── Order Summary ───────────────────┐
│ Field            │ Value                            │
│ Symbol           │ BTCUSDT                          │
│ Side             │ BUY   (green)                    │
│ Order Type       │ MARKET                           │
│ Quantity         │ 0.01                             │
│ Price (USDT)     │ Market price                     │
└──────────────────────────────────────────────────────┘

┌──── Order Placed Successfully ✓ ────┐
│ Order ID      │ <integer>           │
│ Status        │ FILLED              │
│ Executed Qty  │ 0.01                │
│ Avg Fill Price│ $<price>            │
└─────────────────────────────────────┘

✅  Order submitted to Binance Testnet.
```

**Exit code:**
```bash
echo $?   # must print 0
```

---

### Test B — LIMIT SELL (CLI mode)

**Command:**
```bash
python3 -m trading_bot.cli \
  --symbol ETHUSDT \
  --side SELL \
  --order-type LIMIT \
  --quantity 0.05 \
  --price 9999.00
```
> Using a very high price ensures the order stays open (status: NEW) without filling immediately.

**Expected console output (key elements):**
```
┌─────────────────── Order Summary ───────────────────┐
│ Symbol           │ ETHUSDT                          │
│ Side             │ SELL  (red)                      │
│ Order Type       │ LIMIT                            │
│ Quantity         │ 0.05                             │
│ Price (USDT)     │ 9999.0                           │
└──────────────────────────────────────────────────────┘

┌──── Order Placed Successfully ✓ ────┐
│ Order ID      │ <integer>           │
│ Status        │ NEW                 │
│ Executed Qty  │ 0                   │
│ Avg Fill Price│ Pending             │
└─────────────────────────────────────┘

✅  Order submitted to Binance Testnet.
```

**Exit code:**
```bash
echo $?   # must print 0
```

---

### Test C — Interactive (Rich TUI) mode

**Command:**
```bash
python3 -m trading_bot.cli
```

**Expected:** ASCII banner displays, symbol list appears, prompts guide through order placement. No crash on launch.

---

### Test D — Validation error: missing LIMIT price

**Command:**
```bash
python3 -m trading_bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --order-type LIMIT \
  --quantity 0.01
```

**Expected:**
```
┌────────────── Order Failed ✗ ──────────────┐
│ Price is required for LIMIT orders.        │
└────────────────────────────────────────────┘
❌  Order could not be placed.
```

**Exit code:**
```bash
echo $?   # must print 1
```

---

### Test E — Validation error: unsupported symbol

**Command:**
```bash
python3 -m trading_bot.cli \
  --symbol FAKECOIN \
  --side BUY \
  --order-type MARKET \
  --quantity 0.01
```

**Expected:**
```
┌────────────── Order Failed ✗ ──────────────────────────────────────────┐
│ Unsupported symbol 'FAKECOIN'. Supported symbols: ADAUSDT, BNBUSDT ... │
└────────────────────────────────────────────────────────────────────────┘
❌  Order could not be placed.
```

**Exit code:**
```bash
echo $?   # must print 1
```

---

### Test F — Validation error: quantity below minimum

**Command:**
```bash
python3 -m trading_bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.0001
```

**Expected:**
```
┌────────────── Order Failed ✗ ────────────────────────────────────────────────┐
│ Quantity 0.0001 is below minimum allowed quantity 0.001                      │
└──────────────────────────────────────────────────────────────────────────────┘
❌  Order could not be placed.
```

---

## 4. Log File Verification

After running Tests A and B above:

```bash
tail -30 trading_bot/logs/trading_bot.log
```

**Expected:** Lines showing:
- `[INFO] trading_bot.client - Sending POST /fapi/v1/order`
- `[DEBUG] trading_bot.client - Response attempt=1 status=200`
- `[INFO] trading_bot.client - API call succeeded. orderId=<id>`

---

## 5. Help Output

```bash
python3 -m trading_bot.cli --help
```

**Expected:** Full argparse help block with all arguments listed (`--symbol`, `--side`, `--order-type`, `--quantity`, `--price`) and usage examples at the bottom.

---

## 6. Submission Package

```bash
ls -lh trading_bot_submission.zip
```

**Expected:** File exists, size is reasonable (< 1 MB).

Verify zip contents:
```bash
unzip -l trading_bot_submission.zip
```

**Expected:** All source files present, **no** `.env`, no `__pycache__`.

---

## Checklist Summary

- [ ] Python 3.10+ confirmed
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` — no errors
- [ ] `.env` created with real testnet credentials
- [ ] Testnet ping returns 200
- [ ] Test A: MARKET BUY — status FILLED, exit code 0
- [ ] Test B: LIMIT SELL — status NEW, exit code 0
- [ ] Test C: Interactive TUI launches without crash
- [ ] Test D: Missing price error displays correctly, exit code 1
- [ ] Test E: Invalid symbol error displays correctly, exit code 1
- [ ] Test F: Below-minimum quantity error displays correctly
- [ ] Log file contains API request/response entries
- [ ] `--help` shows all arguments
- [ ] ZIP file created, verified, no secrets inside
