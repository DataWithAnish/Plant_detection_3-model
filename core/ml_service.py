import threading, os, tempfile, sys
from django.conf import settings
from importlib import import_module
_lock = threading.RLock()
_service_singleton = None
class MLService:
    def __init__(self):
        self._loaded = False
        self.yolo = None
        self.xception = None
        self.resnet = None
    def warm(self):
        with _lock:
            if self._loaded:
                return
            code_dir = str(settings.INFERENCE_CODE_DIR)
            if code_dir not in sys.path:
                sys.path.insert(0, code_dir)
            m = import_module("plant_classification_app_3model")
            self.yolo = m.YoloClassifier(m.YOLO_MODEL_PATH)
            self.xception = m.XceptionClassifier(m.XCEPTION_TFLITE, m.XCEPTION_LABELS_CROP, m.XCEPTION_LABELS_STATE)
            self.resnet = m.ResNetClassifier(m.RESNET50_KERAS_MODEL, m.RESNET50_CLASS_CSV, m.RESNET_CLASSES_JSON)
            self._loaded = True
    def predict_all(self, pil_image, target_crop=None, target_state=None):
        if not self._loaded:
            self.warm()
        with _lock:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                pil_image.save(tmp.name)
                image_path = tmp.name
            try:
                y = self.yolo.predict(image_path, target_crop, target_state) if self.yolo else None
                x = self.xception.predict(image_path, target_crop, target_state) if self.xception else None
                r = self.resnet.predict(image_path, target_crop, target_state) if self.resnet else None
                return {"YOLOv11": y, "Xception": x, "ResNet": r}
            finally:
                try: os.remove(image_path)
                except Exception: pass
def get_service():
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = MLService()
    return _service_singleton
