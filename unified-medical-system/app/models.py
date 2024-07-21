from flask_login import UserMixin
from app import mongo
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self, _id, umsId, email, passwordHash, rolesId, username=None, **kwargs):
        self.id = str(_id)  # This is needed by Flask-Login
        self.umsId = umsId
        self.email = email
        self.passwordHash = self.passwordHash = passwordHash[0] if isinstance(passwordHash, list) and len(passwordHash) > 0 else None
        self.rolesId = rolesId
        self.username = username
        self.status = kwargs.get('status')

    @staticmethod
    def get(user_id):
        user_data = mongo.db.login.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(
                _id = user_data.get('_id'),
                umsId=user_data.get('umsId'),
                email=user_data.get('email'),
                passwordHash=user_data.get('passwordHash'),
                rolesId=user_data.get('rolesId'),
                username=user_data.get('username'),
                status=user_data.get('status')
            )
        return None

    @staticmethod
    def find_by_identifier(identifier):
        # Search by email or umsId
        user_data = mongo.db.login.find_one({
            "$or": [
                {"email": identifier},
                {"umsId": identifier}
            ]
        })
        if user_data:
            return User(
                _id= user_data.get('_id'),
                umsId=user_data.get('umsId'),
                email=user_data.get('email'),
                passwordHash=user_data.get('passwordHash'),
                rolesId=user_data.get('rolesId'),
                username=user_data.get('username'),
                status=user_data.get('status')
            )
        return None
