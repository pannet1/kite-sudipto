import yaml
import pyotp


diff_of_symbols = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
}

def get_config_from_yaml() -> list[dict]:
    with open("../../../settings.yaml", "r") as yamlfile:
        config_data =  yaml.safe_load(yamlfile)
        print(config_data)
        return config_data

def get_otp(t_otp) -> str:
    return pyotp.TOTP(t_otp).now()

def get_atm(symbol: str, ltp, pe_or_ce="pe") -> int:
    symbol = symbol.upper()
    diff = diff_of_symbols.get(symbol)
    current_strike = ltp - (ltp % diff)
    next_higher_strike = current_strike - diff
    if pe_or_ce=="pe":
        next_higher_strike = current_strike + diff
    if ltp - current_strike < next_higher_strike - ltp:
        return int(current_strike)
    return int(next_higher_strike)

def coin_option_name_with_expiry(symbol, expiry, atm, pe_or_ce):
    # NIFTY23OCT17750CE
    return symbol.upper() + expiry.upper() + str(atm) + pe_or_ce.upper()