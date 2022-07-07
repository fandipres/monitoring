from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
import firebase_admin
import json
from firebase_admin import credentials, auth, db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

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

camera = cv2.VideoCapture(0)
admin = True

@app.context_processor 
def nav_templates():
    nav = [
    {"text": "Monitoring", "url": url_for('monitoring')},
    {"text": "Riwayat Monitoring", "url": url_for('riwayat_monitoring')},
    ]

    if(admin):
        nav.append({"text":"Kelola Member", "url": url_for('kelola_member')})
        nav.append({"text":"Profile", "url": url_for('profile')})
    else:
        nav.append({"text":"Profile", "url": url_for('profile')})
    return dict(navbar = nav)
    
def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/', methods=['GET', 'POST'])
def index():
    if(request.method == "GET"):
        return render_template('index.html')
    elif(request.method == "POST"):
        if(admin_ref.child(request.form.get('username')).get()!=None and check_password_hash(admin_ref.child(request.form.get('username')).child('password').get(), request.form.get('password'))):
            return redirect(url_for('monitoring'))
        elif(member_ref.child(request.form.get('username')).get()!=None and check_password_hash(member_ref.child(request.form.get('username')).child('password').get(), request.form.get('password'))):
            return redirect(url_for('monitoring'))
        else:
            error = "Username atau Password salah, silahkan coba login kembali."
            return render_template('index.html', error=error)

@app.route('/monitoring')
def monitoring():
    tbl = [{"text":"ok11", "text2":"ok12", "text3":"ok13"},{"text":"ok21", "text2":"ok22", "text3":"ok23"},{"text":"ok31", "text2":"ok32", "text3":"ok33"}]
    return render_template('monitoring.html', data=tbl)

@app.route('/riwayat_monitoring')
def riwayat_monitoring():
    tbl = [{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok11", "text2":"ok12", "text3":"ok13", "text4":"ok14", "text5":"ok15", "text6":"ok16", "text7":"ok17"},{"text":"ok21", "text2":"ok22", "text3":"ok23"},{"text":"ok31", "text2":"ok32", "text3":"ok33"}]
    return render_template('riwayat_monitoring.html', len=len(tbl), data=tbl)

@app.route('/detail_aktivitas')
def detail_aktivitas():
    return render_template('detail_aktivitas.html')
    
@app.route('/kelola_member', methods=['GET', 'POST'])
def kelola_member():
    if(request.method == "GET"):
        tbl = member_ref.get(True, False)[0].items()
        return render_template('kelola_member.html', data=tbl)
    elif(request.method == "POST" and request.form.get('_method') == "Tambah"):
        if(request.form.get('username') == "" or request.form.get('password') == ""):
            tbl = member_ref.get(True, False)[0].items()
            error = "Field username dan field password tidak boleh kosong."
            return render_template('kelola_member.html', data=tbl, error=error)
        elif(admin_ref.child(request.form.get('username')).get()!=None or member_ref.child(request.form.get('username')).get()!=None):
            tbl = member_ref.get(True, False)[0].items()
            error = "Username sudah digunakan, silahkan gunakan username lain."
            return render_template('kelola_member.html', data=tbl, error=error)
        else:
            if(request.form.get('role') == "admin"):
                admin_ref.child(request.form.get('username')).set({'nama': request.form.get('name'), 'no_telepon': request.form.get('phone'), 'password': generate_password_hash(request.form.get('password'), "sha256")})
            else:
                member_ref.child(request.form.get('username')).set({'nama': request.form.get('name'), 'no_telepon': request.form.get('phone'), 'password': generate_password_hash(request.form.get('password'), "sha256")})
            success = "Data user berhasil ditambahkan."
            tbl = member_ref.get(True, False)[0].items()
            return render_template('kelola_member.html', data=tbl, success=success)
    elif(request.method == "POST" and request.form.get('_method') == "Simpan"):
        if(request.form.get('usernameedit') == ""):
            tbl = member_ref.get(True, False)[0].items()
            error = "Field username tidak boleh kosong."
            return render_template('kelola_member.html', data=tbl, error=error)
        elif(request.form.get('usernameedit') != request.form.get('usernameedittemp')):
            if(admin_ref.child(request.form.get('usernameedit')).get()!=None or member_ref.child(request.form.get('usernameedit')).get()!=None):
                error = "Username sudah dipergunakan, silahkan gunakan username lain."
                tbl = member_ref.get(True, False)[0].items()
                return render_template('kelola_member.html', data=tbl, error=error)
            else:
                if(request.form.get('passwordedit') == ""):
                    member_ref.child(request.form.get('usernameedit')).set({'nama': request.form.get('nameedit'), 'no_telepon': request.form.get('phoneedit'), 'password': member_ref.child(request.form.get('usernameedittemp')).child('password').get()})
                else:
                    member_ref.child(request.form.get('usernameedit')).set({'nama': request.form.get('nameedit'), 'no_telepon': request.form.get('phoneedit'), 'password': generate_password_hash(request.form.get('passwordedit'), "sha256")})
                member_ref.child(request.form.get('usernameedittemp')).delete()
                success = "Data user berhasil diperbaharui."
                tbl = member_ref.get(True, False)[0].items()
                return render_template('kelola_member.html', data=tbl, success=success)
        else:
            if(request.form.get('passwordedit') == ""):
                member_ref.child(request.form.get('usernameedit')).update({'nama': request.form.get('nameedit'), 'no_telepon': request.form.get('phoneedit'), 'password': member_ref.child(request.form.get('usernameedittemp')).child('password').get()})
            else:
                member_ref.child(request.form.get('usernameedit')).update({'nama': request.form.get('nameedit'), 'no_telepon': request.form.get('phoneedit'), 'password': generate_password_hash(request.form.get('passwordedit'), "sha256")})
            success = "Data user berhasil diperbaharui."
            tbl = member_ref.get(True, False)[0].items()
            return render_template('kelola_member.html', data=tbl, success=success)
    elif(request.method == "POST" and request.form.get('_method') == "Hapus"):
        member_ref.child(request.form.get('usernamedeletetemp')).delete()
        success = "Data user berhasil dihapus."
        tbl = member_ref.get(True, False)[0].items()
        return render_template('kelola_member.html', data=tbl, success=success)
        
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = "member"
    if(request.method == "GET"):
        tbl = member_ref.child(username).get()
        return render_template('profile.html', username=username, data=tbl)
    elif(request.method == "POST" and request.form.get('_method') == "Simpan"):
        if(request.form.get('username') == ""):
            error = "Field username tidak boleh kosong."
            tbl = member_ref.child(username).get()
            return render_template('profile.html', username=username, data=tbl, error=error)
        elif(request.form.get('username') != request.form.get('usernametemp')):
            if(admin_ref.child(request.form.get('username')).get()!=None or member_ref.child(request.form.get('username')).get()!=None):
                error = "Username sudah dipergunakan, silahkan gunakan username lain."
                tbl = member_ref.child(request.form.get('username')).get()
                return render_template('profile.html', username=request.form.get('username'), data=tbl, error=error)
            else:
                member_ref.child(request.form.get('username')).set({'nama': request.form.get('name'), 'no_telepon': request.form.get('phone'), 'password': member_ref.child(request.form.get('usernametemp')).child('password').get()})
                member_ref.child(request.form.get('usernametemp')).delete()
                success = "Perubahan data berhasil disimpan."
                tbl = member_ref.child(request.form.get('username')).get()
                return render_template('profile.html', username=request.form.get('username'), data=tbl, success=success)
        else:
            member_ref.child(request.form.get('username')).update({'nama': request.form.get('name'), 'no_telepon': request.form.get('phone'), 'password': member_ref.child(request.form.get('usernametemp')).child('password').get()})
            success = "Perubahan data berhasil disimpan."
            tbl = member_ref.child(request.form.get('username')).get()
            return render_template('profile.html', username=request.form.get('username'), data=tbl, success=success)
    elif(request.method == "POST" and request.form.get('_method') == "Ganti Password"):
        if(request.form.get('currentpassword') == "" or request.form.get('newpassword') == ""):
            error = "Field password tidak boleh kosong."
            tbl = member_ref.child(request.form.get('username')).get()
            return render_template('profile.html', username=request.form.get('username'), data=tbl, error=error)
        else:
            if(check_password_hash(member_ref.child(request.form.get('username')).child('password').get(), request.form.get('currentpassword'))):
                member_ref.child(request.form.get('username')).update({'password': generate_password_hash(request.form.get('newpassword'), "sha256")})
                success = "Password berhasil diganti."
                tbl = member_ref.child(request.form.get('username')).get()
                return render_template('profile.html', username=request.form.get('username'), data=tbl, success=success)
            else:
                error = "Password saat ini salah."
                tbl = member_ref.child(request.form.get('username')).get()
                return render_template('profile.html', username=request.form.get('username'), data=tbl, error=error)
            
if __name__ == '__main__':
    app.run(debug=False)