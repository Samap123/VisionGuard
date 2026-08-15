import cv2
import time
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from ultralytics import YOLO

from backend.evidence import save_evidence
from backend.alerts import create_alert


# ============================================================
# VISIONGUARD PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "yolo11n.pt"


# ============================================================
# VISIONGUARD YOLO MODEL
# ============================================================

print("=" * 60)
print("VISIONGUARD AI DETECTOR INITIALIZATION")
print("=" * 60)

print(f"YOLO MODEL: {MODEL_PATH}")

model = YOLO(str(MODEL_PATH))

print("YOLO MODEL LOADED SUCCESSFULLY")


# ============================================================
# MONGODB
# ============================================================

MONGO_URL = "mongodb://127.0.0.1:27017"

client = MongoClient(
    MONGO_URL,
    serverSelectionTimeoutMS=3000
)

db = client["visionguard"]

incidents_collection = db["incidents"]


# ============================================================
# MONGODB CONNECTION TEST
# ============================================================

try:

    client.admin.command("ping")

    print("MONGODB: CONNECTED")

except Exception as e:

    print(f"MONGODB WARNING: {e}")


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

CAMERA_ID = "CAM-01"

CAMERA_LOCATION = "Main Gate"

CAMERA_INDEX = 0


# ============================================================
# INTRUSION SETTINGS
# ============================================================

# Minimum number of people required
# to trigger an intrusion.

PERSON_THRESHOLD = 1


# YOLO confidence threshold.

YOLO_CONFIDENCE = 0.50


# Number of consecutive frames required
# before confirming an intrusion.

CONFIRMATION_FRAMES = 5


# Number of seconds the scene must remain
# below the threshold before closing the incident.

CLEAR_DELAY = 2.0


# ============================================================
# INTRUSION SESSION STATE
# ============================================================

intrusion_active = False

intrusion_confirm_count = 0

last_intrusion_seen_time = 0

active_incident_id = None

active_incident_started_at = None


# ============================================================
# CREATE MONGODB INCIDENT
# ============================================================

def create_intrusion_incident(
    person_count,
    evidence_path=None
):

    incident_id = (
        f"VG-INC-"
        f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    )

    started_at = datetime.now()

    incident = {

        "incident_id": incident_id,

        "activity": "Intrusion",

        "risk_level": "HIGH",

        "camera_id": CAMERA_ID,

        "location": CAMERA_LOCATION,

        "status": "ACTIVE",

        "person_count": person_count,

        "evidence_path": evidence_path,

        "timestamp": started_at.isoformat(),

        "started_at": started_at.isoformat(),

        "ended_at": None,

        "duration_seconds": None
    }


    try:

        incidents_collection.insert_one(
            incident.copy()
        )

        print()
        print("💾 INCIDENT SAVED")
        print(f"   ID       : {incident_id}")
        print(f"   Persons  : {person_count}")
        print(f"   Evidence : {evidence_path}")
        print(f"   Started  : {started_at.isoformat()}")
        print()

        return incident


    except Exception as e:

        print()
        print(f"❌ MONGODB INCIDENT ERROR: {e}")
        print()

        return None


# ============================================================
# CLOSE ACTIVE INTRUSION INCIDENT
# ============================================================

def close_intrusion_incident():

    global active_incident_id
    global active_incident_started_at

    if active_incident_id is None:

        return


    ended_at = datetime.now()


    duration_seconds = None


    if active_incident_started_at is not None:

        duration_seconds = round(
            (
                ended_at -
                active_incident_started_at
            ).total_seconds(),
            2
        )


    try:

        result = incidents_collection.update_one(

            {
                "incident_id":
                    active_incident_id
            },

            {
                "$set": {

                    "status": "CLOSED",

                    "ended_at":
                        ended_at.isoformat(),

                    "duration_seconds":
                        duration_seconds
                }
            }
        )


        if result.modified_count > 0:

            print()
            print("✅ INTRUSION SESSION CLOSED")
            print(
                f"   Incident : {active_incident_id}"
            )
            print(
                f"   Duration : {duration_seconds}s"
            )
            print()


        else:

            print(
                "⚠️ Could not update incident status."
            )


    except Exception as e:

        print(
            f"❌ Incident Close Error: {e}"
        )


    # Reset active incident state.

    active_incident_id = None

    active_incident_started_at = None


# ============================================================
# START NEW INTRUSION SESSION
# ============================================================

def start_intrusion_session(
    person_count,
    annotated_frame
):

    global intrusion_active
    global active_incident_id
    global active_incident_started_at
    global last_intrusion_seen_time


    print()
    print("=" * 60)
    print("🚨 VISIONGUARD SECURITY EVENT")
    print("=" * 60)

    print(
        "Activity     : Intrusion"
    )

    print(
        "Risk Level   : HIGH"
    )

    print(
        f"Camera       : {CAMERA_ID}"
    )

    print(
        f"Location     : {CAMERA_LOCATION}"
    )

    print(
        f"Persons      : {person_count}"
    )


    # ========================================================
    # 1. SAVE EVIDENCE
    # ========================================================

    evidence_path = None


    try:

        evidence_path = save_evidence(
            annotated_frame
        )

        print(
            f"📸 EVIDENCE SAVED: {evidence_path}"
        )


    except Exception as e:

        print(
            f"❌ Evidence Save Error: {e}"
        )


    # ========================================================
    # 2. CREATE MONGODB INCIDENT
    # ========================================================

    incident = create_intrusion_incident(
        person_count,
        evidence_path
    )


    if incident is None:

        print(
            "⚠️ Incident could not be created."
        )

        return


    active_incident_id = (
        incident["incident_id"]
    )

    active_incident_started_at = (
        datetime.now()
    )


    # ========================================================
    # 3. CREATE SECURITY ALERT
    # ========================================================

    try:

        create_alert(

            activity="Intrusion",

            risk_level="HIGH",

            camera_id=CAMERA_ID,

            location=CAMERA_LOCATION,

            person_count=person_count,

            evidence_path=evidence_path
        )


        print(
            "🚨 SECURITY ALERT CREATED"
        )


    except Exception as e:

        print(
            f"❌ Alert Error: {e}"
        )


    # ========================================================
    # 4. ACTIVATE SESSION
    # ========================================================

    intrusion_active = True

    last_intrusion_seen_time = time.time()


    print(
        "🔴 INTRUSION SESSION ACTIVE"
    )

    print(
        "📌 New alerts will NOT be created "
        "until this intrusion ends."
    )

    print("=" * 60)
    print()


# ============================================================
# GENERATE LIVE CAMERA FRAMES
# ============================================================

def generate_frames():

    global intrusion_active
    global intrusion_confirm_count
    global last_intrusion_seen_time


    # ========================================================
    # OPEN WEBCAM
    # ========================================================

    print()
    print("=" * 60)
    print("VISIONGUARD CAMERA STARTING")
    print("=" * 60)


    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )


    # Fallback camera initialization.

    if not camera.isOpened():

        print(
            "⚠️ DirectShow camera opening failed."
        )

        camera.release()

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )


    # Final camera check.

    if not camera.isOpened():

        print(
            "❌ ERROR: Could not open webcam."
        )

        return


    print(
        "CAMERA: ONLINE"
    )


    # ========================================================
    # CAMERA RESOLUTION
    # ========================================================

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        640
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        480
    )


    # ========================================================
    # CAMERA FPS
    # ========================================================

    camera.set(
        cv2.CAP_PROP_FPS,
        30
    )


    print(
        "🎥 VisionGuard AI Detection Started"
    )

    print(
        "📷 Camera: CAM-01 | Main Gate"
    )

    print(
        "🤖 YOLO: Active"
    )

    print(
        f"🚨 Intrusion Threshold: "
        f"{PERSON_THRESHOLD} persons"
    )

    print(
        f"🧠 Confirmation Frames: "
        f"{CONFIRMATION_FRAMES}"
    )

    print(
        f"⏱️ Clear Delay: "
        f"{CLEAR_DELAY} seconds"
    )

    print("=" * 60)
    print()


    # ========================================================
    # MAIN DETECTION LOOP
    # ========================================================

    try:

        while True:

            # =================================================
            # READ CAMERA FRAME
            # =================================================

            success, frame = camera.read()


            if not success or frame is None:

                print(
                    "⚠️ Camera frame read failed."
                )

                time.sleep(0.05)

                continue


            # =================================================
            # YOLO OBJECT DETECTION
            # =================================================

            try:

                results = model(

                    frame,

                    conf=YOLO_CONFIDENCE,

                    verbose=False
                )

                result = results[0]


            except Exception as e:

                print(
                    f"❌ YOLO Detection Error: {e}"
                )

                continue


            # =================================================
            # COUNT PERSONS
            # =================================================

            person_count = 0


            if result.boxes is not None:

                for cls in result.boxes.cls:

                    class_id = int(cls)

                    # COCO class 0 = person.

                    if class_id == 0:

                        person_count += 1


            # =================================================
            # DRAW YOLO DETECTIONS
            # =================================================

            annotated_frame = result.plot()


            # =================================================
            # CURRENT TIME
            # =================================================

            current_time = time.time()


            # =================================================
            # CHECK INTRUSION CONDITION
            # =================================================

            intrusion_detected = (
                person_count >= PERSON_THRESHOLD
            )


            # =================================================
            # INTRUSION DETECTED
            # =================================================

            if intrusion_detected:

                # ------------------------------------------------
                # UPDATE LAST SEEN TIME
                # ------------------------------------------------

                last_intrusion_seen_time = (
                    current_time
                )


                # ------------------------------------------------
                # CONFIRMATION LOGIC
                # ------------------------------------------------

                if not intrusion_active:

                    intrusion_confirm_count += 1


                # ------------------------------------------------
                # RED ALERT HEADER
                # ------------------------------------------------

                cv2.rectangle(

                    annotated_frame,

                    (0, 0),

                    (640, 90),

                    (0, 0, 120),

                    -1
                )


                cv2.putText(

                    annotated_frame,

                    "INTRUSION DETECTED",

                    (20, 35),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.85,

                    (255, 255, 255),

                    2,

                    cv2.LINE_AA
                )


                cv2.putText(

                    annotated_frame,

                    f"Persons: {person_count}",

                    (20, 70),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.65,

                    (255, 220, 220),

                    2,

                    cv2.LINE_AA
                )


                # ------------------------------------------------
                # CONFIRMING STATUS
                # ------------------------------------------------

                if not intrusion_active:

                    cv2.putText(

                        annotated_frame,

                        (
                            f"CONFIRMING "
                            f"{intrusion_confirm_count}/"
                            f"{CONFIRMATION_FRAMES}"
                        ),

                        (360, 35),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.55,

                        (255, 255, 255),

                        2,

                        cv2.LINE_AA
                    )


                # ------------------------------------------------
                # START NEW SESSION
                # ------------------------------------------------

                if (

                    not intrusion_active

                    and
                    intrusion_confirm_count
                    >= CONFIRMATION_FRAMES

                ):

                    start_intrusion_session(

                        person_count,

                        annotated_frame
                    )


                    intrusion_confirm_count = 0


            # =================================================
            # NORMAL / CLEAR STATE
            # =================================================

            else:

                # ------------------------------------------------
                # RESET CONFIRMATION
                # ------------------------------------------------

                if not intrusion_active:

                    intrusion_confirm_count = 0


                # ------------------------------------------------
                # CLOSE ACTIVE SESSION
                # ------------------------------------------------

                if intrusion_active:

                    time_since_last_detection = (

                        current_time
                        -
                        last_intrusion_seen_time
                    )


                    if (
                        time_since_last_detection
                        >= CLEAR_DELAY
                    ):

                        close_intrusion_incident()

                        intrusion_active = False

                        intrusion_confirm_count = 0


                # ------------------------------------------------
                # NORMAL MONITORING HEADER
                # ------------------------------------------------

                cv2.rectangle(

                    annotated_frame,

                    (0, 0),

                    (640, 85),

                    (0, 80, 0),

                    -1
                )


                cv2.putText(

                    annotated_frame,

                    "SYSTEM MONITORING",

                    (20, 35),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.8,

                    (255, 255, 255),

                    2,

                    cv2.LINE_AA
                )


                cv2.putText(

                    annotated_frame,

                    f"Persons: {person_count}",

                    (20, 70),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.65,

                    (220, 255, 220),

                    2,

                    cv2.LINE_AA
                )


            # =================================================
            # ACTIVE SESSION INDICATOR
            # =================================================

            if intrusion_active:

                cv2.putText(

                    annotated_frame,

                    "ALERT SESSION ACTIVE",

                    (370, 35),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.55,

                    (255, 255, 255),

                    2,

                    cv2.LINE_AA
                )


            # =================================================
            # CAMERA INFORMATION
            # =================================================

            cv2.putText(

                annotated_frame,

                "CAM-01 | MAIN GATE",

                (400, 465),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (255, 255, 255),

                1,

                cv2.LINE_AA
            )


            # =================================================
            # ENCODE FRAME AS JPEG
            # =================================================

            ret, buffer = cv2.imencode(

                ".jpg",

                annotated_frame,

                [

                    cv2.IMWRITE_JPEG_QUALITY,

                    80
                ]
            )


            if not ret:

                continue


            frame_bytes = buffer.tobytes()


            # =================================================
            # MJPEG STREAM
            # =================================================

            yield (

                b"--frame\r\n"

                b"Content-Type: image/jpeg\r\n"

                b"Content-Length: "

                + str(
                    len(frame_bytes)
                ).encode()

                + b"\r\n\r\n"

                + frame_bytes

                + b"\r\n"
            )


    # ========================================================
    # CLIENT DISCONNECTED
    # ========================================================

    except GeneratorExit:

        print()

        print(
            "🎥 VisionGuard camera stream disconnected."
        )


    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        print()

        print(
            f"❌ Detection Stream Error: {e}"
        )


    # ========================================================
    # ALWAYS RELEASE CAMERA
    # ========================================================

    finally:

        camera.release()

        print(
            "🎥 VisionGuard camera released."
        )