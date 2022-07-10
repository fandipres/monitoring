from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
import firebase_admin
import json
from firebase_admin import credentials, auth, db, storage
from werkzeug.security import generate_password_hash, check_password_hash

# Detectron2
import torch 
import torchvision
import datetime
import glob
import os
import numpy as np
import json
import random
import matplotlib.pyplot as plt
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.engine import DefaultTrainer, DefaultPredictor
from detectron2.structures import BoxMode
from detectron2.utils.visualizer import ColorMode, Visualizer

def get_data_dicts(directory, classes):
    dataset_dicts = []
    for filename in [file for file in os.listdir(directory) if file.endswith('.json')]:
        json_file = os.path.join(directory, filename)
        with open(json_file) as f:
            img_anns = json.load(f)

        record = {}
        
        filename = os.path.join(directory, img_anns["imagePath"])
        
        record["file_name"] = filename
        record["height"] = 3840
        record["width"] = 2160
      
        annos = img_anns["shapes"]
        objs = []
        for anno in annos:
            px = [a[0] for a in anno['points']] # x coord
            py = [a[1] for a in anno['points']] # y-coord
            poly = [(x, y) for x, y in zip(px, py)] # poly for segmentation
            poly = [p for x in poly for p in x]

            obj = {
                "bbox": [np.min(px), np.min(py), np.max(px), np.max(py)],
                "bbox_mode": BoxMode.XYXY_ABS,
                "segmentation": [poly],
                "category_id": classes.index(anno['label']),
                "iscrowd": 0
            }
            objs.append(obj)
        record["annotations"] = objs
        dataset_dicts.append(record)
    return dataset_dicts
    
classes = ["mengambil_handphone", "membuka_pintu"]

data_path = 'dataset/'

for d in ["train", "test"]:
    DatasetCatalog.register(
        "category_" + d, 
        lambda d=d: get_data_dicts(data_path+d, classes)
    )
    MetadataCatalog.get("category_" + d).set(thing_classes=classes)

microcontroller_metadata = MetadataCatalog.get("category_train")

cfg = get_cfg()
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
cfg.merge_from_file(model_zoo.get_config_file("Misc/mask_rcnn_R_50_FPN_3x_gn.yaml"))
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 2
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.3
cfg.DATASETS.TEST = ("skin_test", )
predictor = DefaultPredictor(cfg)

test_dataset_dicts = get_data_dicts(data_path+'test', classes)

# Flask App
app = Flask(__name__)

# Connect to Firebase
cred = credentials.Certificate('firebase/fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL':json.load(open('firebase/fbConfig.json'))['databaseURL'], 'storageBucket':'cctv-f970e.appspot.com'})
bucket = storage.bucket()
                
# DB Reference
ref = db.reference('/')
admin_ref=ref.child('Admin')
member_ref=ref.child('Member')
kategori_ref=ref.child('Kategori_Aktivitas')
riwayat_ref=ref.child('Riwayat_Monitoring')
log_ref=ref.child('Log_Riwayat_Monitoring')

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
            log = 0 if len(log_ref.get())==0 else int([*log_ref.get(False, True)][-1])+1
            predictions = predictor(frame)
            if(len(predictions.get("instances").pred_classes) != 0):
                v = Visualizer(frame[:,:,::-1], metadata=microcontroller_metadata, scale=1, instance_mode=ColorMode.SEGMENTATION)
                output = v.draw_instance_predictions(predictions["instances"].to("cpu"))
                time = datetime.datetime.now()
                current_time = time.strftime("%d%m%Y-%H%M%S")
                filename = '%s.jpeg' % current_time
                cv2.imwrite("capture\image-"+filename, output.get_image()[:,:,::-1])
                blob = bucket.blob("image-"+filename)
                blob.upload_from_filename("capture\image-"+filename)
                if(0 in predictions.get("instances").pred_classes):
                    print("mengambil_handphone")
                    riwayat_ref.child("activity-"+filename[0:-5]).set({'kategori': "0", 'waktu': time.strftime("%H:%M:%S-%d/%m/%Y"), 'gambar': "image-"+filename})
                    log_ref.child(str(log)).set({'riwayat': "activity-"+filename[0:-5], 'username': "sistem", 'waktu': time.strftime("%H:%M:%S-%d/%m/%Y"), 'keterangan': 'created'})
                elif(1 in predictions.get("instances").pred_classes):
                    print("membuka_pintu")
                    riwayat_ref.child("activity-"+filename[0:-5]).set({'kategori': "1", 'waktu': time.strftime("%H:%M:%S-%d/%m/%Y"), 'gambar': "image-"+filename})
                    log_ref.child(str(log)).set({'riwayat': "activity-"+filename[0:-5], 'username': "sistem", 'waktu': time.strftime("%H:%M:%S-%d/%m/%Y"), 'keterangan': 'created'})
                elif(0 in predictions.get("instances").pred_classes and 1 in predictions.get("instances").pred_classes):
                    print("dua-duanya")
                    riwayat_ref.child("activity-"+filename[0:-5]).set({'kategori': "0, 1", 'waktu': time.strftime("%H:%M:%S-%d/%m/%Y"), 'gambar': "image-"+filename})
                    log_ref.child(str(log)).set({'riwayat': "activity-"+filename[0:-5], 'username': "sistem", 'waktu': time.strftime("%H:%M:%S-%d/%m/%Y"), 'keterangan': 'created'})
                ret, buffer = cv2.imencode('.jpg', output.get_image()[:,:,::-1])
                frame = buffer.tobytes()
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
    return render_template('monitoring.html')

@app.route('/riwayat_monitoring')
def riwayat_monitoring():
    if(request.method == "GET"):
        tbl = riwayat_ref.get(True, False)[0].items() if len(riwayat_ref.get())!=0 else ""
        return render_template('riwayat_monitoring.html', data=tbl)

@app.route('/detail_aktivitas')
def detail_aktivitas():
    return render_template('detail_aktivitas.html')
    
@app.route('/kelola_member', methods=['GET', 'POST'])
def kelola_member():
    if(request.method == "GET"):
        tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
        return render_template('kelola_member.html', data=tbl)
    elif(request.method == "POST" and request.form.get('_method') == "Tambah"):
        if(request.form.get('username') == "" or request.form.get('password') == ""):
            tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
            error = "Field username dan field password tidak boleh kosong."
            return render_template('kelola_member.html', data=tbl, error=error)
        elif(admin_ref.child(request.form.get('username')).get()!=None or member_ref.child(request.form.get('username')).get()!=None):
            tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
            error = "Username sudah digunakan, silahkan gunakan username lain."
            return render_template('kelola_member.html', data=tbl, error=error)
        else:
            if(request.form.get('role') == "admin"):
                admin_ref.child(request.form.get('username')).set({'nama': request.form.get('name'), 'no_telepon': request.form.get('phone'), 'password': generate_password_hash(request.form.get('password'), "sha256")})
            else:
                member_ref.child(request.form.get('username')).set({'nama': request.form.get('name'), 'no_telepon': request.form.get('phone'), 'password': generate_password_hash(request.form.get('password'), "sha256")})
            success = "Data user berhasil ditambahkan."
            tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
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
        if len(member_ref.get())==1:
            error = "Tidak dapat menghapus member, minimal terdapat 1 member."
            tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
            return render_template('kelola_member.html', data=tbl, error=error)
        else:
            member_ref.child(request.form.get('usernamedeletetemp')).delete()
            success = "Data user berhasil dihapus."
            tbl = member_ref.get(True, False)[0].items() if len(member_ref.get())!=0 else ""
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