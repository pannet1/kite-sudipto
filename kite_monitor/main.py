
import kite_connect
import utils



    

if __name__ == "__main__":
    configuration_details: list[dict] = utils.get_config_from_yaml() 
    credentials: dict = configuration_details.get('credentials')
    username: str = credentials.get('username')
    password: str = credentials.get('password')
    t_otp: str = credentials.get('time_based_otp_key')
    otp: str = utils.get_otp(t_otp)
    print(otp)
    enc_token = kite_connect.get_enctoken(username, password, otp)
    kite_app = kite_connect.KiteApp(enc_token)
    print(kite_app.profile())


