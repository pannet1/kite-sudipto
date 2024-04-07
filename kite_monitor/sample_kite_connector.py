from playwright.sync_api import sync_playwright
import kite_connect
import utils
import sys

configuration_details: list[dict] = utils.get_config_from_yaml()
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
context = browser.new_context()


def login_to_kite_web_using_playwright(credentials_from_config, context) -> tuple:
    username = credentials_from_config.get("username")
    password = credentials_from_config.get("password")
    t_otp = credentials_from_config.get("time_based_otp_key")
    page = context.new_page()
    page.goto("https://kite.zerodha.com/?next=%2Fdashboard")
    page.get_by_label("User ID").click()
    page.get_by_label("User ID").fill(username)
    page.get_by_placeholder("Password").click()
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()
    otp = utils.get_otp(t_otp)
    page.get_by_placeholder("••••••").fill(otp)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="I understand").click()
    enc_token = [
        cookie["value"] for cookie in context.cookies() if cookie["name"] == "enctoken"
    ]
    enc_token = next(iter(enc_token), None)
    return enc_token


# Other operations
# enc_token = login_to_kite_web_using_playwright(
#     configuration_details["credentials"], context
# )
# if not enc_token:
#     print("enc_token is missing. Please check")
#     sys.exit(-1)

enc_token = kite_connect.get_enctoken(configuration_details["credentials"].get("username"), configuration_details["credentials"].get("password"), configuration_details["credentials"].get("time_based_otp_key"))
kite_client = kite_connect.KiteApp(enc_token)
print(enc_token)
print(kite_client.profile())
import pandas as pd
# Perform Kite API calls here
df = kite_client.historical_data("BANKNIFTY2440347000CE", "2014-04-01 09:00:00", "2014-04-01 16:00:00", "5 minute")
# df.to_csv("BANKNIFTY2440347000CE_APR_1_5_mins.csv")
print(df)
