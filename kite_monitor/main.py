
import utils
import pprint
kite_chart_url = 'https://kite.zerodha.com/chart/web/ciq/{segment}/{option_name}/{instrument_token}?theme=dark'

def get_instrument_token(option_name, df):
    tokens = df[df['tradingsymbol']== option_name ]['instrument_token'].to_list()
    return tokens[0] if len(tokens) >= 1 else 0 
    pass
    

def coin_option_names(symbol_details_from_config, instrument_details):
    symbol_details = utils.merge_common_to_symbols(symbol_details_from_config)
    output_symbol_details = {}
    for symbol, details in symbol_details.items():
        ltp = utils.get_ltp_from_redis(details['underlying'])
        atm = utils.get_atm(details['diff'], ltp)
        for i in ["ce", "pe"]:
            val = atm + details[i]
            option_name = symbol+details['expiry']+str(val)+i.upper()
            instrument_token = get_instrument_token(option_name, instrument_details)
            output_symbol_details[option_name] = kite_chart_url.format(segment=details['segment'], 
                                                   option_name=option_name, 
                                                   instrument_token=instrument_token)
    return output_symbol_details
    

if __name__ == "__main__":
    configuration_details: list[dict] = utils.get_config_from_yaml() 
    credentials: dict = configuration_details.get('credentials')
    username: str = credentials.get('username')
    password: str = credentials.get('password')
    t_otp: str = credentials.get('time_based_otp_key')
    symbol_details_from_config: list[dict] = configuration_details.get('symbols')
    instrument_details = utils.get_instrument_details()
    symbol_details = coin_option_names(symbol_details_from_config, instrument_details)
    
    pprint.pprint(symbol_details)
    
    # otp: str = utils.get_otp(t_otp)
    # print(otp)
    # enc_token = kite_connect.get_enctoken(username, password, otp)
    # kite_app = kite_connect.KiteApp(enc_token)
    # print(kite_app.profile())


