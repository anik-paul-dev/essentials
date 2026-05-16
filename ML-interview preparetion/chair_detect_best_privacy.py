
# Cell-1
# Installation Cell (No changes needed, but run this first and restart runtime as prompted)
!pip install ultralytics --quiet
!pip install torch torchvision torchaudio --quiet
!pip install gtts --quiet
!pip install playsound --quiet
!pip install speechrecognition --quiet
!apt install -y libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg -qq
!pip install pyaudio --quiet
!pip install filterpy --quiet
!pip install transformers --quiet

!pip uninstall -y mediapipe opencv-python opencv-contrib-python -q
!pip cache purge -q
!pip install mediapipe==0.10.14 --no-cache-dir --force-reinstall --quiet
!pip install opencv-python-headless==4.10.0.84 --no-cache-dir --force-reinstall --quiet

print("MediaPipe downgrade finished. RESTART RUNTIME NOW (Runtime → Restart runtime), then run the next cells.")

"""Cell-2"""

# Cell-2
import cv2
import numpy as np
import torch
import mediapipe as mp
from ultralytics import YOLO
from gtts import gTTS
import os
import time
import speech_recognition as sr
from IPython.display import display, Javascript, Audio, clear_output, Image, HTML, Video
from google.colab.output import eval_js
from base64 import b64decode, b64encode
import requests
import io
import PIL
import html
from filterpy.kalman import KalmanFilter
from scipy.spatial.distance import euclidean
from transformers import pipeline

from google.colab import drive
drive.mount('/content/drive')

"""Cell-3"""

# Cell-3
model_yolo = YOLO('yolov8l-seg.pt')  # Large model for better chair detection from side, left, right, back and partial views
midas = torch.hub.load('intel-isl/MiDaS', 'DPT_Large')
midas.eval()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
midas.to(device)
midas_transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
transform = midas_transforms.dpt_transform
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.6, model_complexity=2)
mp_face = mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.6)
nlp_guidance = pipeline("text-generation", model="gpt2", device=0 if torch.cuda.is_available() else -1)
# Globals for perfect audio-frame synchronization
SPEAK_COOLDOWN = 7.0
last_guidance_time = 0.0
last_nearest_track_id = -1
last_empty_count = -1
print("Models loaded (upgraded to yolov8l-seg for full chair detection from all angles). MediaPipe version:", mp.__version__)

"""Cell-4"""

# Cell-4 (bbox slicing & mask resize for video frames)
def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area != 0 else 0

def apply_mask(frame, bbox, mask):
    if mask is None:
        x1, y1, x2, y2 = map(int, bbox)
        return frame[y1:y2, x1:x2]

    # Use float bbox for accurate slicing (no int loss)
    x1, y1, x2, y2 = bbox
    crop_h = int(y2 - y1)
    crop_w = int(x2 - x1)

    if crop_h <= 0 or crop_w <= 0:
        return np.zeros((1,1,3), dtype=np.uint8)  # empty fallback

    # Crop with float → int conversion carefully
    crop = frame[int(y1):int(y2), int(x1):int(x2)].copy()

    # Resize mask with exact target size + INTER_LINEAR for smooth
    mask_resized = cv2.resize(mask.astype(np.float32), (crop_w, crop_h), interpolation=cv2.INTER_LINEAR)

    # Safety: if shapes still mismatch by 1 px (rare float error), pad/trim
    if mask_resized.shape[:2] != crop.shape[:2]:
        mh, mw = mask_resized.shape[:2]
        ch, cw = crop.shape[:2]
        pad_h = ch - mh
        pad_w = cw - mw
        if pad_h > 0 or pad_w > 0:
            mask_resized = cv2.copyMakeBorder(mask_resized, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=0.0)
        elif pad_h < 0 or pad_w < 0:
            mask_resized = mask_resized[:ch, :cw]

    # Now safe to apply
    crop[mask_resized < 0.5] = 0
    return crop

"""Cell-5"""

# Cell-5 (occupancy calculation criteria) - COMPLETELY NEW APPROACH: PURE RECTANGULAR/BOX-SHAPE OVERLAP
# Uses only full rectangular bounding box overlap between chair box and person box
# No mask, no contours, no seat-area percentage — exactly rectangular/square box shape as you asked
# If person box overlaps chair box at all → occupied (works for side/back/partial views)
# All keys, prints, contours drawing (now rectangular in Cell-10), tracking, distance, speak() unchanged
def detect_occupancy(frame, results):
    chairs = []
    persons = []
    for result in results:
        if result.masks is None:
            continue
        boxes = result.boxes
        masks = result.masks.data.cpu().numpy()
        for i, box in enumerate(boxes):
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            if conf < 0.60:
                continue
            xyxy = box.xyxy[0].cpu().numpy()
            if result.names[cls] == 'chair':
                chairs.append({'bbox': xyxy, 'mask': masks[i], 'occupied': False, 'conf_chair': conf})
            elif result.names[cls] == 'person':
                persons.append({'bbox': xyxy, 'conf_person': conf})
    for chair in chairs:
        chair_bbox = chair['bbox']
        max_overlap = 0
        best_person_bbox = None
        best_iou = 0.0
        best_conf_person = 0.0
        for person in persons:
            # PURE RECTANGULAR BOX-SHAPE OVERLAP (full chair box)
            effective_iou = calculate_iou(chair_bbox, person['bbox'])
            if effective_iou > 0.08:
                overlap = effective_iou * (person['conf_person'] + chair['conf_chair']) / 2
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_person_bbox = person['bbox'].copy()
                    best_iou = effective_iou
                    best_conf_person = person['conf_person']
        chair['max_overlap_score'] = max_overlap
        chair['overlapping_person_bbox'] = best_person_bbox
        chair['iou_value'] = best_iou
        chair['conf_person_used'] = best_conf_person
        chair['hips_z'] = None
        chair['pose_detected'] = False
        chair['occupied'] = False
        # PRIMARY: rectangular box overlap decides
        if max_overlap > 0.22:
            chair['occupied'] = True
        # SECONDARY: pose only for confirmation (not required)
        if max_overlap > 0.15:
            chair_crop = apply_mask(frame, chair_bbox, chair['mask'])
            if chair_crop.size > 0:
                pose_results = pose.process(cv2.cvtColor(chair_crop, cv2.COLOR_BGR2RGB))
                if pose_results.pose_landmarks:
                    chair['pose_detected'] = True
                    left_hip = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
                    right_hip = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
                    hips_avg_z = (left_hip.z + right_hip.z) / 2
                    chair['hips_z'] = hips_avg_z
                    if hips_avg_z < -0.05:
                        chair['occupied'] = True
    occupied_count = sum(1 for c in chairs if c['occupied'])
    empty_count = len(chairs) - occupied_count
    return chairs, occupied_count, empty_count

"""Cell-6"""

# Cell-6 (distance measure)
def estimate_distance(frame, chairs):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    input_batch = transform(img).to(device)
    with torch.no_grad():
        prediction = midas(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
    depth_map = prediction.cpu().numpy()
    def calibrate(raw):
        return max(0.5, 22.0 / (raw + 14.0))
    for chair in chairs:
        bbox = chair['bbox']
        mask = chair.get('mask')
        x1 = max(0, int(bbox[0]))
        y1 = max(0, int(bbox[1]))
        x2 = min(depth_map.shape[1], int(bbox[2]))
        y2 = min(depth_map.shape[0], int(bbox[3]))
        if y2 <= y1 or x2 <= x1:
            chair['distance'] = 5.0
            chair['raw_median'] = None
            chair['seat_pixels'] = 0
            continue
        depth_crop = depth_map[y1:y2, x1:x2]
        if mask is not None:
            h, w = y2 - y1, x2 - x1
            mask_resized = cv2.resize(mask.astype(np.float32), (w, h))
            seat_start = int(0.6 * h)
            valid_mask = mask_resized[seat_start:, :] > 0.5
            valid = depth_crop[seat_start:, :][valid_mask]
            if len(valid) > 15:
                med = np.median(valid)
                chair['distance'] = calibrate(med)
                chair['raw_median'] = med
                chair['seat_pixels'] = len(valid)
                continue
        if depth_crop.size > 0:
            med = np.median(depth_crop)
            chair['distance'] = calibrate(med)
            chair['raw_median'] = med
            chair['seat_pixels'] = depth_crop.size
        else:
            chair['raw_median'] = None
            chair['seat_pixels'] = 0
    return chairs

"""Cell-7"""

# Cell-7 (chair tracking)
class ChairTracker:
    def __init__(self):
        self.trackers = {}
        self.next_id = 0
        self.max_match_dist = 60
    def update(self, detections):
        new_detections = []
        centers = [((d['bbox'][0]+d['bbox'][2])/2, (d['bbox'][1]+d['bbox'][3])/2) for d in detections]
        for det, center in zip(detections, centers):
            matched = False
            for tid, kf in list(self.trackers.items()):
                pred = kf.x[:2].flatten()
                if euclidean(pred, center) < self.max_match_dist:
                    det['predicted_center'] = pred.tolist()
                    kf.update(np.array([[center[0]], [center[1]]]))
                    det['track_id'] = tid
                    matched = True
                    break
            if not matched:
                kf = KalmanFilter(dim_x=4, dim_z=2)
                kf.F = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]])
                kf.H = np.array([[1,0,0,0],[0,1,0,0]])
                kf.x = np.array([[center[0]], [center[1]], [0], [0]])
                kf.P *= 1000.0
                kf.R = 8
                kf.Q = np.eye(4) * 0.1
                self.trackers[self.next_id] = kf
                det['track_id'] = self.next_id
                det['predicted_center'] = center
                self.next_id += 1
            new_detections.append(det)
        to_remove = []
        for tid, kf in self.trackers.items():
            kf.predict()
            if tid not in [d.get('track_id') for d in new_detections]:
                if kf.P[0,0] > 15000:
                    to_remove.append(tid)
        for tid in to_remove:
            del self.trackers[tid]
        return new_detections
tracker = ChairTracker()

"""Cell-8"""

# Cell-8 (Best Privacy Chair Guidance + speak function + LOCK & NAVIGATE SYSTEM)
# FIXED: Re-anchor by minimum center-distance (200px generous threshold) instead of IoU.
#        IoU fails when camera moves because pixel bbox shifts too much.
#        Center-distance re-anchor correctly finds same physical chair across all camera angles.
# FIXED: frames_out_of_view only increments when NO chair found within distance threshold.
# ALL original: scoring (0.55*dist+0.45*nearby), privacy_msg, FOV=78, obstacles,
#               speak(), is_best flag — COMPLETELY UNCHANGED.

# ─────────────────────────────────────────────────────────────
# speak() — UNCHANGED
# ─────────────────────────────────────────────────────────────
def speak(text):
    if not text.strip():
        return
    tts = gTTS(text=text, lang='en')
    audio_file = "guidance.mp3"
    tts.save(audio_file)
    display(Audio(audio_file, autoplay=True))
    time.sleep(len(text.split()) / 2.3 + 2.0)
    try:
        os.remove(audio_file)
    except:
        pass


# ─────────────────────────────────────────────────────────────
# LOCK STATE
# ─────────────────────────────────────────────────────────────
class LockState:
    def __init__(self):
        self.locked              = False
        self.track_id            = None    # current best-known track_id (updated by re-anchor)
        self.last_bbox           = None    # last known bbox [x1,y1,x2,y2] in pixels
        self.last_center         = None    # last known (cx, cy) in pixels
        self.last_distance       = None
        self.last_angle          = None
        self.last_direction      = None
        self.frames_out_of_view  = 0
        self.last_seen_side      = 'ahead'
        self.sit_confirmed       = False
        self.waiting_conf        = False

    def reset(self):
        self.__init__()

lock_state = LockState()


# ─────────────────────────────────────────────────────────────
# RE-ANCHOR LOCKED CHAIR
#
# Strategy (in priority order):
#   1. Exact track_id match — fastest, works when tracker is stable
#   2. Minimum center-distance match (threshold 200px) — works when
#      camera moves and tracker reassigns track_id. Uses the center
#      of each detected chair bbox vs lock_state.last_center.
#      200px is generous enough for large camera movements at 640x480.
#   3. If nothing within 200px → return None (genuinely out of frame)
#
# When re-anchored via center-distance, track_id is updated so
# next frame uses exact match again (fast path).
# last_bbox and last_center are ONLY updated here when chair is FOUND.
# ─────────────────────────────────────────────────────────────
def reanchor_locked_chair(chairs):
    if not lock_state.locked or lock_state.last_center is None:
        return None

    # ── Fast path: exact track_id ────────────────────────────
    for c in chairs:
        if c.get('track_id') == lock_state.track_id:
            # Update last_center and last_bbox with fresh values
            bx = c['bbox']
            lock_state.last_center = ((bx[0]+bx[2])/2, (bx[1]+bx[3])/2)
            lock_state.last_bbox   = bx
            return c

    # ── Slow path: minimum center-distance (camera moved) ────
    lc = lock_state.last_center
    best_dist  = 200.0   # max pixel distance to consider same chair
    best_chair = None

    for c in chairs:
        bx = c['bbox']
        cx = (bx[0] + bx[2]) / 2
        cy = (bx[1] + bx[3]) / 2
        d  = ((cx - lc[0])**2 + (cy - lc[1])**2) ** 0.5
        if d < best_dist:
            best_dist  = d
            best_chair = c

    if best_chair is not None:
        old_id = lock_state.track_id
        bx     = best_chair['bbox']
        lock_state.track_id   = best_chair.get('track_id')
        lock_state.last_center = ((bx[0]+bx[2])/2, (bx[1]+bx[3])/2)
        lock_state.last_bbox   = bx
        print(f"[LOCK RE-ANCHOR] track_id {old_id}→{lock_state.track_id} "
              f"center_dist={best_dist:.1f}px")
        return best_chair

    # ── Not found within threshold — genuinely out of frame ──
    return None


# ─────────────────────────────────────────────────────────────
# CONFIRMATION via eval_js polling
# Same proven mechanism as video_frame() in Cell-9.
# ─────────────────────────────────────────────────────────────
def ask_confirmation(prompt_text, chair_dist=None, chair_dir=None):
    """Returns True=YES lock, False=NO skip."""
    lock_state.waiting_conf = True

    dist_str = f"{chair_dist:.1f}m" if chair_dist else "?"
    dir_str  = chair_dir or "ahead"

    js_overlay = ("""
    window.__chairLockAnswer = null;
    (function() {
      var old = document.getElementById('__chairLockOverlay');
      if (old) old.remove();
      var overlay = document.createElement('div');
      overlay.id = '__chairLockOverlay';
      overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;"""
      """z-index:2147483647;background:rgba(0,0,0,0.82);display:flex;"""
      """align-items:center;justify-content:center;font-family:monospace;';
      var box = document.createElement('div');
      box.style.cssText = 'background:#0d1b2a;border:3px solid #00e5ff;border-radius:18px;"""
      """padding:40px 52px;text-align:center;max-width:540px;width:90%;"""
      """box-shadow:0 0 50px rgba(0,229,255,0.4);';
      box.innerHTML = """
        """'<div style="font-size:24px;color:#00e5ff;font-weight:bold;margin-bottom:10px;">"""
        """&#x1F512; LOCK BEST CHAIR?</div>'"""
        """+'<div style="font-size:15px;color:#ddd;margin-bottom:6px;">PROMPT_TEXT</div>'"""
        """+'<div style="font-size:14px;color:#aaa;margin-bottom:26px;">"""
        """Distance: DIST_STR &nbsp;|&nbsp; Direction: DIR_STR</div>'"""
        """+'<div style="display:flex;gap:28px;justify-content:center;">'"""
        """+'<button id="__yesBtn" style="background:#00c853;color:#fff;border:none;"""
        """border-radius:12px;padding:16px 50px;font-size:22px;font-weight:bold;"""
        """cursor:pointer;">&#x2705; YES</button>'"""
        """+'<button id="__noBtn" style="background:#d50000;color:#fff;border:none;"""
        """border-radius:12px;padding:16px 50px;font-size:22px;font-weight:bold;"""
        """cursor:pointer;">&#x274C; NO</button>'"""
        """+'</div>'"""
        """+'<div style="margin-top:18px;font-size:12px;color:#777;">"""
        """Click YES or NO &bull; or say yes / no</div>';"""
      """overlay.appendChild(box);
      document.body.appendChild(overlay);
      document.getElementById('__yesBtn').onclick=function(){"""
        """window.__chairLockAnswer='yes';overlay.style.display='none';};
      document.getElementById('__noBtn').onclick=function(){"""
        """window.__chairLockAnswer='no';overlay.style.display='none';};
    })();
    """).replace('PROMPT_TEXT', html.escape(prompt_text)) \
       .replace('DIST_STR',    dist_str) \
       .replace('DIR_STR',     dir_str)

    display(Javascript(js_overlay))

    speak_text = f"{prompt_text} It is {dist_str} {dir_str}. Say yes to lock or no to skip."
    speak(speak_text)

    # ── Voice (fails silently on Colab cloud — no mic device) ──
    voice_answer = None
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio_data = recognizer.listen(source, timeout=3, phrase_time_limit=3)
        heard = recognizer.recognize_google(audio_data).lower()
        print(f"[Voice heard]: '{heard}'")
        if any(w in heard for w in ['yes','yeah','yep','yup','sure']):
            voice_answer = 'yes'
        elif any(w in heard for w in ['no','nope','nah','skip']):
            voice_answer = 'no'
    except Exception as ve:
        print(f"[Voice skipped]: {ve}")

    if voice_answer:
        display(Javascript(
            f"window.__chairLockAnswer='{voice_answer}';"
            "var ov=document.getElementById('__chairLockOverlay');"
            "if(ov) ov.style.display='none';"))
        lock_state.waiting_conf = False
        print(f"[Confirmation-voice]: {'YES' if voice_answer=='yes' else 'NO'}")
        return voice_answer == 'yes'

    # ── Poll JS global — eval_js, same as Cell-9 video_frame ──
    deadline   = time.time() + 30.0
    answer_str = None
    while time.time() < deadline:
        try:
            val = eval_js('window.__chairLockAnswer')
            if val and str(val).lower() in ('yes', 'no'):
                answer_str = str(val).lower()
                break
        except Exception:
            pass
        time.sleep(0.25)

    display(Javascript(
        "var ov=document.getElementById('__chairLockOverlay');"
        "if(ov) ov.style.display='none';"
        "window.__chairLockAnswer=null;"))

    if answer_str is None:
        answer_str = 'no'
        print("[Confirmation timed out — No]")

    lock_state.waiting_conf = False
    print(f"[Confirmation]: {'YES — locking' if answer_str=='yes' else 'NO — skip'}")
    return answer_str == 'yes'


# ─────────────────────────────────────────────────────────────
# SIT CONFIRMATION — same eval_js pattern
# ─────────────────────────────────────────────────────────────
def ask_sit_confirmation():
    js_overlay = ("""
    window.__sitAnswer = null;
    (function() {
      var old = document.getElementById('__sitOverlay');
      if (old) old.remove();
      var overlay = document.createElement('div');
      overlay.id = '__sitOverlay';
      overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;"""
      """z-index:2147483647;background:rgba(0,0,0,0.82);display:flex;"""
      """align-items:center;justify-content:center;font-family:monospace;';
      var box = document.createElement('div');
      box.style.cssText = 'background:#0d2a0d;border:3px solid #69f0ae;border-radius:18px;"""
      """padding:40px 52px;text-align:center;max-width:500px;width:90%;"""
      """box-shadow:0 0 50px rgba(105,240,174,0.4);';
      box.innerHTML = """
        """'<div style="font-size:24px;color:#69f0ae;font-weight:bold;margin-bottom:12px;">"""
        """&#x1FA91; HAVE YOU SAT DOWN?</div>'"""
        """+'<div style="font-size:15px;color:#ddd;margin-bottom:26px;">"""
        """You are very close to the locked chair.<br>Confirm if you have taken your seat.</div>'"""
        """+'<div style="display:flex;gap:28px;justify-content:center;">'"""
        """+'<button id="__sitYes" style="background:#00c853;color:#fff;border:none;"""
        """border-radius:12px;padding:16px 50px;font-size:22px;font-weight:bold;"""
        """cursor:pointer;">&#x2705; YES, SAT</button>'"""
        """+'<button id="__sitNo" style="background:#d50000;color:#fff;border:none;"""
        """border-radius:12px;padding:16px 50px;font-size:22px;font-weight:bold;"""
        """cursor:pointer;">&#x274C; NOT YET</button>'"""
        """+'</div>';"""
      """overlay.appendChild(box);
      document.body.appendChild(overlay);
      document.getElementById('__sitYes').onclick=function(){"""
        """window.__sitAnswer='yes';overlay.style.display='none';};
      document.getElementById('__sitNo').onclick=function(){"""
        """window.__sitAnswer='no';overlay.style.display='none';};
    })();
    """)
    display(Javascript(js_overlay))
    speak("You are very close to the locked chair. Have you sat down? Click YES or say yes.")

    voice_answer = None
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.listen(source, timeout=3, phrase_time_limit=3)
        heard = recognizer.recognize_google(audio_data).lower()
        if any(w in heard for w in ['yes','yeah','yep','sat','done']):
            voice_answer = 'yes'
        elif any(w in heard for w in ['no','nope','not','yet']):
            voice_answer = 'no'
    except:
        pass

    if voice_answer:
        display(Javascript(
            f"window.__sitAnswer='{voice_answer}';"
            "var ov=document.getElementById('__sitOverlay');"
            "if(ov) ov.style.display='none';"))
        return voice_answer == 'yes'

    deadline   = time.time() + 25.0
    answer_str = None
    while time.time() < deadline:
        try:
            val = eval_js('window.__sitAnswer')
            if val and str(val).lower() in ('yes', 'no'):
                answer_str = str(val).lower()
                break
        except Exception:
            pass
        time.sleep(0.25)

    display(Javascript(
        "var ov=document.getElementById('__sitOverlay');"
        "if(ov) ov.style.display='none';"
        "window.__sitAnswer=null;"))

    if answer_str is None:
        answer_str = 'no'
    print(f"[Sit confirmation]: {answer_str.upper()}")
    return answer_str == 'yes'


# ─────────────────────────────────────────────────────────────
# NAVIGATE TO LOCKED CHAIR
# locked_chair: matched chair dict from reanchor, or None.
# ─────────────────────────────────────────────────────────────
def navigate_to_locked(locked_chair, frame_width):
    global lock_state, last_guidance_time

    fov_deg      = 78
    frame_center = frame_width / 2

    # ── Chair NOT in frame ────────────────────────────────────
    if locked_chair is None:
        lock_state.frames_out_of_view += 1
        if lock_state.frames_out_of_view == 1 or lock_state.frames_out_of_view % 15 == 0:
            side = lock_state.last_seen_side or 'ahead'
            turn_msg = ("Move forward" if side == 'ahead'
                        else f"Turn {side}")
            speak(f"Locked chair is out of the camera frame. {turn_msg} to find it.")
            print(f"[LOCK NAV] Out of frame {lock_state.frames_out_of_view}x. Side:{side}")
        return

    # ── Chair visible ─────────────────────────────────────────
    lock_state.frames_out_of_view = 0
    bx       = locked_chair['bbox']
    center_x = (bx[0] + bx[2]) / 2

    rel = center_x / frame_width
    lock_state.last_seen_side = ('left' if rel < 0.38
                                  else ('right' if rel > 0.62 else 'ahead'))

    dist      = locked_chair.get('distance', lock_state.last_distance or 3.0)
    raw_angle = (center_x - frame_center) / frame_width * fov_deg
    direction = ("left"          if raw_angle < -10
                 else ("right"   if raw_angle >  10
                        else "straight ahead"))
    abs_angle = abs(raw_angle)

    lock_state.last_distance  = dist
    lock_state.last_angle     = abs_angle
    lock_state.last_direction = direction

    print(f"[LOCK NAV] ID={lock_state.track_id} "
          f"dist={dist:.2f}m angle={abs_angle:.1f}° dir={direction}")

    # ── Sit confirmation when very close ──────────────────────
    if dist < 1.2 and not lock_state.sit_confirmed:
        if ask_sit_confirmation():
            lock_state.sit_confirmed = True
            speak("Great! Navigation complete. Enjoy your seat!")
            lock_state.reset()
            return
        else:
            speak("Okay, keep going.")
            return

    # ── Navigation guidance with cooldown ─────────────────────
    now = time.time()
    if now - last_guidance_time >= SPEAK_COOLDOWN:
        last_guidance_time = now
        if abs_angle > 40:
            msg = (f"Wrong direction. Locked chair is to your {direction}. "
                   f"Turn {direction} and walk forward.")
        elif direction == "straight ahead":
            msg = f"Locked chair straight ahead, {dist:.1f} meters. Keep going."
        else:
            msg = (f"Locked chair is {dist:.1f} meters. "
                   f"Turn {direction} about {abs_angle:.0f} degrees.")
        speak(msg)


# ─────────────────────────────────────────────────────────────
# PROVIDE GUIDANCE
# MODIFIED: receives locked_chair (pre-computed in main).
# ORIGINAL logic runs only when NOT locked.
# ─────────────────────────────────────────────────────────────
def provide_guidance(chairs, frame_width, results, locked_chair):
    global lock_state

    # ── LOCKED: navigate only ─────────────────────────────────
    if lock_state.locked and not lock_state.sit_confirmed:
        navigate_to_locked(locked_chair, frame_width)
        return

    # ══════════════════════════════════════════════════════════
    # ORIGINAL PROVIDE_GUIDANCE — COMPLETELY UNCHANGED
    # ══════════════════════════════════════════════════════════
    empty_chairs = [c for c in chairs
                    if not c.get('occupied', True)
                    and 'distance' in c
                    and 'track_id' in c]
    if not empty_chairs:
        speak("No empty chairs detected in the current view.")
        return

    persons = []
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:
                persons.append(box.xyxy[0].cpu().numpy())

    PRIVACY_RADIUS_PX = 180
    for chair in empty_chairs:
        chair_center_x = (chair['bbox'][0] + chair['bbox'][2]) / 2
        chair_center_y = (chair['bbox'][1] + chair['bbox'][3]) / 2
        nearby_count = 0
        for p in persons:
            p_center_x = (p[0] + p[2]) / 2
            p_center_y = (p[1] + p[3]) / 2
            dist_px = ((chair_center_x - p_center_x)**2 +
                       (chair_center_y - p_center_y)**2) ** 0.5
            if dist_px < PRIVACY_RADIUS_PX:
                nearby_count += 1
        chair['nearby_persons'] = nearby_count

    for chair in empty_chairs:
        chair['best_score'] = (chair['distance'] * 0.55) + (chair['nearby_persons'] * 0.45)

    empty_chairs.sort(key=lambda x: (x['best_score'], x.get('track_id', 9999)))

    best_chair     = empty_chairs[0]
    dist           = best_chair['distance']
    chair_center_x = (best_chair['bbox'][0] + best_chair['bbox'][2]) / 2
    frame_center_x = frame_width / 2
    fov_deg        = 78
    angle          = (chair_center_x - frame_center_x) / frame_width * fov_deg
    direction      = ("left"         if angle < -10
                      else ("right"  if angle >  10
                             else "straight ahead"))
    angle = abs(angle)

    obstacles  = [b for r in results for b in r.boxes
                  if int(b.cls[0]) not in [0, 56]]
    path_clear = len(obstacles) < 4

    nearest = best_chair
    print(f"GUIDANCE VALUES (used for audio): Nearest ID={nearest.get('track_id','?')} | "
          f"dist={dist:.2f}m | center_x={chair_center_x:.1f}px | angle={angle:.1f}° | "
          f"direction={direction} | path_clear={path_clear} | "
          f"total_empty={len(empty_chairs)} | "
          f"best_score={best_chair.get('best_score',0):.3f}")

    nearby      = best_chair['nearby_persons']
    privacy_msg = ""
    if nearby == 0:
        privacy_msg = "Excellent privacy — no one nearby. "
    elif nearby <= 2:
        privacy_msg = "Good privacy. "
    else:
        privacy_msg = "Best available for privacy. "

    # Mark is_best (UNCHANGED)
    for c in chairs:
        c['is_best'] = False
    best_chair['is_best'] = True

    # ── Ask lock confirmation ──────────────────────────────────
    prompt = (f"Best chair found. {privacy_msg}"
              f"It is {dist:.1f} meters {direction}. Lock this chair?")

    if ask_confirmation(prompt, chair_dist=dist, chair_dir=direction):
        bx = best_chair['bbox']
        lock_state.locked           = True
        lock_state.track_id         = best_chair.get('track_id')
        lock_state.last_bbox        = bx.copy() if hasattr(bx, 'copy') else list(bx)
        lock_state.last_center      = ((bx[0]+bx[2])/2, (bx[1]+bx[3])/2)
        lock_state.last_distance    = dist
        lock_state.last_angle       = angle
        lock_state.last_direction   = direction
        lock_state.last_seen_side   = 'ahead'
        lock_state.sit_confirmed    = False
        lock_state.frames_out_of_view = 0
        print(f"[LOCK SET] track_id={lock_state.track_id} "
              f"center={lock_state.last_center} dist={dist:.1f}m dir={direction}")
        speak(f"Chair locked. "
              f"The chair is {dist:.1f} meters {direction}. I will guide you there.")
    else:
        # Original full guidance on No (UNCHANGED)
        base = (f"{privacy_msg}Empty chair is {dist:.1f} meters "
                f"{direction}, about {angle:.0f} degrees.")
        if not path_clear:
            base += " Be careful, objects may be in the path."
        if dist > 6:
            base += " Move slowly."
        speak(base)
        speak(f"Total {len(empty_chairs)} empty chairs and "
              f"{len(chairs)-len(empty_chairs)} occupied.")

"""Cell-9"""

# Cell-9
# Updated JS to image converter
def js_to_image(js_reply):
    if not js_reply:
        return None
    image_bytes = b64decode(js_reply.split(',')[1])
    jpg_as_np = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

# Updated bbox to bytes for overlay
def bbox_to_bytes(bbox_array):
    bbox_PIL = PIL.Image.fromarray(bbox_array, 'RGBA')
    iobuf = io.BytesIO()
    bbox_PIL.save(iobuf, format='png')
    bbox_bytes = 'data:image/png;base64,{}'.format((str(b64encode(iobuf.getvalue()), 'utf-8')))
    return bbox_bytes

# Continuous video stream JS (2026 compatible)
def video_stream():
    js = Javascript('''
    var video;
    var div = null;
    var stream;
    var captureCanvas;
    var imgElement;
    var labelElement;
    var pendingResolve = null;
    var shutdown = false;
    function removeDom() {
       if (stream && stream.getVideoTracks().length > 0) {
         stream.getVideoTracks()[0].stop();
       }
       if (video) video.remove();
       if (div) div.remove();
       video = null;
       div = null;
       stream = null;
       imgElement = null;
       captureCanvas = null;
       labelElement = null;
    }
    function onAnimationFrame() {
      if (!shutdown) {
        window.requestAnimationFrame(onAnimationFrame);
      }
      if (pendingResolve) {
        var result = "";
        if (!shutdown) {
          captureCanvas.getContext('2d').drawImage(video, 0, 0, 640, 480);
          result = captureCanvas.toDataURL('image/jpeg', 0.8)
        }
        var lp = pendingResolve;
        pendingResolve = null;
        lp(result);
      }
    }
    async function createDom() {
      if (div !== null) {
         return stream;
      }
      div = document.createElement('div');
      div.style.border = '2px solid black';
      div.style.padding = '3px';
      div.style.width = '100%';
      div.style.maxWidth = '600px';
      document.body.appendChild(div);
      const modelOut = document.createElement('div');
      modelOut.innerHTML = "<span>Status:</span>";
      labelElement = document.createElement('span');
      labelElement.innerText = 'No data';
      labelElement.style.fontWeight = 'bold';
      modelOut.appendChild(labelElement);
      div.appendChild(modelOut);
      video = document.createElement('video');
      video.style.display = 'block';
      video.width = div.clientWidth - 6;
      video.setAttribute('playsinline', '');
      video.onclick = () => { shutdown = true; };
      stream = await navigator.mediaDevices.getUserMedia(
          {video: { facingMode: "environment"}});
      div.appendChild(video);
      imgElement = document.createElement('img');
      imgElement.style.position = 'absolute';
      imgElement.style.zIndex = 1;
      imgElement.onclick = () => { shutdown = true; };
      div.appendChild(imgElement);
      const instruction = document.createElement('div');
      instruction.innerHTML =
          '<span style="color: red; font-weight: bold;">' +
          'When finished, click here or on the video to stop this demo</span>';
      div.appendChild(instruction);
      instruction.onclick = () => { shutdown = true; };
      video.srcObject = stream;
      await video.play();
      captureCanvas = document.createElement('canvas');
      captureCanvas.width = 640;
      captureCanvas.height = 480;
      window.requestAnimationFrame(onAnimationFrame);
      return stream;
    }
    async function stream_frame(label, imgData) {
      if (shutdown) {
        removeDom();
        shutdown = false;
        return '';
      }
      var preCreate = Date.now();
      stream = await createDom();
      var preShow = Date.now();
      if (label != "") {
        labelElement.innerHTML = label;
      }
      if (imgData != "") {
        var videoRect = video.getClientRects()[0];
        imgElement.style.top = videoRect.top + "px";
        imgElement.style.left = videoRect.left + "px";
        imgElement.style.width = videoRect.width + "px";
        imgElement.style.height = videoRect.height + "px";
        imgElement.src = imgData;
      }
      var preCapture = Date.now();
      var result = await new Promise(function(resolve, reject) {
        pendingResolve = resolve;
      });
      shutdown = false;
      return {'create': preShow - preCreate,
              'show': preCapture - preShow,
              'capture': Date.now() - preCapture,
              'img': result};
    }
    ''')
    display(js)

def video_frame(label, bbox):
    data = eval_js('stream_frame("{}", "{}")'.format(label, bbox))
    return data

# Mobile stream — FIXED FOR PUBLIC URL (ngrok + laptop proxy)
def capture_mobile_stream(stream_url):
    """
    FIXED VERSION - NOW WORKS WITH PUBLIC URL
    Use the ngrok public URL from laptop proxy[](https://xxxx.ngrok-free.app)
    Local 192.168 IP will NEVER work from Colab cloud.
    """
    if not stream_url or not stream_url.startswith(('http://', 'https://')):
        print("❌ ERROR: Please use a PUBLIC ngrok URL[](https://xxxx.ngrok-free.app), not local 192.168 IP.")
        print("   Follow the laptop proxy + ngrok steps above.")
        return None
    max_retries = 4
    for attempt in range(max_retries):
        try:
            shot_url = stream_url.rstrip('/') + '/shot.jpg'
            response = requests.get(shot_url, timeout=15)
            if response.status_code == 200:
                img_arr = np.frombuffer(response.content, dtype=np.uint8)
                img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                if img is not None:
                    print(f"✅ Mobile frame captured successfully from public URL (attempt {attempt+1})")
                    return img
            print(f"Mobile shot failed: status {response.status_code} (attempt {attempt+1})")
        except Exception as e:
            print(f"Mobile error (attempt {attempt+1}): {e} - Retrying...")
        time.sleep(1.0)
    print("❌ All retries failed. Check ngrok is running and proxy is active.")
    return None

"""Cell- 10"""

# Cell-10 (option- for mobile & video & webcam)
# MODIFIED: lock_state.reset() at main() start.
# MODIFIED: reanchor_locked_chair() called once per frame, result passed everywhere.
# MODIFIED: Best-chair selection FULLY SKIPPED when lock active.
# MODIFIED: is_best cleared on all chairs when lock active (no duplicate label).
# MODIFIED: Draw loop uses lock_state.track_id (re-anchored) for is_locked check.
# MODIFIED: Ghost box drawn ONLY when frames_out_of_view > 0 (truly out of frame).
# MODIFIED: provide_guidance() called with locked_chair argument.
# MODIFIED: Thesis loop inner bbox var renamed bbox_c (no collision with webcam bbox var).
# ALL other logic UNCHANGED — thesis prints, output video, containers, frame capture.

def main(input_mode='colab_webcam', video_path=None, stream_url=None, max_frames=100):
    global lock_state
    lock_state.reset()

    frame_count = 0
    cap         = None
    bbox        = ''           # webcam overlay bytes — unchanged
    label_html  = 'Capturing...'
    out         = None

    # ── Output video writer — UNCHANGED ──────────────────────
    if input_mode == 'video_file' and video_path:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Cannot open video file.")
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps is None:
            fps = 30.0
        out = cv2.VideoWriter('processed_chair_detection.mp4',
                              cv2.VideoWriter_fourcc(*'mp4v'),
                              int(fps), (640, 480))

    # ── Webcam container — UNCHANGED ─────────────────────────
    if input_mode == 'colab_webcam':
        video_stream()
        time.sleep(2)
        display(Javascript('''
        setTimeout(() => {
            const videoDivs = document.querySelectorAll('div[style*="border: 2px solid black"]');
            if (videoDivs.length > 0) {
                const videoDiv = videoDivs[videoDivs.length - 1];
                videoDiv.style.position = 'fixed';
                videoDiv.style.right = '40px';
                videoDiv.style.top = '120px';
                videoDiv.style.width = '660px';
                videoDiv.style.zIndex = '9999';
                videoDiv.style.border = '4px solid #000';
                const imgElement = videoDiv.querySelector('img');
                if (imgElement) {
                    imgElement.style.position = 'fixed';
                    imgElement.style.zIndex = '10000';
                    function syncOverlay() {
                        const rect = videoDiv.getBoundingClientRect();
                        imgElement.style.left = rect.left + 'px';
                        imgElement.style.top = rect.top + 'px';
                        imgElement.style.width = rect.width + 'px';
                        imgElement.style.height = rect.height + 'px';
                    }
                    syncOverlay();
                    setInterval(syncOverlay, 80);
                }
            }
        }, 1500);
        '''))

    # ── Mobile / Video right container — UNCHANGED ───────────
    right_container_id = None
    if input_mode in ['mobile_stream', 'video_file']:
        right_container_id = f"right_display_{int(time.time()*1000)}"
        display(HTML(f'''
        <div id="{right_container_id}"
             style="position: fixed; right: 40px; top: 120px; width: 660px; z-index: 9999;
                    border: 4px solid #000; background: #111; padding: 8px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.6);">
            <div style="color: white; font-weight: bold; text-align: center; margin-bottom: 8px;">
                Processed Frame ({input_mode.replace('_', ' ').title()})
            </div>
            <img id="{right_container_id}_img" style="width:100%; display:block;" src="">
        </div>
        '''))
        display(Javascript(f'''
        setInterval(() => {{
            const el = document.getElementById("{right_container_id}");
            if (el) {{
                el.style.position = "fixed";
                el.style.right = "40px";
                el.style.top = "120px";
            }}
        }}, 300);
        '''))

    print(f"Starting main loop... Mode: {input_mode}")
    if input_mode == 'mobile_stream':
        print("✅ Mobile streaming active.")

    while True:
        frame = None

        # ── Frame capture — UNCHANGED ────────────────────────
        if input_mode == 'colab_webcam':
            try:
                js_reply = video_frame(label_html, bbox)
                if not js_reply or 'img' not in js_reply:
                    print("Webcam stopped.")
                    break
                frame = js_to_image(js_reply['img'])
                if frame is None:
                    print("Invalid frame.")
                    continue
            except Exception as e:
                print(f"Webcam error: {e}")
                break

        elif input_mode == 'video_file':
            ret, frame = cap.read()
            if not ret:
                print("End of video.")
                break

        elif input_mode == 'mobile_stream' and stream_url:
            frame = capture_mobile_stream(stream_url)
            if frame is None:
                print("No mobile frame — retrying.")
                time.sleep(2)
                continue
            time.sleep(0.35)

        elif input_mode == 'single_image':
            frame = cv2.imread('test.jpg')
            if frame is None:
                print("Cannot load test.jpg")
                break

        if frame is None:
            print(f"Frame {frame_count:04d}: skipping.")
            continue

        # ── Detection pipeline — UNCHANGED ───────────────────
        frame   = cv2.resize(frame, (640, 480))
        results = model_yolo(frame, verbose=False, conf=0.20)
        chairs, occ_count, empty_count = detect_occupancy(frame, results)
        chairs  = estimate_distance(frame, chairs)
        chairs  = tracker.update(chairs)

        # ════════════════════════════════════════════════════════
        # RE-ANCHOR locked chair ONCE per frame.
        # Must happen BEFORE best-chair selection AND provide_guidance.
        # Result is passed to provide_guidance and draw loop.
        # ════════════════════════════════════════════════════════
        locked_chair = None
        if lock_state.locked and not lock_state.sit_confirmed:
            locked_chair = reanchor_locked_chair(chairs)

        # ════════════════════════════════════════════════════════
        # BEST CHAIR SELECTION
        # Completely SKIPPED when lock is active.
        # This prevents: duplicate BEST CHAIR label, re-asking
        # confirmation, and locked chair being re-scored.
        # When locked, all chairs get is_best=False.
        # ════════════════════════════════════════════════════════
        if not lock_state.locked:
            empty_chairs_sel = [c for c in chairs
                                if not c.get('occupied', True)
                                and 'distance' in c
                                and 'track_id' in c]
            if empty_chairs_sel:
                for chair in empty_chairs_sel:
                    if 'nearby_persons' not in chair:
                        chair['nearby_persons'] = 0
                    chair['best_score'] = ((chair['distance'] * 0.55) +
                                           (chair['nearby_persons'] * 0.45))
                empty_chairs_sel.sort(
                    key=lambda x: (x['best_score'], x.get('track_id', 9999)))
                best = empty_chairs_sel[0]
                for c in chairs:
                    c['is_best'] = False
                best['is_best'] = True
        else:
            # Lock active — no BEST CHAIR label on any chair
            for c in chairs:
                c['is_best'] = False

        # ── THESIS PRINTS — UNCHANGED ────────────────────────
        print("=== THESIS VERIFICATION VALUES - Frame", frame_count, "===")
        for chair in chairs:
            tid    = chair.get('track_id', '?')
            bbox_c = chair['bbox']    # renamed — no collision with webcam 'bbox' var
            center = ((bbox_c[0]+bbox_c[2])/2, (bbox_c[1]+bbox_c[3])/2)
            print(f"Chair ID: {tid}")
            print(f" BBOX (exact pixels): {list(map(float, bbox_c))}")
            print(f" Center (px): ({center[0]:.1f}, {center[1]:.1f})")
            print(f" Measured Center for Tracking: {center}")
            print(f" Predicted Center (KF): {chair.get('predicted_center', 'N/A')}")
            print(f" Distance (practical): {chair.get('distance', 0):.2f} m")
            print(f" Raw median depth (MiDaS): {chair.get('raw_median', 'N/A')}")
            print(f" Seat pixels used: {chair.get('seat_pixels', 0)}")
            print(f" Occupied: {chair.get('occupied', False)}")
            print(f" conf_chair (YOLO): {chair.get('conf_chair', 0):.3f}")
            print(f" Max overlap score S: {chair.get('max_overlap_score', 0):.3f}")
            print(f" IoU value used: {chair.get('iou_value', 0):.3f}")
            print(f" conf_person used: {chair.get('conf_person_used', 0):.3f}")
            print(f" Overlapping person BBOX: {chair.get('overlapping_person_bbox')}")
            print(f" Hips z (MediaPipe): {chair.get('hips_z', 'N/A')}")
            print(f" Pose detected: {chair.get('pose_detected', False)}")
            if 'mask' in chair and chair['mask'] is not None:
                mask_bin = (chair['mask'] > 0.5).astype(np.uint8) * 255
                contours, _ = cv2.findContours(
                    mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours and len(contours[0]) > 0:
                    contour_sample    = contours[0][:5].reshape(-1, 2).tolist()
                    total_contour_pts = sum(len(cnt) for cnt in contours)
                    print(f" Contour points (sample 5 of ~{total_contour_pts}): "
                          f"{contour_sample}")
                else:
                    print(f" Contour points: No contours found")
            else:
                print(f" Contour points: No mask available")
        print("=== END THESIS VALUES ===")

        # ── Guidance — video_file skips audio (UNCHANGED) ────
        if input_mode != 'video_file':
            provide_guidance(chairs, frame.shape[1], results, locked_chair)

        # ════════════════════════════════════════════════════════
        # DRAW OVERLAYS
        # is_locked uses re-anchored lock_state.track_id.
        # Ghost box ONLY when frames_out_of_view > 0.
        # ════════════════════════════════════════════════════════
        bbox_array    = np.zeros((frame.shape[0], frame.shape[1], 4), dtype=np.uint8)
        font          = cv2.FONT_HERSHEY_SIMPLEX
        font_scale    = 0.55
        font_thickness = 2

        for chair in chairs:
            is_best     = chair.get('is_best', False)
            is_occupied = chair.get('occupied', True)
            # is_locked: match against re-anchored track_id
            is_locked   = (lock_state.locked
                           and not lock_state.sit_confirmed
                           and chair.get('track_id') == lock_state.track_id)

            # ── Color by priority ────────────────────────────
            if is_locked:
                box_color = (0, 165, 255)   # Orange — LOCKED
                thickness = 6
            elif is_best:
                box_color = (0, 255, 255)   # Yellow — BEST CHAIR (unchanged)
                thickness = 4
            elif not is_occupied:
                box_color = (0, 255, 0)     # Green — empty (unchanged)
                thickness = 3
            else:
                box_color = (0, 0, 255)     # Red — occupied (unchanged)
                thickness = 3

            x1, y1, x2, y2 = map(int, chair['bbox'])
            cv2.rectangle(frame,      (x1,y1),(x2,y2), box_color,          thickness)
            cv2.rectangle(bbox_array, (x1,y1),(x2,y2), box_color+(255,),   thickness)

            base_y = y1 - 10

            if is_locked:
                cv2.putText(frame,      "** LOCKED **",  (x1, base_y-68),
                            font, 0.80, (0,165,255), 3)
                cv2.putText(bbox_array, "** LOCKED **",  (x1, base_y-68),
                            font, 0.80, (0,165,255,255), 3)
                cv2.putText(frame,      "NAVIGATING TO", (x1, base_y-46),
                            font, 0.65, (0,255,255), 2)
                cv2.putText(bbox_array, "NAVIGATING TO", (x1, base_y-46),
                            font, 0.65, (0,255,255,255), 2)
                status_text = (f"Empty {chair.get('distance',0):.1f}m"
                               if not is_occupied
                               else f"Occupied {chair.get('distance',0):.1f}m")
                col = (0,255,0) if not is_occupied else (0,0,255)
                cv2.putText(frame,      status_text, (x1, base_y-22),
                            font, font_scale, col, font_thickness)
                cv2.putText(bbox_array, status_text, (x1, base_y-22),
                            font, font_scale, col+(255,), font_thickness)
                nav_ang = lock_state.last_angle     or 0.0
                nav_dir = lock_state.last_direction or ''
                id_text = (f"ID:{chair.get('track_id','?')} "
                           f"{nav_ang:.0f}deg {nav_dir}")
                cv2.putText(frame,      id_text, (x1, base_y+2),
                            font, font_scale, (0,165,255), font_thickness)
                cv2.putText(bbox_array, id_text, (x1, base_y+2),
                            font, font_scale, (0,165,255,255), font_thickness)

            elif is_best:
                # UNCHANGED from original
                cv2.putText(frame,      "BEST CHAIR", (x1, base_y-45),
                            font, 0.75, (0,255,255), 3)
                cv2.putText(bbox_array, "BEST CHAIR", (x1, base_y-45),
                            font, 0.75, (0,255,255,255), 3)
                status_text = (f"Empty {chair.get('distance',0):.1f}m"
                               if not is_occupied
                               else f"Occupied {chair.get('distance',0):.1f}m")
                col = (0,255,0) if not is_occupied else (0,0,255)
                cv2.putText(frame,      status_text, (x1, base_y-20),
                            font, font_scale, col, font_thickness)
                cv2.putText(bbox_array, status_text, (x1, base_y-20),
                            font, font_scale, col+(255,), font_thickness)
                id_text = f"ID:{chair.get('track_id','?')}"
                cv2.putText(frame,      id_text, (x1, base_y+5),
                            font, font_scale, col, font_thickness)
                cv2.putText(bbox_array, id_text, (x1, base_y+5),
                            font, font_scale, col+(255,), font_thickness)

            else:
                # UNCHANGED from original
                status_text = (f"Empty {chair.get('distance',0):.1f}m"
                               if not is_occupied
                               else f"Occupied {chair.get('distance',0):.1f}m")
                col = (0,255,0) if not is_occupied else (0,0,255)
                cv2.putText(frame,      status_text, (x1, base_y-20),
                            font, font_scale, col, font_thickness)
                cv2.putText(bbox_array, status_text, (x1, base_y-20),
                            font, font_scale, col+(255,), font_thickness)
                id_text = f"ID:{chair.get('track_id','?')}"
                cv2.putText(frame,      id_text, (x1, base_y+5),
                            font, font_scale, col, font_thickness)
                cv2.putText(bbox_array, id_text, (x1, base_y+5),
                            font, font_scale, col+(255,), font_thickness)

        # ── Ghost box: ONLY when chair truly absent from YOLO ─
        # frames_out_of_view>0 means reanchor returned None this frame
        if (lock_state.locked
                and not lock_state.sit_confirmed
                and lock_state.frames_out_of_view > 0
                and lock_state.last_bbox is not None):
            gx1,gy1,gx2,gy2 = map(int, lock_state.last_bbox)
            gx1=max(0,min(gx1,639)); gx2=max(0,min(gx2,639))
            gy1=max(0,min(gy1,479)); gy2=max(0,min(gy2,479))
            cv2.rectangle(frame,      (gx1,gy1),(gx2,gy2),(80,80,200),2)
            cv2.rectangle(bbox_array, (gx1,gy1),(gx2,gy2),(80,80,200,160),2)
            side = lock_state.last_seen_side or 'ahead'
            cv2.putText(frame, f"LOCKED (out of frame - go {side})",
                        (gx1, max(10,gy1-8)), font, 0.48, (80,80,200), 2)

        # ── Save / push / write — UNCHANGED ──────────────────
        cv2.imwrite(f'output_frame_{frame_count:04d}.jpg', frame)

        if input_mode in ['mobile_stream','video_file'] and right_container_id:
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = b64encode(buffer).decode('utf-8')
            display(Javascript(f'''
                const img = document.getElementById("{right_container_id}_img");
                if (img) {{
                    img.src = "data:image/jpeg;base64,{jpg_as_text}";
                }}
            '''))

        if out is not None:
            out.write(frame)

        print(f"Frame {frame_count:04d} | Empty:{empty_count} | Occ:{occ_count} | "
              f"Tracks:{len(tracker.trackers)} | "
              f"Dist:{[round(c.get('distance',0),1) for c in chairs]} | "
              f"Locked:{lock_state.locked}(ID:{lock_state.track_id}) | "
              f"OutOfFrame:{lock_state.frames_out_of_view}")

        if input_mode == 'colab_webcam':
            bbox = bbox_to_bytes(bbox_array)   # outer 'bbox' — unchanged

        frame_count += 1
        if input_mode != 'video_file' and frame_count >= max_frames:
            break

    if cap is not None:
        cap.release()
    if out is not None:
        out.release()
        print("\n✅ Video processing complete.")
        display(HTML('<h2>🎥 Processed Video with Chair Detections</h2>'))
        display(Video('processed_chair_detection.mp4', embed=True))
    print("Processing completed.")


# Cleanup — UNCHANGED
import os, glob
deleted = 0
for f in glob.glob('output_frame_*.jpg'):
    os.remove(f)
    deleted += 1
if os.path.exists('processed_chair_detection.mp4'):
    os.remove('processed_chair_detection.mp4')
    print("✅ Removed processed_chair_detection.mp4")
if os.path.exists('guidance.mp3'):
    os.remove('guidance.mp3')
print(f"✅ Cleanup complete! Deleted {deleted} output frame images.")

# Cell - Cleanup: Remove all saved output frames
import os
import glob

# Remove all output_frame_*.jpg files
deleted = 0
for f in glob.glob('output_frame_*.jpg'):
    os.remove(f)
    deleted += 1

# Also remove processed video if exists
if os.path.exists('processed_chair_detection.mp4'):
    os.remove('processed_chair_detection.mp4')
    print("✅ Removed processed_chair_detection.mp4")

# Remove guidance audio if exists
if os.path.exists('guidance.mp3'):
    os.remove('guidance.mp3')

print(f"✅ Cleanup complete! Deleted {deleted} output frame images.")

"""Cell-11"""

# Cell-11
# === FINAL TEST  (run one at a time) ===

# Colab webcam
#main(input_mode='colab_webcam', max_frames=100)

# Video file example (upload mp4 first in drive)
#main(input_mode='video_file', video_path='/content/drive/MyDrive/content/cv.mp4', max_frames=100)

# Mobile stream (use PUBLIC ngrok URL from laptop proxy)
# After starting IP Webcam + laptop proxy + ngrok http 5000:
main(input_mode='mobile_stream', stream_url='https://margarito-unslurred-whistlingly.ngrok-free.dev', max_frames=100)
# Replace the URL with your actual ngrok https URL