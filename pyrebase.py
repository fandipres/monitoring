import firebase_admin
import json
import pyrebase
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to Firebase
firebase = pyrebase.initialize_app(json.load(open('fbconfig.json')))
db = firebase.database()

# Menu
print("TAMBAH DATA")
print("1. Admin")
print("2. Member")
opsi = int(input("Opsi : "))
count = 0
if(opsi == 1):
    if(db.child('Admin').get()==None):
        count = 0
    else:
        snapshot = db.child('Admin').order_by_key().limit_to_last(1).get()
        for item in snapshot.each():
            count=item.key()
            count+=1
    print("TAMBAH DATA ADMIN")
    username = input("Username : ")
    password = input("Password : ")
    status = generate_password_hash(password, "sha256")
    db.child('Admin').child(str(count)).set({'username': username, 'password': generate_password_hash(password, "sha256")})
elif(opsi == 2):
    if(db.child('Member').get()==None):
        count = 0
    else:
        snapshot = db.child('Member').order_by_key().limit_to_last(1).get()
        for item in snapshot.each():
            count=item.key()
            count+=1
    print("TAMBAH DATA MEMBER")
    username = input("Username : ")
    password = input("Password : ")
    status = generate_password_hash(password, "sha256")
    db.child('Member').child(str(count)).set({'username': username, 'password': generate_password_hash(password, "sha256")})