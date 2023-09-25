from flask import Flask, jsonify, Blueprint
import pymongo

app = Flask(__name__)
dc = Blueprint('dc', __name__)

# Replace with your actual connection string
connection_string = "mongodb://root:nucloud@10.97.62.194:30050,10.97.62.194:30051,10.97.62.194:30052/?retryWrites=true&replicaSet=nucloudrs&readPreference=primary&serverSelectionTimeoutMS=5000&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-256"

# Create a MongoClient instance
client = pymongo.MongoClient(connection_string)

# Access a specific database (replace 'your-database-name' with the actual database name)
qms_db = client['qms']

# Access a specific collection (replace 'your-collection-name' with the actual collection name)
users_collection = qms_db['users']
coupons_collection = qms_db['coupons']

# Now you can perform MongoDB operations on the 'collection' object


@app.route('/')
def index():
    return jsonify({"detail": "Not found"})


def find_deleted_coupons():
    deleted_coupons = []
    coupons = []
    users = list(users_collection.find({"coupon_usage": {"$exists": True}},{"username": 1,"coupon_usage":1, "_id":0}))
    for user in users:
        username = user["username"]
        coupon_usage = user["coupon_usage"]
        individual_coupon_usage = {}
        overall_coupon_usage = {}
        
        try:
            individual_coupon_usage = coupon_usage["individual"]
        except:
            print(f"individual coupon is not present for {username}")

        try:
            overall_coupon_usage = coupon_usage["overall"]
        except:
            print(f"overall coupon is not present for {username}")

        for key, value in individual_coupon_usage.items():
            coupons.append({"coupon_name":key, "usage":value, "user": username})

        for key, value in overall_coupon_usage.items():
            coupons.append({"coupon_name":key, "usage":value, "user": username})

    active_coupons = list(coupons_collection.find({},{"name": 1, "_id":0}))
    active_coupons = [coupon["name"] for coupon in active_coupons]

    for coupon in coupons:
        if coupon["coupon_name"] not in active_coupons:
            deleted_coupons.append(coupon)

    return deleted_coupons


@app.route('/deleted_coupons')
def _deleted_coupons():
    return find_deleted_coupons()

@dc.route('/zero_usage')
def zero_usage_deleted_coupons():
    deleted_coupons = find_deleted_coupons()
    
    report = []

    for coupon in deleted_coupons:
        if coupon["usage"] == 0:
            report.append(coupon)

    return report

@dc.route('/non_zero_usage')
def non_zero_usage_deleted_coupons():
    deleted_coupons = find_deleted_coupons()
    
    report = []

    for coupon in deleted_coupons:
        if coupon["usage"] != 0:
            report.append(coupon)

    return report

app.register_blueprint(dc, url_prefix='/deleted_coupons')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)