import cv2
import os
import json
from datetime import datetime


# ============================================================
# VisionGuard Evidence Storage
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

EVIDENCE_DIR = os.path.join(
    PROJECT_ROOT,
    "evidence"
)

os.makedirs(
    EVIDENCE_DIR,
    exist_ok=True
)


# ============================================================
# Save Evidence
# ============================================================

def save_evidence(
    frame,
    person_count=0,
    camera_id="CAM-01",
    location="Main Gate"
):
    """
    Saves:
    1. Evidence image
    2. Evidence details JSON

    Returns:
        image_path
    """

    timestamp = datetime.now()

    timestamp_text = timestamp.strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    readable_time = timestamp.isoformat()


    # ========================================================
    # File Names
    # ========================================================

    image_filename = (
        f"intrusion_{timestamp_text}.jpg"
    )

    json_filename = (
        f"intrusion_{timestamp_text}.json"
    )


    image_path = os.path.join(
        EVIDENCE_DIR,
        image_filename
    )

    json_path = os.path.join(
        EVIDENCE_DIR,
        json_filename
    )


    # ========================================================
    # Save Image
    # ========================================================

    image_saved = cv2.imwrite(
        image_path,
        frame
    )

    if not image_saved:

        print("❌ Failed to save evidence image")

        return None


    # ========================================================
    # Evidence Details
    # ========================================================

    evidence_details = {

        "incident_id":
            f"VG-INC-{timestamp_text}",

        "activity":
            "Intrusion",

        "risk_level":
            "HIGH",

        "camera_id":
            camera_id,

        "location":
            location,

        "person_count":
            person_count,

        "timestamp":
            readable_time,

        "evidence_image":
            image_filename,

        "evidence_path":
            image_path,

        "status":
            "ACTIVE"
    }


    # ========================================================
    # Save JSON
    # ========================================================

    try:

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                evidence_details,
                file,
                indent=4
            )

    except Exception as e:

        print(
            f"❌ Failed to save evidence details: {e}"
        )


    # ========================================================
    # Console Output
    # ========================================================

    print(
        f"📸 EVIDENCE IMAGE: {image_path}"
    )

    print(
        f"📄 EVIDENCE DETAILS: {json_path}"
    )


    return image_path