from flask import Flask, jsonify, request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import google.generativeai as genai
from PIL import Image
import io
import re

from datetime import timezone
app = Flask(__name__)
CORS(app)

URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv('SECRET_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = MongoClient(URI)
db = client['purchase_manager']

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = db.users.find_one({"email": data['email']})
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except Exception:
            return jsonify({'message': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)

    return decorated

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Purchase Manager API"}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if any(key not in data for key in ['email', 'password', 'name']):
        return jsonify({"message": "Missing required fields"}), 400
    if not validate_email(data['email']):
        return jsonify({"message": "Invalid email format"}), 400
    is_valid_password, password_message = validate_password(data['password'])
    if not is_valid_password:
        return jsonify({"message": password_message}), 400
    if db.users.find_one({"email": data['email']}):
        return jsonify({"message": "Email already registered"}), 409
    hashed_password = generate_password_hash(data['password'], method="scrypt")
    user = {
        "email": data['email'],
        "password": hashed_password,
        "name": data['name'],
        "created_at": datetime.now(timezone.utc),
        "profile": {
            "phone": data.get('phone', ''),
            "address": data.get('address', ''),
            "preferences": {"notifications": True, "newsletter": False},
        },
    }
    print(user)
    db.users.insert_one(user)
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = db.users.find_one({"email": data['email']})
    if user and check_password_hash(user['password'], data['password']):
        token = jwt.encode(
            {
                'email': user['email'],
                'exp': datetime.now(timezone.utc) + timedelta(hours=24),
            },
            SECRET_KEY,
        )
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "email": user['email'],
                "name": user['name']
            }
        }), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/analyze-receipt', methods=['POST'])
@token_required
def analyze_receipt(current_user):
    if 'image' not in request.files:
        return jsonify({"message": "No image provided"}), 400
    image_file = request.files['image']
    try:
        image = Image.open(image_file)
        prompt = """
        Analyze this receipt/invoice image and extract the following information:
        1. Product name/description
        2. Purchase date (in YYYY-MM-DD format)
        3. Store name
        4. Total price (numeric value only)
        5. Product category (choose from: Electronics, Clothing, Home & Kitchen, Books, Sports, Others)
        6. Warranty period (if visible)
        7. Customer care number (if available)

        Return the information in this exact JSON format as given below and if some fields are missing then leave them empty and return in the JSON only:
        {
            "product_name": "",
            "purchase_date": "",
            "store_name": "",
            "price": "",
            "category": "",
            "warranty_period": "",
            "customer_care": ""
        }
        """
        response = model.generate_content([prompt, image])
        try:
            result = eval(response.text)
            return jsonify(result), 200
        except Exception:
            return jsonify({"message": "Failed to parse receipt information"}), 500
    except Exception as e:
        return jsonify({"message": f"Error processing image: {str(e)}"}), 500

@app.route('/invoice/add', methods=['POST'])
@token_required
def add_invoice(current_user):
    try:
        data = request.form.to_dict()
        required_fields = ['product_name', 'purchase_date', 'store_name', 'customer_care_number']
        if any(field not in data for field in required_fields):
            return jsonify({"message": "Missing required fields"}), 400
        bill_image = request.files.get('bill_image')
        additional_docs = request.files.getlist('documents')
        documents = []
        if bill_image:
            bill_image_path = f"bills/{current_user['_id']}_{bill_image.filename}"
            documents.append({
                "type": "bill",
                "path": bill_image_path,
                "name": bill_image.filename
            })
        for doc in additional_docs:
            doc_path = f"documents/{current_user['_id']}_{doc.filename}"
            documents.append({
                "type": "additional",
                "path": doc_path,
                "name": doc.filename
            })
        invoice = {
            "user_id": str(current_user['_id']),
            "product_name": data['product_name'],
            "purchase_date": datetime.fromisoformat(data['purchase_date']),
            "store_name": data['store_name'],
            "customer_care_number": data['customer_care_number'],
            "price": float(data.get('price', 0)),
            "category": data.get('category', 'Others'),
            "warranty_period": data.get('warranty_period'),
            "documents": documents,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = db.invoices.insert_one(invoice)
        return jsonify({
            "message": "Invoice added successfully",
            "invoice_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"message": f"Error adding invoice: {str(e)}"}), 500

@app.route('/invoice/list', methods=['GET'])
@token_required
def list_invoices(current_user):
    try:
        category = request.args.get('category')
        sort_by = request.args.get('sort_by', 'purchase_date')
        sort_order = int(request.args.get('sort_order', -1))
        query = {"user_id": str(current_user['_id'])}
        if category:
            query["category"] = category
        invoices = list(db.invoices.find(
            query,
            sort=[(sort_by, sort_order)]
        ))
        for invoice in invoices:
            invoice['_id'] = str(invoice['_id'])
            invoice['purchase_date'] = invoice['purchase_date'].isoformat()
            invoice['created_at'] = invoice['created_at'].isoformat()
            invoice['updated_at'] = invoice['updated_at'].isoformat()
        return jsonify(invoices), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching invoices: {str(e)}"}), 500

@app.route('/invoice/<invoice_id>', methods=['GET'])
@token_required
def get_invoice(current_user, invoice_id):
    try:
        invoice = db.invoices.find_one({
            "_id": ObjectId(invoice_id),
            "user_id": str(current_user['_id'])
        })
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404
        invoice['_id'] = str(invoice['_id'])
        invoice['purchase_date'] = invoice['purchase_date'].isoformat()
        invoice['created_at'] = invoice['created_at'].isoformat()
        invoice['updated_at'] = invoice['updated_at'].isoformat()
        return jsonify(invoice), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching invoice: {str(e)}"}), 500

@app.route('/invoice/<invoice_id>', methods=['PUT'])
@token_required
def update_invoice(current_user, invoice_id):
    try:
        data = request.json
        invoice = db.invoices.find_one({
            "_id": ObjectId(invoice_id),
            "user_id": str(current_user['_id'])
        })
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404
        updateable_fields = [
            'product_name', 'store_name', 'customer_care_number',
            'warranty_period', 'price', 'category', 'notes'
        ]
        updates = {field: data[field] for field in updateable_fields if field in data}
        if 'purchase_date' in data:
            updates['purchase_date'] = datetime.fromisoformat(data['purchase_date'])
        updates['updated_at'] = datetime.now(timezone.utc)
        if updates:
            db.invoices.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": updates}
            )
            return jsonify({"message": "Invoice updated successfully"}), 200
        return jsonify({"message": "No updates provided"}), 400
    except Exception as e:
        return jsonify({"message": f"Error updating invoice: {str(e)}"}), 500

@app.route('/invoice/<invoice_id>', methods=['DELETE'])
@token_required
def delete_invoice(current_user, invoice_id):
    try:
        result = db.invoices.delete_one({
            "_id": ObjectId(invoice_id),
            "user_id": str(current_user['_id'])
        })
        if result.deleted_count == 0:
            return jsonify({"message": "Invoice not found"}), 404
        return jsonify({"message": "Invoice deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error deleting invoice: {str(e)}"}), 500

@app.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    try:
        user_id = str(current_user['_id'])
        total_invoices = db.invoices.count_documents({"user_id": user_id})
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "total_value": {"$sum": {"$ifNull": ["$price", 0]}}
            }}
        ]
        categories = list(db.invoices.aggregate(pipeline))
        recent_invoices = list(db.invoices.find(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=5
        ))
        for invoice in recent_invoices:
            invoice['_id'] = str(invoice['_id'])
            invoice['purchase_date'] = invoice['purchase_date'].isoformat()
            invoice['created_at'] = invoice['created_at'].isoformat()
            invoice['updated_at'] = invoice['updated_at'].isoformat()
        return jsonify({
            "total_invoices": total_invoices,
            "categories": categories,
            "recent_invoices": recent_invoices
        }), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching dashboard stats: {str(e)}"}), 500

if __name__ == '__main__':
    app.run()
