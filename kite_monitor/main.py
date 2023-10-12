
import kite_connect
import utils

def get_atm(diff: str, ltp) -> int:
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
        atm = get_atm(details['diff'], ltp)
        for i in ["ce", "pe"]:
            val = atm + details[i]
            option_names.append(symbol+details['expiry']+str(val)+i.upper())
    return option_names
    

if __name__ == "__main__":
    configuration_details: list[dict] = utils.get_config_from_yaml() 
    credentials: dict = configuration_details.get('credentials')
    username: str = credentials.get('username')
    password: str = credentials.get('password')
    t_otp: str = credentials.get('time_based_otp_key')
    otp: str = utils.get_otp(t_otp)
    symbol_details_from_config: list[dict] = configuration_details.get('symbols')
    print(coin_option_names(symbol_details_from_config))
    # enc_token = kite_connect.get_enctoken(username, password, otp)
    # kite_app = kite_connect.KiteApp(enc_token)
    # print(kite_app.profile())


