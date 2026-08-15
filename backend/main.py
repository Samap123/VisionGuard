import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient

from backend.detector import generate_frames


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

EVIDENCE_DIR = os.path.join(
    BASE_DIR,
    "evidence"
)

os.makedirs(
    EVIDENCE_DIR,
    exist_ok=True
)


# ============================================================
# VISIONGUARD FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="VisionGuard API",
    description="AI-powered intelligent CCTV surveillance backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# SERVE EVIDENCE IMAGES
# ============================================================

app.mount(
    "/evidence",
    StaticFiles(directory=EVIDENCE_DIR),
    name="evidence"
)


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
# CAMERA CONFIGURATION
# ============================================================

cameras = [

    {
        "camera_id": "CAM-01",
        "location": "Main Gate",
        "status": "ONLINE",
        "control_room": "CR-01"
    }

]


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "system": "VisionGuard",
        "status": "online"
    }


# ============================================================
# LIVE CAMERA FEED
# ============================================================

@app.get("/video_feed")
def video_feed():

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    try:

        client.admin.command("ping")

        return {
            "status": "online",
            "service": "VisionGuard Backend",
            "database": "connected"
        }

    except Exception:

        return {
            "status": "online",
            "service": "VisionGuard Backend",
            "database": "disconnected"
        }


# ============================================================
# CAMERA INFORMATION
# ============================================================

@app.get("/cameras")
def get_cameras():

    return {
        "total_cameras": len(cameras),
        "cameras": cameras
    }


# ============================================================
# GET INCIDENTS
# ============================================================

@app.get("/incidents")
def get_incidents():

    incidents = list(
        incidents_collection.find(
            {},
            {"_id": 0}
        ).sort(
            "timestamp",
            -1
        )
    )

    # --------------------------------------------------------
    # Add browser-accessible evidence URL
    # --------------------------------------------------------

    for incident in incidents:

        evidence_path = incident.get(
            "evidence_path"
        )

        if evidence_path:

            filename = os.path.basename(
                evidence_path
            )

            incident["evidence_url"] = (
                f"/evidence/{filename}"
            )

        else:

            incident["evidence_url"] = None


    return {

        "total_incidents": len(
            incidents
        ),

        "incidents": incidents
    }


# ============================================================
# CREATE INCIDENT
# ============================================================

@app.post("/incidents")
def create_incident(

    activity: str = "Intrusion",

    risk_level: str = "HIGH",

    camera_id: str = "CAM-01",

    location: str = "Main Gate"

):

    incident_id = (

        f"VG-INC-"
        f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    )


    incident = {

        "incident_id": incident_id,

        "activity": activity,

        "risk_level": risk_level,

        "camera_id": camera_id,

        "location": location,

        "status": "ACTIVE",

        "timestamp": datetime.now().isoformat()

    }


    incidents_collection.insert_one(
        incident.copy()
    )


    return {

        "message":
            "Incident created successfully",

        "incident":
            incident

    }