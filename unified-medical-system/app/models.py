from flask_login import UserMixin
from app import mongo
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self,umsId, username, email, password, user_type):
        self.username = username
        self.email = email
        self.password = password
        self.user_type = user_type

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(
                umsId=user_data['umsId'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                user_type=user_data['user_type']
            )
        return None

    @staticmethod
    def find_by_username(username):
        user_data = mongo.db.users.find_one({"username": username})
        if user_data:
            return User(
                umsId=user_data['umsId'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                user_type=user_data['user_type']
            )
        return None
    
    @staticmethod
    def find_by_email(email):
        user_data = mongo.db.users.find_one({"email": email})
        if user_data:
            print(user_data['umsId']) #for debugging
            return User(
                umsId=user_data['umsId'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                user_type=user_data['user_type']
            )
        return None