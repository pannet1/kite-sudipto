dct_symbols = {
    "NIFTY": {
        "diff": 50
    },
    "BANKNIFTY": {
        "diff": 100
    }
}

ltps = {"NIFTY": 19251.50, "BANKNIFTY": 43399.95}  # Example LTP

# Update dct_symbols with ltps values and calculate ATM strike
for symbol, ltp in ltps.items():
    if symbol in dct_symbols:
        dct_symbols[symbol]["ltp"] = ltp
        diff = dct_symbols[symbol]['diff']
        current_strike = ltp - (ltp % diff)
        next_higher_strike = current_strike + diff
        if ltp - current_strike < next_higher_strike - ltp:
            dct_symbols[symbol]["atm_strike"] = int(current_strike)
        else:
            dct_symbols[symbol]["atm_strike"] = int(next_higher_strike)

print(dct_symbols)
