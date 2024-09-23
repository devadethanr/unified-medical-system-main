from hashlib import sha256
import json
import random
import os
import requests
from flask import Blueprint, request, render_template, redirect, send_file, jsonify
from werkzeug.utils import secure_filename
from timeit import default_timer as timer
from pymongo import MongoClient
from bson import json_util
from os import getenv
from datetime import datetime
import json



client = MongoClient(getenv('MONGO_URI'))

db = client['umsdb']
blockchain_collection = db['medicalRecords']
meddata_bp = Blueprint('meddata', __name__)
# Block class
class Block:
    def __init__(self, index, transactions, prev_hash):
        self.index = index
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.nonce = 0
        self.record = datetime.utcnow()  # Add this line

    def generate_hash(self):
        all_data_combined = str(self.index) + str(self.nonce) + self.prev_hash + json_util.dumps(self.transactions)
        return sha256(all_data_combined.encode()).hexdigest()
    
    def add_t(self, t):
        self.transactions.append(t)

    def to_dict(self):
        return {
            "index": self.index,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "record": self.record
        }
    
# Blockchain class
class Blockchain:
    difficulty = 3

    def __init__(self):
        self.pending = []
        self.chain = []
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.generate_hash()
        self.chain.append(genesis_block)
    def add_block(self, block, hashl):
        prev_hash = self.last_block().hash
        if prev_hash == block.prev_hash and self.is_valid(block, hashl):
            block.hash = hashl
            self.chain.append(block)
        
            # Convert block to dictionary and store in MongoDB
            block_dict = {
                'index': block.index,
                'transactions': block.transactions,
                'prev_hash': block.prev_hash,
                'nonce': block.nonce,
                'hash': block.hash
            }
            blockchain_collection.insert_one(block_dict)
            
            return True
        else:
            return False

    def mine(self):
        if(len(self.pending) > 0):
            last_block = self.last_block()
            new_block = Block(last_block.index + 1, self.pending, last_block.hash)
            hashl = self.p_o_w(new_block)
            self.add_block(new_block, hashl)
            self.pending = []
            return new_block.index
        else:
            return False

    def p_o_w(self, block):
        block.nonce = 0
        get_hash = block.generate_hash()
        while not get_hash.startswith("0" * Blockchain.difficulty):
            block.nonce = random.randint(0,99999999)
            get_hash = block.generate_hash()
        return get_hash

    def add_pending(self, transaction):
        self.pending.append(transaction)
        
    def check_chain_validity(self, chain):
        result = True
        prev_hash = "0"
        for block in chain:
            block_hash = block.hash
            if self.is_valid(block, block.hash) and prev_hash == block.prev_hash:
                block.hash = block_hash
                prev_hash = block_hash
            else:
                result = False
        return result

    def is_valid(self, block, block_hash):
        if(block_hash.startswith("0" * Blockchain.difficulty)):
            if(block.generate_hash() == block_hash):
                return True
            else:
                return False
        else:
            return False

    def last_block(self):
        return self.chain[-1]

blockchain = Blockchain()
peers = []

# Stores all the post transaction in the node
request_tx = []
# store filename
files = {}
# destination for upload files
UPLOAD_FOLDER = "SIN13/unified-medical-system/UPLOADS"

# store address
ADDR = "http://127.0.0.1:8000"  # This port (8000) may conflict with your other Flask app

# create a list of requests that peers have sent to upload files
def get_tx_req():
    global request_tx
    chain_addr = "{0}/chain".format(ADDR)
    try:
        resp = requests.get(chain_addr)
        if resp.status_code == 200:
            content = []
            chain = json.loads(resp.content.decode())
            for block in chain["chain"]:
                for trans in block["transactions"]:
                    trans["index"] = block["index"]
                    trans["hash"] = block["prev_hash"]
                    content.append(trans)
            request_tx = sorted(content, key=lambda k: k["hash"], reverse=True)
    except requests.exceptions.ConnectionError:
        print(f"Unable to connect to {ADDR}. Make sure the port is not in use by another application.")
        request_tx = []


@meddata_bp.route('/')
def index():
    get_tx_req()
    return render_template('test/blockchain.html',node_address=ADDR, request_tx=request_tx)
@meddata_bp.route("/submit", methods=["POST"])
def submit():
    start = timer()
    user = request.form["user"]
    up_file = request.files["v_file"]
    
    # Ensure the UPLOAD_FOLDER exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Generate a secure filename and save the file
    filename = secure_filename(up_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    up_file.save(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Store the file path instead of the content
    files[filename] = file_path
    
    post_object = {
        "user": user,
        "v_file": filename,
        "file_path": file_path,
        "file_size": file_size
    }
   
    address = "{0}/new_transaction".format(ADDR)
    requests.post(address, json=post_object)
    end = timer()
    print(end - start)
    return redirect("/")


@meddata_bp.route("/submit/<string:variable>", methods=["GET"])
def download_file(variable):
    p = files[variable]
    return send_file(p, as_attachment=True)

@meddata_bp.route("/new_transaction", methods=["POST"])
def new_transaction():
    file_data = request.get_json()
    required_fields = ["user", "v_file", "file_data", "file_size"]
    for field in required_fields:
        if not file_data.get(field):
            return "Transaction does not have valid fields!", 404
    blockchain.add_pending(file_data)
    return "Success", 201

@meddata_bp.route("/chain", methods=["GET"])
def get_chain():
    chain = []
    for block in blockchain.chain:
        chain.append(block.__dict__)
    print("Chain Len: {0}".format(len(chain)))
    return json.dumps({"length": len(chain), "chain": chain})

@meddata_bp.route("/mine", methods=["GET"])
def mine_uncofirmed_transactions():
    result = blockchain.mine()
    if result:
        return "Block #{0} mined successfully.".format(result)
    else:
        return "No pending transactions to mine."

@meddata_bp.route("/pending_tx")
def get_pending_tx():
    return json.dumps(blockchain.pending)

@meddata_bp.route("/add_block", methods=["POST"])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"], block_data["transactions"], block_data["prev_hash"])
    hashl = block_data["hash"]
    added = blockchain.add_block(block, hashl)
    if not added:
        return "The Block was discarded by the node.", 400
    return "The block was added to the chain.", 201


@meddata_bp.route("/add_meddata", methods=["POST"])
def add_meddata_route():
    medical_data = request.get_json()
    result = add_meddata(medical_data)
    return jsonify(result), 201

from datetime import datetime
from bson import ObjectId

def add_meddata(medical_data):
    createdAt = datetime.utcnow()
    medical_data["createdAt"] = createdAt
    medical_data["record"] = createdAt.isoformat()  # Add this line to include the required 'record' field
    
    # Convert ObjectId to string if present
    if '_id' in medical_data and isinstance(medical_data['_id'], ObjectId):
        medical_data['_id'] = str(medical_data['_id'])
    
    blockchain.add_pending(medical_data)
    result = blockchain.mine()
    
    if result:
        return {"message": f"Medical data added and Block #{result} mined successfully."}
    else:
        return {"message": "Medical data added to pending transactions."}

@meddata_bp.route("/get_meddata", methods=["GET"])
def get_meddata():
    medical_data = request.get_json()
    # Validate the required fields
    required_fields = ["patientId", "doctorId", "hospitalId", "Symptoms", "Diagnosis", "TreatmentPlan", "Prescription", "AdditionalNotes", "FollowUpDate", "Attachments"]
    for field in required_fields:
        if not medical_data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400
