import yaml
import pyotp


def get_ltp_from_redis(instrument_or_symbol):
    pass

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
