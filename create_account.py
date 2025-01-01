import sys
import argparse
from app import app, db, User
import jwt

def create_account(email, subscription_plan):
    with app.app_context():
        if User.query.filter_by(email=email).first():
            print(f"Error: Email {email} is already registered")
            return False

        jwt_token = jwt.encode(
            {'email': email},
            app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )

        user = User(
            email=email,
            subscription_plan=subscription_plan,
            jwt_token=jwt_token
        )
        db.session.add(user)
        db.session.commit()
        print(f"Account created successfully for {email}")
        print(f"JWT Token: {jwt_token}")
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new user account')
    parser.add_argument('email', help='User email address')
    parser.add_argument('--plan', choices=['free', 'silver', 'gold'], default='free',
                      help='Subscription plan (default: free)')
    
    args = parser.parse_args()
    create_account(args.email, args.plan)