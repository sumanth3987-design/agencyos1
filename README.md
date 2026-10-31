# 1. Clone the repository
git clone https://github.com/sumanth3987-design/agencyos1.git
cd agencyos1

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables (.env)
# Create a .env file in the root directory:
SECRET_KEY=your_cryptographically_secure_random_key_min_32_chars
FLASK_ENV=development
RAZORPAY_KEY_ID=rzp_test_placeholder
RAZORPAY_KEY_SECRET=placeholder_secret

# 5. Run the local application
python run.py