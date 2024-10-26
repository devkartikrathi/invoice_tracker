from flask import Flask, jsonify, request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# Load environment variables
URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv('SECRET_KEY')
# Initialize MongoDB client
client = MongoClient(URI)
db = client['purchase_manager']

@app.route('/register', methods=['POST'])
def register():
  data = request.json
  hashed_password = generate_password_hash(data['password'], method='sha256')
  user = {
      "email": data['email'],
      "password": hashed_password
  }
  db.users.insert_one(user)
  return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
  data = request.json
  user = db.users.find_one({"email": data['email']})
  if user and check_password_hash(user['password'], data['password']):
      return jsonify({"message": "Login successful"}), 200
  return jsonify({"message": "Invalid credentials"}), 401

@app.route('/invoice/add', methods=['POST'])
def add_invoice():
  data = request.json
  invoice = {
      "user_id": data['user_id'],
      "product_name": data['product_name'],
      "purchase_date": data['purchase_date'],
      "store_name": data['store_name'],
      "customer_care_number": data['customer_care_number'],
      "documents": data.get('documents', [])
  }
  db.invoices.insert_one(invoice)
  return jsonify({"message": "Invoice added successfully"}), 201

@app.route('/invoice/list', methods=['GET'])
def list_invoices():
  user_id = request.args.get('user_id')
  invoices = list(db.invoices.find({"user_id": user_id}))
  for invoice in invoices:
      invoice['_id'] = str(invoice['_id'])
  return jsonify(invoices), 200

@app.route('/invoice/delete/<invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
  db.invoices.delete_one({"_id": ObjectId(invoice_id)})
  return jsonify({"message": "Invoice deleted successfully"}), 200

if __name__ == '__main__':
#   app.run(debug=True)
    app.run()