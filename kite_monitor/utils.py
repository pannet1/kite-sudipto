import yaml
import pyotp
from io import BytesIO
import requests 
import pandas as pd

def get_ltp_from_redis(instrument_or_symbol):
    return 16000

def get_atm(diff: str, ltp) -> int:
    current_strike = ltp - (ltp % diff)
    next_higher_strike = current_strike + diff
    if ltp - current_strike < next_higher_strike - ltp:
        return int(current_strike)
    return int(next_higher_strike)

def get_instrument_details() -> pd.DataFrame:
    url = 'https://api.kite.trade/instruments'
    r = requests.get(url, allow_redirects=True)
    # open('instruments.csv', 'wb').write(r.content)
    return pd.read_csv(BytesIO(r.content))

def merge_common_to_symbols(input_with_common: list[dict]):
    output_without_common: dict = {}
    common_items = {}
    
    for item in input_with_common:
        if "common" in item:
            common_items.update(item["common"])
            break
    for item in input_with_common:
        if "common" not in item:
            for k, v in item.items():
                v.update(common_items)
            output_without_common.update(item)

    return output_without_common

def get_config_from_yaml() -> list[dict]:
    with open("../../../settings.yaml", "r") as yamlfile:
        config_data =  yaml.safe_load(yamlfile)
        print(config_data)
        return config_data

def get_otp(t_otp) -> str:
    return pyotp.TOTP(t_otp).now()
