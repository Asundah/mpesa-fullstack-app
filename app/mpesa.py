import requests
import base64
from datetime import datetime
from .config import Config

class MpesaAPI:
    def __init__(self):
        self.consumer_key = Config.CONSUMER_KEY
        self.consumer_secret = Config.CONSUMER_SECRET
        self.shortcode = Config.SHORTCODE
        self.passkey = Config.PASSKEY
        self.callback_url = Config.CALLBACK_URL

        if Config.ENVIRONMENT == "production":
            self.base_url = "https://api.safaricom.co.ke"
        else:
            self.base_url = "https://sandbox.safaricom.co.ke"

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()

        headers = {"Authorization": f"Basic {auth}"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json().get("access_token")
        return None

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        token = self.get_access_token()
        if not token:
            return {"error": "Failed to obtain access token"}

        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+"):
            phone_number = phone_number[1:]

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        return response.json()