from ultralytics import YOLO
from backend.evidence import save_evidence
from backend.alerts import create_alert

import time


# ============================================================
# VisionGuard YOLO Model
# ============================================================

model = YOLO("yolo11n.pt")


# ============================================================
# Intrusion Configuration
# ============================================================

PERSON_THRESHOLD = 1

EVIDENCE_COOLDOWN = 5

last_evidence_time = 0


# ============================================================
# Object Detection
# ============================================================

def detect_objects(frame):

    global last_evidence_time


    # ========================================================
    # Run YOLO
    # ========================================================

    results = model(
        frame,
        conf=0.5,
        verbose=False
    )

    result = results[0]


    # ========================================================
    # Count Persons
    # ========================================================

    person_count = 0

    if result.boxes is not None:

        for box in result.boxes:

            class_id = int(box.cls[0])

            # COCO class 0 = person
            if class_id == 0:

                person_count += 1


    # ========================================================
    # Annotated Frame
    # ========================================================

    annotated_frame = result.plot()


    # ========================================================
    # Intrusion Detection
    # ========================================================

    intrusion_detected = (
        person_count >= PERSON_THRESHOLD
    )


    # ========================================================
    # Intrusion Alert
    # ========================================================

    if intrusion_detected:

        current_time = time.time()


        # ====================================================
        # Add Alert Text To Camera
        # ====================================================

        import cv2

        cv2.putText(
            annotated_frame,
            "INTRUSION DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (0, 0, 255),
            3
        )

        cv2.putText(
            annotated_frame,
            f"Persons: {person_count}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


        # ====================================================
        # Cooldown
        # ====================================================

        if (
            current_time - last_evidence_time
            >= EVIDENCE_COOLDOWN
        ):

            # ==================================================
            # Save Evidence
            # ==================================================

            evidence_path = save_evidence(
                annotated_frame,
                person_count=person_count,
                camera_id="CAM-01",
                location="Main Gate"
            )


            # ==================================================
            # Create Security Alert
            # ==================================================

            alert = create_alert(
                activity="Intrusion",
                risk_level="HIGH",
                camera_id="CAM-01",
                location="Main Gate",
                person_count=person_count,
                evidence_path=evidence_path
            )


            # ==================================================
            # Console Alert
            # ==================================================

            print(
                f"🚨 ALERT CREATED: "
                f"{alert['message']}"
            )


            # ==================================================
            # Update Cooldown
            # ==================================================

            last_evidence_time = current_time


    # ========================================================
    # Return Detection Result
    # ========================================================

    return (
        annotated_frame,
        person_count,
        intrusion_detected
    )