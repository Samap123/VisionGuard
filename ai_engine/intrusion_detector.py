import cv2
import os
import requests
from datetime import datetime
from ultralytics import YOLO

# ==========================================
# VisionGuard - Incident Engine
# ==========================================

# Load YOLO model
model = YOLO("yolo11n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

# ==========================================
# Camera Information
# ==========================================

CAMERA_ID = "CAM-01"
LOCATION = "Main Gate"
RISK_LEVEL = "HIGH"
BACKEND_URL = "http://127.0.0.1:8000/incidents"

def send_incident_to_backend(
    activity,
    risk_level,
    camera_id,
    location
):
    try:
        response = requests.post(
            BACKEND_URL,
            params={
                "activity": activity,
                "risk_level": risk_level,
                "camera_id": camera_id,
                "location": location
            },
            timeout=5
        )

        if response.status_code == 200:
            print("SUCCESS: Incident sent to VisionGuard Backend")
            print("Backend Response:")
            print(response.json())

        else:
            print(
                "ERROR: Backend returned status code:",
                response.status_code
            )

    except requests.exceptions.RequestException as error:
        print("ERROR: Could not connect to VisionGuard Backend")
        print(error)

# ==========================================
# Evidence Folder
# ==========================================

EVIDENCE_FOLDER = "evidence"

os.makedirs(EVIDENCE_FOLDER, exist_ok=True)

# ==========================================
# Restricted Zone
# ==========================================

ZONE_X1 = 150
ZONE_Y1 = 100
ZONE_X2 = 550
ZONE_Y2 = 450

# ==========================================
# Incident Control
# ==========================================

incident_active = False
incident_number = 0

print("===================================")
print("      VISIONGUARD INCIDENT ENGINE")
print("===================================")
print(f"Camera   : {CAMERA_ID}")
print(f"Location : {LOCATION}")
print("Risk     : HIGH")
print("Press Q to exit.")
print()

while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read webcam frame.")
        break

    results = model(frame, verbose=False)

    intrusion_detected = False

    # ======================================
    # Process detections
    # ======================================

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # Only detect PERSON
            if class_id != 0:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Person center
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Check restricted zone
            inside_zone = (
                ZONE_X1 <= center_x <= ZONE_X2
                and
                ZONE_Y1 <= center_y <= ZONE_Y2
            )

            if inside_zone:

                intrusion_detected = True

                box_color = (0, 0, 255)

                label = f"INTRUSION {confidence:.2f}"

            else:

                box_color = (0, 255, 0)

                label = f"PERSON {confidence:.2f}"

            # Draw person box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                box_color,
                2
            )

            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                box_color,
                2
            )

    # ======================================
    # CREATE INCIDENT
    # ======================================

    if intrusion_detected and not incident_active:

        incident_active = True
        incident_number += 1

        incident_id = (
            f"VG-INC-"
            f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Evidence filename
        evidence_filename = (
            f"{incident_id}.jpg"
        )

        evidence_path = os.path.join(
            EVIDENCE_FOLDER,
            evidence_filename
        )

        # Save evidence image
        cv2.imwrite(
            evidence_path,
            frame
        )

        # Create incident log
        incident_log = f"""
========================================
VISIONGUARD INCIDENT REPORT
========================================

Incident ID : {incident_id}

Activity    : Intrusion
Risk Level  : {RISK_LEVEL}

Camera ID   : {CAMERA_ID}
Location    : {LOCATION}

Timestamp   : {timestamp}

Status      : ACTIVE
Evidence    : {evidence_filename}

========================================
"""

        print(incident_log)

        send_incident_to_backend(
               activity="Intrusion",
               risk_level=RISK_LEVEL,
               camera_id=CAMERA_ID,
               location=LOCATION
            )

        # Save incident report
        report_filename = (
            f"{incident_id}.txt"
        )

        report_path = os.path.join(
            EVIDENCE_FOLDER,
            report_filename
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(incident_log)

    # ======================================
    # Reset incident when area is clear
    # ======================================

    if not intrusion_detected:

        incident_active = False

    # ======================================
    # Draw Restricted Zone
    # ======================================

    if intrusion_detected:

        zone_color = (0, 0, 255)

    else:

        zone_color = (255, 165, 0)

    cv2.rectangle(
        frame,
        (ZONE_X1, ZONE_Y1),
        (ZONE_X2, ZONE_Y2),
        zone_color,
        3
    )

    cv2.putText(
        frame,
        "RESTRICTED ZONE",
        (ZONE_X1, ZONE_Y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        zone_color,
        2
    )

    # ======================================
    # Status Panel
    # ======================================

    if intrusion_detected:

        status = "INTRUSION DETECTED"
        status_color = (0, 0, 255)

    else:

        status = "AREA SECURE"
        status_color = (0, 200, 0)

    cv2.rectangle(
        frame,
        (20, 20),
        (500, 80),
        (25, 25, 25),
        -1
    )

    cv2.putText(
        frame,
        status,
        (35, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        status_color,
        2
    )

    # Camera information
    cv2.putText(
        frame,
        f"{CAMERA_ID} | {LOCATION}",
        (20, frame.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # Display
    cv2.imshow(
        "VisionGuard - Incident Engine",
        frame
    )

    # Quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# ==========================================
# Cleanup
# ==========================================

cap.release()
cv2.destroyAllWindows()

print("VisionGuard Incident Engine stopped.")