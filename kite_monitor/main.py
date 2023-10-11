
import kite_connect
import utils

def get_atm(diff: str, ltp, call_or_put_val) -> int:
    symbol = symbol.upper()
    current_strike = ltp - (ltp % diff)
    next_higher_strike = current_strike + diff
    if ltp - current_strike < next_higher_strike - ltp:
        return int(current_strike)
    return int(next_higher_strike)

def coin_option_names(symbol_details_from_config):
    option_names = []
    symbol_details = utils.merge_common_to_symbols(symbol_details_from_config)
    for symbol, details in symbol_details.items():
        ltp = utils.get_ltp_from_redis(details['underlying'])
        for i in ["ce", "pe"]:
            atm = get_atm(details['diff'], ltp, details[i])
            option_names.append(symbol+details['expiry']+str(atm)+details[i]+i.upper())
    return option_names
    

if __name__ == "__main__":
    configuration_details: list[dict] = utils.get_config_from_yaml() 
    credentials: dict = configuration_details.get('credentials')
    username: str = credentials.get('username')
    password: str = credentials.get('password')
    t_otp: str = credentials.get('time_based_otp_key')
    otp: str = utils.get_otp(t_otp)
    print(otp)
    symbol_details_from_config: list[dict] = configuration_details.get('symbols')
    coin_option_names(symbol_details_from_config)
    # enc_token = kite_connect.get_enctoken(username, password, otp)
    # kite_app = kite_connect.KiteApp(enc_token)
    # print(kite_app.profile())


