FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgl1 libglib2.0-0 libjpeg62-turbo libpng16-16 libtiff5 \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements-merged.txt || \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p scripts && \
    bash -lc 'cat > scripts/fetch_models.sh << "SH"\n\
#!/usr/bin/env bash\n\
set -euo pipefail\n\
BASE=\"inference_code/models\"\n\
mkdir -p \"$BASE/yolo\" \"$BASE/xception\" \"$BASE/resnet50\"\n\
dl(){ local url=\"${1:-}\" out=\"${2}\"; if [ -n \"$url\" ] && [ ! -f \"$out\" ]; then echo \"Downloading: $out\"; mkdir -p \"$(dirname \"$out\")\"; wget -q --show-progress -O \"$out\" \"$url\"; fi; }\n\
dl \"${YOLO_URL:-}\"                  \"$BASE/yolo/best.pt\"\n\
dl \"${XCEPTION_TFLITE_URL:-}\"       \"$BASE/xception/xception_pv1.tflite\"\n\
dl \"${XCEPTION_LABELS_CROP_URL:-}\"  \"$BASE/xception/labels_crop.txt\"\n\
dl \"${XCEPTION_LABELS_STATE_URL:-}\" \"$BASE/xception/labels_state.txt\"\n\
dl \"${RESNET_H5_URL:-}\"             \"$BASE/resnet50/resnet50_stage2_conv5.h5\"\n\
dl \"${RESNET_CSV_URL:-}\"            \"$BASE/resnet50/class_index.csv\"\n\
dl \"${RESNET_JSON_URL:-}\"           \"$BASE/resnet50/class_names.json\"\n\
echo \"Model files present (if any):\"; find \"$BASE\" -maxdepth 2 -type f -printf \"%P\\n\" 2>/dev/null || true\n\
missing=0\n\
[ -f \"$BASE/yolo/best.pt\" ] || { echo \"WARN: YOLO weight missing\"; missing=1; }\n\
[ -f \"$BASE/xception/xception_pv1.tflite\" ] || { echo \"WARN: Xception TFLite missing\"; missing=1; }\n\
[ -f \"$BASE/xception/labels_crop.txt\" ] || { echo \"WARN: labels_crop.txt missing\"; missing=1; }\n\
[ -f \"$BASE/xception/labels_state.txt\" ] || { echo \"WARN: labels_state.txt missing\"; missing=1; }\n\
[ -f \"$BASE/resnet50/resnet50_stage2_conv5.h5\" ] || { echo \"WARN: ResNet .h5 missing\"; missing=1; }\n\
if [ ! -f \"$BASE/resnet50/class_index.csv\" ] && [ ! -f \"$BASE/resnet50/class_names.json\" ]; then echo \"WARN: No ResNet class map (csv/json)\"; missing=1; fi\n\
if [ \"$missing\" -ne 0 ]; then echo \"Some models/labels are missing. App will start but predictions may fail.\" >&2; fi\n\
SH' && chmod +x scripts/fetch_models.sh

ENV DJANGO_SETTINGS_MODULE=plantweb.settings
ENV PORT=8000
EXPOSE 8000

CMD ["bash", "-lc", "bash scripts/fetch_models.sh && gunicorn plantweb.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
