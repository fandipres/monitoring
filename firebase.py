import firebase_admin
import json
from firebase_admin import credentials, db
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to Firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL':json.load(open('fbconfig.json'))['databaseURL']})

# DB Reference
ref = db.reference('/')
admin_ref=ref.child('Admin')
member_ref=ref.child('Member')
kategori_ref=ref.child('Kategori_Aktivitas')
riwayat_ref=ref.child('Riwayat_Monitoring')
log_ref=ref.child('Log_Riwayat_Aktivitas')

# Menu Versi 1
# print("TAMBAH DATA")
# print("1. Admin")
# print("2. Member")
# opsi = int(input("Opsi : "))
# count = 0
# if(opsi == 1):
    # if(len(admin_ref.get())==0):
        # count = 0
    # else:
        # snapshot = admin_ref.get(False, True)
        # count = int([*snapshot][-1])
        # count += 1
    # print("TAMBAH DATA ADMIN")
    # username = input("Username : ")
    # password = input("Password : ")
    # admin_ref.child(str(count)).set({'username': username, 'password': generate_password_hash(password, "sha256")})
# elif(opsi == 2):
    # if(len(member_ref.get())==0):
        # count = 0
    # else:
        # snapshot = member_ref.get(False, True)
        # count = int([*snapshot][-1])
        # count += 1
    # print("TAMBAH DATA MEMBER")
    # username = input("Username : ")
    # password = input("Password : ")
    # member_ref.child(str(count)).set({'username': username, 'password': generate_password_hash(password, "sha256")})

# Menu Versi 2
print("TAMBAH DATA")
print("1. Admin")
print("2. Member")
opsi = int(input("Opsi : "))
if(opsi == 1):
    print("TAMBAH DATA ADMIN")
    username = input("Username : ")
    password = input("Password : ")
    if(admin_ref.child(username).get()==None):
        admin_ref.child(username).set({'password': generate_password_hash(password, "sha256")})
    else:
        print("Username exists.")
elif(opsi == 2):
    print("TAMBAH DATA MEMBER")
    username = input("Username : ")
    password = input("Password : ")
    if(member_ref.child(username).get()==None):
        member_ref.child(username).set({'password': generate_password_hash(password, "sha256")})
    else:
        print("Username exists.")