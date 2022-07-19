import torch
# assert torch.__version__.startswith("1.8") 
import torchvision
import cv2
import datetime
import glob
import os
import numpy as np
import json
import random
import matplotlib.pyplot as plt
# %matplotlib inline

from detectron2.structures import BoxMode
from detectron2.data import DatasetCatalog, MetadataCatalog

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
    
classes = ["mengambil_hp", "membuka_pintu"]

data_path = 'dataset/'

for d in ["train", "test"]:
    DatasetCatalog.register(
        "category_" + d, 
        lambda d=d: get_data_dicts(data_path+d, classes)
    )
    MetadataCatalog.get("category_" + d).set(thing_classes=classes)

microcontroller_metadata = MetadataCatalog.get("category_train")

from detectron2 import model_zoo
from detectron2.engine import DefaultTrainer, DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode, Visualizer

cfg = get_cfg()
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
cfg.merge_from_file(model_zoo.get_config_file("Misc/mask_rcnn_R_50_FPN_3x_gn.yaml"))
# cfg.DATASETS.TRAIN = ("category_train",)
# cfg.DATASETS.TEST = ()
# cfg.DATALOADER.NUM_WORKERS = 2
# cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("Misc/mask_rcnn_R_50_FPN_3x_gn.yaml")
# cfg.SOLVER.IMS_PER_BATCH = 2
# cfg.SOLVER.BASE_LR = 0.00025
# cfg.SOLVER.MAX_ITER = 1000
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 2

# os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
# trainer = DefaultTrainer(cfg) 
# trainer.resume_or_load(resume=False)

# trainer.train()

cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.55
cfg.DATASETS.TEST = ("skin_test", )
predictor = DefaultPredictor(cfg)

# test_dataset_dicts = get_data_dicts(data_path+'test', classes)

# for d in random.sample(test_dataset_dicts, 5):
    # img = cv2.imread(d["file_name"])
    # outputs = predictor(img)
    # v = Visualizer(img[:, :, ::-1],
                   # metadata=microcontroller_metadata, 
                   # scale=0.8, 
                   # instance_mode=ColorMode.SEGMENTATION # removes the colors of unsegmented pixels
    # )
    # v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    # print(outputs)
    # plt.figure(figsize = (14, 10))
    # plt.imshow(v.get_image())
    # plt.show()

cam = cv2.VideoCapture(0)
success, image = cam.read()
while success:
    x = datetime.datetime.now()
    current_time = x.strftime("%d%m%Y_%H%M%S")
    filename = '%s.jpeg' % current_time
    predictions = predictor(image)
    v = Visualizer(image[:,:,::-1], metadata=microcontroller_metadata, scale=1, instance_mode=ColorMode.SEGMENTATION)
    output = v.draw_instance_predictions(predictions["instances"].to("cpu"))
        
    cv2.imshow("result", output.get_image()[:,:,::-1])
    if(len(predictions.get("instances").pred_classes) != 0):
        print(0 in predictions.get("instances").pred_classes)
        cv2.imwrite("result\image-"+filename, output.get_image()[:,:,::-1])
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    success, image = cam.read()