from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .forms import UploadForm
from .ml_service import get_service
from PIL import Image
import io, uuid

PLANT_CONF_THRESHOLD = 0.60
HIGH_CONF_THRESHOLD  = 0.85
INFER_CAP_SECONDS    = 3.0   # 0s -> 100% fast; >=3s -> 0%

def _pct(x):
    try: return f"{float(x)*100:.1f}%"
    except Exception: return "—"

def _pct_num0to100(x):
    try:
        v = max(0.0, min(100.0, float(x)*100.0))
        return int(round(v))
    except Exception:
        return 0

def _speed_pct(infer_secs):
    try: s = float(infer_secs)
    except Exception: return 0
    pct = (INFER_CAP_SECONDS - s) / INFER_CAP_SECONDS
    pct = max(0.0, min(1.0, pct))
    return int(round(pct * 100))

def _split_combined(name):
    raw = (name or "").strip().strip("_")
    a, b = raw, ""
    if "___" in raw:
        a, b = raw.split("___", 1)
    elif "__" in raw:
        a, b = raw.split("__", 1)
    crop = a.replace("_", " ").strip()
    state = b.replace("_", " ").strip()
    if "(" in crop and ")" in crop:
        inner = crop[crop.find("(")+1:crop.find(")")].strip()
        if inner: crop = inner
    crop  = " ".join(w.capitalize() for w in crop.split())
    state = " ".join(w.capitalize() for w in state.split())
    return crop, state

def upload_view(request):
    form = UploadForm()
    return render(request, "core/upload.html", {"form": form})

def predict_view(request):
    if request.method != "POST":
        return redirect("upload")

    form = UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "core/upload.html", {"form": form, "error": "Please choose a valid image."})

    img_file = form.cleaned_data["image"]
    target_crop  = form.cleaned_data.get("target_crop") or ""
    target_state = form.cleaned_data.get("target_state") or ""

    # Save for display
    uid = uuid.uuid4().hex
    ext = (img_file.name.split(".")[-1] or "jpg").lower()
    rel_path = f"uploads/{uid}.{ext}"
    saved_path = default_storage.save(rel_path, ContentFile(img_file.read()))
    image_url = settings.MEDIA_URL + saved_path

    # PIL for inference
    with default_storage.open(saved_path, "rb") as fh:
        pil = Image.open(io.BytesIO(fh.read())).convert("RGB")

    svc = get_service()
    raw = svc.predict_all(pil, target_crop or None, target_state or None)

    # Per-model friendly summary
    friendly = []
    for model_name, data in (raw or {}).items():
        if not data:
            friendly.append({"model": model_name, "present": False, "note": "Model not loaded"})
            continue

        if "crop" in data and "state" in data:
            crop = data["crop"]["top1_name"]
            state = data["state"]["top1_name"]
            conf = float(data["crop"]["top1_conf"])
            pretty_label = f'{" ".join(w.capitalize() for w in crop.split("_"))} — {" ".join(w.capitalize() for w in state.split("_"))}'
        else:
            top1 = data.get("top1_name", "")
            crop, state = _split_combined(top1)
            conf = float(data.get("top1_conf", 0.0))
            pretty_label = f"{crop}" + (f" — {state}" if state else "")

        infer_secs = data.get("infer_secs", 0.0)
        conf_pct_num  = _pct_num0to100(conf)
        infer_pct_num = _speed_pct(infer_secs)

        conf_class = "bar-green" if conf >= HIGH_CONF_THRESHOLD else ("bar-amber" if conf >= PLANT_CONF_THRESHOLD else "bar-red")
        infer_class = "bar-green" if infer_pct_num >= 67 else ("bar-amber" if infer_pct_num >= 34 else "bar-red")

        friendly.append({
            "model": model_name, "present": True, "label": pretty_label.strip() or "Unknown",
            "crop": crop, "state": state,
            "conf": conf, "conf_pct": _pct(conf), "conf_pct_num": conf_pct_num, "conf_class": conf_class,
            "infer_secs": infer_secs, "infer_pct_num": infer_pct_num, "infer_class": infer_class,
            "device": data.get("device", "—"),
            "prep_secs": data.get("prep_secs"),
            "debug": data,
        })

    # Consensus for verdict
    crops = {}
    for it in friendly:
        if not it.get("present"): continue
        key = (it["crop"] or "").lower()
        crops.setdefault(key, {"count": 0, "best": it})
        crops[key]["count"] += 1
        if it["conf"] > crops[key]["best"]["conf"]:
            crops[key]["best"] = it
    consensus = None
    if crops:
        consensus = sorted(crops.items(), key=lambda kv: (kv[1]["count"], kv[1]["best"]["conf"]), reverse=True)[0][1]["best"]

    verdict = {}
    if consensus and consensus["conf"] >= PLANT_CONF_THRESHOLD:
        verdict["status"] = "ok"
        verdict["title"] = f"This looks like: {consensus['label']}"
        verdict["subtitle"] = f"Confidence {consensus['conf_pct']} (from {consensus['model']})"
    else:
        verdict["status"] = "warn"
        verdict["title"] = "Not sure this is a supported plant"
        verdict["subtitle"] = "Try a clearer image of a single leaf/fruit. Confidence is low."

    ctx = {
        "image_url": image_url,
        "verdict": verdict,
        "models": friendly,
        "threshold": int(PLANT_CONF_THRESHOLD * 100),
        "target_crop": target_crop,
        "target_state": target_state,
        "raw": raw,
    }
    return render(request, "core/result.html", ctx)
