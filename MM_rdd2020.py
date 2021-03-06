# -*- coding: utf-8 -*-
"""
Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n33kxxWuEnr_WiMueTAkF5FL2MeEqsiI

# MMDetection Tutorial
## Install MMDetection


# install dependencies: 
!pip install pyyaml==5.1 pycocotools>=2.0.1
# Check GCC version
!gcc --version
# Check nvcc version
!nvcc -V
# Check nvidia devices
!nvidia-smi

# install dependencies: (use cu101 because colab has CUDA 10.1)
! pip install -U torch==1.5.1+cu101 torchvision==0.6.1+cu101 -f https://download.pytorch.org/whl/torch_stable.html

# install mmcv-full thus we could use CUDA operators
! pip install mmcv-full==latest+torch1.5.0+cu101 -f https://openmmlab.oss-accelerate.aliyuncs.com/mmcv/dist/index.html

# Install mmdetection
! rm -rf mmdetection
! git clone https://github.com/open-mmlab/mmdetection.git
# %cd mmdetection

! pip install -e .

# install Pillow 7.0.0 back in order to avoid bug in colab
! pip install Pillow==7.0.0

# Download model file 
mkdir checkpoints
wget -c https://open-mmlab.s3.ap-northeast-2.amazonaws.com/mmdetection/v2.0/mask_rcnn/mask_rcnn_r50_caffe_fpn_mstrain-poly_3x_coco/mask_rcnn_r50_caffe_fpn_mstrain-poly_3x_coco_bbox_mAP-0.408__segm_mAP-0.37_20200504_163245-42aa3d00.pth \
     -O checkpoints/mask_rcnn_r50_caffe_fpn_mstrain-poly_3x_coco_bbox_mAP-0.408__segm_mAP-0.37_20200504_163245-42aa3d00.pth

""" 

# Point to the dataset - https://github.com/sekilab/RoadDamageDetector/blob/master/RoadDamageDatasetTutorial.ipynb
MMDETECTION_ROOT    = "/home/rahul/workspace/tor/open-mmlab/mmdetection/"
DETECTRON2_DATASETS = "/media/rahul/Karmic/data/"
ROADDAMAGE_DATASET  = DETECTRON2_DATASETS+"rdd2020/"


# Check Pytorch installation
import torch, torchvision
print(torch.__version__, torch.cuda.is_available())

# Check MMDetection installation
import mmdet
print(mmdet.__version__)

# Check mmcv installation
from mmcv.ops import get_compiling_cuda_version, get_compiler_version
print(get_compiling_cuda_version())
print(get_compiler_version())

## Perform inference with a MMDet detector
## MMDetection already provides high level APIs to do inference and training.
"""## Train a detector on customized dataset

To train a new detector, there are usually three things to do:
1. Support a new dataset
2. Modify the config
3. Train a new detector

### Support a new dataset

There are three ways to support a new dataset in MMDetection: 
  1. reorganize the dataset into COCO format.
  2. reorganize the dataset into a middle format.
  3. implement a new dataset.

Usually we recommend to use the first two methods which are usually easier than the third.

In this tutorial, we gives an example that converting the data into the format of existing datasets like COCO, VOC, etc. Other methods and more advanced usages can be found in the [doc](https://mmdetection.readthedocs.io/en/latest/tutorials/new_dataset.html#).
"""

# Let's take a look at the dataset image

import copy
import os.path as osp
import os

import mmcv
import numpy as np
import matplotlib.pyplot as plt
from xml.etree import ElementTree
from xml.dom import minidom

from mmdet.datasets.builder import DATASETS
from mmdet.datasets.custom import CustomDataset

import data_rdd


"""According to the RDD documentation. We need to read annotations of each image and convert them into middle format MMDetection accept is as below"""
@DATASETS.register_module()
class RddDataset(CustomDataset):

    CLASSES_super = ("D00", "D01", "D10", "D11", "D20", "D40", "D43", "D44", "D50", "D0w0")
    CLASSES = ("D00", "D10", "D20", "D40")
    DATA_SUPERCATEGORY = ("Czech", "India", "Japan")

    def load_annotations(self, ann_file):
        image_id_count = 0
        cat2label = {k: i for i, k in enumerate(self.CLASSES)}
        # load image list from file #image_list = mmcv.list_from_file(self.ann_file)
        data_infos = []
        # convert annotations to middle format
        # for idx, regions_data in enumerate(self.DATA_SUPERCATEGORY):
        regions_data = "../" # Doing this one country at a time as per the configuration
        ann_path = os.path.join(self.data_root, regions_data, "annotations/xmls")
        img_path = os.path.join(self.data_root, regions_data, "images")
        print("\tLoading ", " - ", img_path, " - ", ann_path)
        # list annotations/xml dir and for each annotation load the data
        image_list = [filename for filename in os.listdir(img_path) if filename.endswith('.jpg')]
        for img_id, img_filename in enumerate(image_list):
            image_id_count = image_id_count + 1
            filename = os.path.join(img_path, img_filename)
            image = mmcv.imread(filename)
            height, width = image.shape[:2]
            data_info = dict(filename=img_filename, width=width, height=height)
            # Load image annotations xml
            ann_filename = img_filename.split(".")[0] + ".xml"
            if os.path.isfile(os.path.join(ann_path, ann_filename)):
                infile_xml = open(os.path.join(ann_path, ann_filename))
                tree = ElementTree.parse(infile_xml)
                root = tree.getroot()
                gt_bboxes = []
                gt_labels = []
                gt_bboxes_ignore = []
                gt_labels_ignore = []
                for obj in root.iter('object'):
                    bbox_name, xmlbox = obj.find('name').text, obj.find('bndbox')
                    xmin, xmax = np.float(xmlbox.find('xmin').text), np.float(xmlbox.find('xmax').text)
                    ymin, ymax = np.float(xmlbox.find('ymin').text), np.float(xmlbox.find('ymax').text)
                    bbox = [xmin, ymin, xmax, ymax]       # (x0, y0, x1, y1)                         
                    if bbox_name in cat2label:
                        gt_labels.append(cat2label[bbox_name])
                        gt_bboxes.append(bbox)
                    else:
                        gt_labels_ignore.append(-1)
                        gt_bboxes_ignore.append(bbox)

            data_anno = dict(
                bboxes=np.array(gt_bboxes, dtype=np.float32).reshape(-1, 4),
                labels=np.array(gt_labels, dtype=np.long),
                bboxes_ignore=np.array(gt_bboxes_ignore,
                                        dtype=np.float32).reshape(-1, 4),
                labels_ignore=np.array(gt_labels_ignore, dtype=np.long))

            data_info.update(ann=data_anno)
            data_infos.append(data_info)
        return data_infos

"""
### Modify the config
In the next step, we need to modify the config for the training.
To accelerate the process, we finetune a detector using a pre-trained detector.
"""
from mmcv import Config
from mmdet.apis import set_random_seed

def get_train_config(country = None):
    cfg = Config.fromfile(MMDETECTION_ROOT+'/configs/faster_rcnn/faster_rcnn_r50_caffe_fpn_mstrain_1x_coco.py')
    """Given a config that trains a Faster R-CNN on COCO dataset, we need to modify some values to use it for training Faster R-CNN on KITTI dataset."""
    
    # Modify dataset type and path
    cfg.dataset_type = 'RddDataset'
    #cfg.data_root = '/content/gdrive/My Drive/Projects/Windspect/code/data/rdd2020/'

    cfg.data.test.type = 'RddDataset'
    cfg.data.test.data_root = ROADDAMAGE_DATASET+'ltest/'+country+'/images'
    cfg.data.test.ann_file = ''
    cfg.data.test.img_prefix = ''

    cfg.data.train.type = 'RddDataset'
    cfg.data.train.data_root = ROADDAMAGE_DATASET+'ltrain/'+country+'/images'
    cfg.data.train.ann_file = ''
    cfg.data.train.img_prefix = ''

    cfg.data.val.type = 'RddDataset'
    cfg.data.val.data_root = ROADDAMAGE_DATASET+'lval/'+country+'/images'
    cfg.data.val.ann_file = ''
    cfg.data.val.img_prefix = ''

    # modify num classes of the model in box head
    cfg.model.roi_head.bbox_head.num_classes = len(data_rdd.RDD_DAMAGE_CATEGORIES)
    # We can still use the pre-trained Mask RCNN model though we do not need to use the mask branch
    cfg.load_from = MMDETECTION_ROOT+'/checkpoints/mask_rcnn_r50_caffe_fpn_mstrain-poly_3x_coco_bbox_mAP-0.408__segm_mAP-0.37_20200504_163245-42aa3d00.pth'
    # Set up working dir to save files and logs.
    cfg.work_dir = './output/run_mm_1/'

    # The original learning rate (LR) is set for 8-GPU training.
    # We divide it by 8 since we only use one GPU.
    cfg.optimizer.lr = 0.02 / 8
    cfg.lr_config.warmup = None
    cfg.log_config.interval = 10
    # Change the evaluation metric since we use customized dataset.
    cfg.evaluation.metric = 'mAP'
    # We can set the evaluation interval to reduce the evaluation times
    cfg.evaluation.interval = 12
    # We can set the checkpoint saving interval to reduce the storage cost
    cfg.checkpoint_config.interval = 12

    # Set seed thus the results are more reproducible
    cfg.seed = 0
    set_random_seed(0, deterministic=False)
    cfg.gpu_ids = range(1)

    cfg.total_epochs = 50
    return cfg 


cfg = get_train_config(country = "Japan")

# We can initialize the logger for training and have a look
# at the final config used for training
print(f'Config:\n{cfg.pretty_text}')

"""
### Train a new detector
Finally, lets initialize the dataset and detector, then train a new detector!
"""

from mmdet.datasets import build_dataset
from mmdet.models import build_detector
from mmdet.apis import train_detector


print("\nConfig: ", cfg.data.train)

# Build dataset
datasets = [build_dataset(cfg.data.train)]

print(datasets)

# Build the detector
model = build_detector(cfg.model, train_cfg=cfg.train_cfg, test_cfg=cfg.test_cfg)
# Add an attribute for visualization convenience
model.CLASSES = datasets[0].CLASSES

# Create work_dir
mmcv.mkdir_or_exist(osp.abspath(cfg.work_dir))
train_detector(model, datasets, cfg, distributed=False, validate=True)

"""### Understand the log
From the log, we can have a basic understanding the training process and know how well the detector is trained.

Firstly, the ResNet-50 backbone pre-trained on ImageNet is loaded, this is a common practice since training from scratch is more cost. The log shows that all the weights of the ResNet-50 backbone are loaded except the `conv1.bias`, which has been merged into `conv.weights`.

Second, since the dataset we are using is small, we loaded a Mask R-CNN model and finetune it for detection. Because the detector we actually using is Faster R-CNN, the weights in mask branch, e.g. `roi_head.mask_head`, are `unexpected key in source state_dict` and not loaded.
The original Mask R-CNN is trained on COCO dataset which contains 80 classes but KITTI Tiny dataset only have 3 classes. Therefore, the last FC layer of the pre-trained Mask R-CNN for classification has different weight shape and is not used.

Third, after training, the detector is evaluated by the default VOC-style evaluation. The results show that the detector achieves 54.1 mAP on the val dataset,
 not bad!

## Test the trained detector

After finetuning the detector, let's visualize the prediction results!
"""
from mmdet.apis import inference_detector, init_detector, show_result_pyplot


def get_infer_model():
    work_dir = './output/run_mm_1/'
    config_file = MMDETECTION_ROOT+'/configs/faster_rcnn/faster_rcnn_r50_caffe_fpn_mstrain_1x_coco.py'
    """Given a config that trains a Faster R-CNN on COCO dataset, we need to modify some values to use it for training Faster R-CNN on KITTI dataset."""
    checkpoint_file = work_dir+"epoch_final.pth"
    model = init_detector(config_file, checkpoint_file, device='cuda:1')
    return model
    
model = get_infer_model()

# Examples
img = mmcv.imread(ROADDAMAGE_DATASET+"/val/India/images/India_000005.jpg")
result = inference_detector(model, img)
show_result_pyplot(model, img, result)
print(result)



"""
# Generate submission format result for RDD2020
def format_submission_result(image_meta, predictions):
  boxes = predictions.pred_boxes.tensor.numpy() if predictions.has("pred_boxes") else None
  scores = predictions.scores.numpy() if predictions.has("scores") else None
  classes = predictions.pred_classes.numpy() if predictions.has("pred_classes") else None
  if len(classes) > 0:
    formatted_result = [image_meta["image_name"]]
    for (cls, scr, bbx) in zip(classes, scores, boxes):
      (x_min, y_min, x_max, y_max) = bbx
      formatted_result += [str(int(cls))]                                        # Class Index Label
      formatted_result += [str(int(x_min)), str(int(y_min)), str(int(x_max)), str(int(y_max))]  # (x_min, y_min, x_max, y_max)
    return formatted_result
  return None

def generate_results():
  results = []
  for idx, d in enumerate(dataset_test_submission_dicts):
    im = cv2.imread(d["file_name"])
    outputs = predictor(im)
    formatted_result = format_submission_result(d, outputs["instances"].to("cpu"))
    if formatted_result is not None:
      out_item = ' '.join(formatted_result)
      #print(idx,"\t ", out_item)
      results.append(out_item)
  return results

results = generate_results()

def write_results_to_file():
    with open('hal_submission_rdd2020.txt', 'w') as f:
      f.writelines("%s\n" % line for line in results)
write_results_to_file()
"""