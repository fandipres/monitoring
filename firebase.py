import firebase_admin
import json
from firebase_admin import credentials, db
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to Firebase
cred = credentials.Certificate('firebase/fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL':json.load(open('firebase/fbConfig.json'))['databaseURL']})

# DB Reference
ref = db.reference('/')
admin_ref=ref.child('Admin')
member_ref=ref.child('Member')
kategori_ref=ref.child('Kategori_Aktivitas')
riwayat_ref=ref.child('Riwayat_Monitoring')
log_ref=ref.child('Log_Riwayat_Monitoring')

# Menu Utama
print("MENU UTAMA")
print("1. Menu User")
print("2. Menu Aktivitas")
opsi = int(input("Opsi : "))
# Menu User
if(opsi == 1):
    print("MENU USER")
    print("1. Lihat Data Admin")
    print("2. Lihat Data Member")
    print("3. Tambah Data Admin")
    print("4. Tambah Data Member")
    opsi = int(input("Opsi : "))
    if(opsi == 1):
        print("LIHAT DATA ADMIN")
        tbl = admin_ref.get(True, False)[0].items() if len(admin_ref.get())!=0 else ""
        print(tbl)
    elif(opsi == 2):
        print("LIHAT DATA MEMBER")
        tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
        print(tbl)
    elif(opsi == 3):
        print("TAMBAH DATA ADMIN")
        username = input("Username : ")
        password = input("Password : ")
        if(admin_ref.child(username).get()==None):
            admin_ref.child(username).set({'password': generate_password_hash(password)})
        else:
            print("Username exists.")
    elif(opsi == 4):
        print("TAMBAH DATA MEMBER")
        username = input("Username : ")
        password = input("Password : ")
        if(member_ref.child(username).get()==None):
            member_ref.child(username).set({'password': generate_password_hash(password)})
        else:
            print("Username exists.")
# Menu Aktivitas
elif(opsi == 2):
    print("MENU AKTIVITAS")
    print("1. Lihat Data Aktivitas")
    print("2. Tambah Data Aktivitas")
    opsi = int(input("Opsi : "))
    if(opsi == 1):
        print("LIHAT DATA AKTIVITAS")
        tbl = kategori_ref.get(True, False)[0] if len(kategori_ref.get())!=0 else ""
        print(tbl)
    elif(opsi == 2):
        count = 0 if len(kategori_ref.get())==0 else int([*kategori_ref.get(False, True)][-1])+1
        print("TAMBAH DATA AKTIVITAS")
        aktivitas = input("Nama Aktivitas : ")
        kategori_ref.child(str(count)).set({'nama_aktivitas': aktivitas})