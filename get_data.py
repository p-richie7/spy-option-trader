# get_data_fixed.py
from ib_insync import IB, Stock, Option
from datetime import date

HOST, PORT, CLIENT_ID = "127.0.0.1", 7497, 1   # TWS Paper defaults

ib = IB()
ib.connect(HOST, PORT, clientId=CLIENT_ID)

# 1) Use delayed market data if you don't have live subscriptions
# 1 = live, 2 = frozen, 3 = delayed, 4 = delayed-frozen
ib.reqMarketDataType(3)

# 2) Define and qualify the SPY stock to get a valid conId
spy = Stock("SPY", "SMART", "USD", primaryExchange="ARCA")
ib.qualifyContracts(spy)
print("SPY conId:", spy.conId)

# 3) Get a (delayed) market price
q = ib.reqMktData(spy, "", False, False)
ib.sleep(2.0)  # give TWS time to populate fields
print("SPY market price (delayed ok):", q.marketPrice())

# 4) Fetch option security definition using the *real* underlying conId
params = ib.reqSecDefOptParams(spy.symbol, "", "STK", spy.conId)
# pick the SMART/OPRA entry (varies by account/region)
p = next((x for x in params if x.exchange in ("SMART","OPRA")), params[0])

expiries = sorted(p.expirations)
strikes  = sorted(p.strikes)

print("First few expiries:", expiries[:5])
expiry = expiries[0]

# 5) Request a few put quotes around ATM (delayed is fine)
# choose ~10 strikes around the middle of the strikes list
mid = len(strikes)//2
band = strikes[max(0, mid-5): mid+5]

contracts = [Option("SPY", expiry, k, "P", "SMART") for k in band]
ib.qualifyContracts(*contracts)

ticks = [ib.reqMktData(c, "", False, False) for c in contracts]
ib.sleep(3.0)

for c, t in zip(contracts, ticks):
    bid = t.bid if t.bid is not None else float("nan")
    ask = t.ask if t.ask is not None else float("nan")
    print(f"{expiry}  {c.strike:>7.2f}  bid:{bid!s:>6}  ask:{ask!s:>6}")

ib.disconnect()
