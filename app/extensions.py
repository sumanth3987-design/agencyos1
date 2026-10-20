from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import razorpay
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

def get_razorpay_client():
    key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")
    try:
        return razorpay.Client(auth=(key_id, key_secret))
    except Exception as e:
        print(f"Warning: Razorpay client init failed (running in sandbox mode): {e}")
        return None
