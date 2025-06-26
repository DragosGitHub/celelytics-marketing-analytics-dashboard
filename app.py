import os
import pandas as pd
from flask import Flask, request, jsonify, render_template
import logging
import traceback
from dotenv import load_dotenv
from flask_cors import CORS
import openai
from openai import AzureOpenAI
from process import (
    load_data_from_adls,
    join_data,
    analyze_data,
    store_insights,
    save_contact_submission
)

print("✅ OpenAI version:", openai.__version__)

# ✅ Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Initialize Flask app and set static/template directories
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['DEBUG'] = True
CORS(app)

# ✅ Load environment variables
load_dotenv()

# 🔐 Azure Config from .env
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("AZURE_FILE_SYSTEM_NAME")
TRANSACTIONS_PATH = os.getenv("AZURE_TRANSACTIONS_PATH")
PRODUCTS_PATH = os.getenv("AZURE_PRODUCTS_PATH")
TABLE_CONNECTION_STRING = os.getenv("TABLE_CONNECTION_STRING", "")

# 🤖 GPT Config
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://22bcs-mcd49sn1-eastus2.cognitiveservices.azure.com/")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_DEPLOYMENT_NAME = "chatbot-gpt"

# ✅ Initialize OpenAI client
azure_client = AzureOpenAI(
    api_version="2023-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY
)

# ✅ Serve frontend index.html
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Process uploaded or cloud-hosted data
@app.route('/process', methods=['POST'])
def process_data():
    print("🔍 /process route hit")
    try:
        # 🧾 Check file upload or fallback to ADLS
        if 'transactions' in request.files and 'products' in request.files:
            print("📝 Upload files received")
            transactions = pd.read_csv(request.files['transactions'])
            products = pd.read_csv(request.files['products'])
        else:
            print("☁️ Loading from Azure")
            transactions = load_data_from_adls(STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY, CONTAINER_NAME, TRANSACTIONS_PATH)
            products = load_data_from_adls(STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY, CONTAINER_NAME, PRODUCTS_PATH)

        # ✅ Validate expected columns
        expected_txn_cols = {'transaction_id', 'customer_id', 'product_id', 'quantity', 'date', 'channel'}
        expected_prod_cols = {'product_id', 'product_name', 'price', 'category'}

        if not expected_txn_cols.issubset(transactions.columns.str.lower()):
            raise ValueError("🚫 The transactions file seems invalid or incomplete. Please make sure it contains columns like 'transaction_id', 'customer_id', etc.")

        if not expected_prod_cols.issubset(products.columns.str.lower()):
            raise ValueError("🚫 The products file seems invalid or incomplete. Please ensure it contains columns like 'product_name', 'price', etc.")

        print("📦 Joining data")
        df = join_data(transactions, products)

        print("📊 Analyzing data")
        insights = analyze_data(df)

        # ✅ Store insights
        store_insights(
            insights,
            STORAGE_ACCOUNT_NAME,
            STORAGE_ACCOUNT_KEY,
            CONTAINER_NAME,
            base_path="saved-insights"
        )

        print("✅ Returning insights")
        return jsonify({
            "success": True,
            "message": "Your insights have been saved to cloud.",
            "insights": insights
        })

    except Exception as e:
        print("❌ Error occurred:", str(e))
        return jsonify({
            "success": False,
            "error": str(e),
            "details": "Make sure your CSV files are correct and properly formatted."
        }), 500

# ✅ Contact form handler
@app.route('/contact', methods=['POST'])
def contact_submission():
    try:
        data = request.json
        save_contact_submission(
            TABLE_CONNECTION_STRING,
            "contacts",
            data['name'],
            data['email'],
            data['message']
        )
        logger.info("Contact form submitted")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error in /contact: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ✅ Chatbot route
@app.route('/ask', methods=['POST'])
def ask_gpt():
    try:
        user_question = request.json.get('message', '')
        if not user_question:
            return jsonify({"error": "No question provided"}), 400

        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for marketing analytics insights."},
                {"role": "user", "content": user_question}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        answer = response.choices[0].message.content
        return jsonify({"reply": answer})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# ✅ Run the server locally
if __name__ == '__main__':
    print("✅ Flask app starting...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
