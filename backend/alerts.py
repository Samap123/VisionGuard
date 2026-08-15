from datetime import datetime


# ============================================================
# VisionGuard Alert System
# ============================================================

def create_alert(
    activity="Intrusion",
    risk_level="HIGH",
    camera_id="CAM-01",
    location="Main Gate",
    person_count=0,
    evidence_path=None
):
    """
    Creates a VisionGuard security alert.
    """

    alert = {
        "alert_type": "SECURITY_ALERT",
        "activity": activity,
        "risk_level": risk_level,
        "camera_id": camera_id,
        "location": location,
        "person_count": person_count,
        "evidence_path": evidence_path,
        "timestamp": datetime.now().isoformat(),

        "message": (
            f"🚨 {activity} detected at {location} | "
            f"Camera: {camera_id} | "
            f"Persons: {person_count} | "
            f"Risk: {risk_level}"
        )
    }

    # Console alert
    print()
    print("=" * 65)
    print("🚨 VISIONGUARD SECURITY ALERT")
    print("=" * 65)
    print(f"Activity     : {activity}")
    print(f"Risk Level   : {risk_level}")
    print(f"Camera       : {camera_id}")
    print(f"Location     : {location}")
    print(f"Persons      : {person_count}")
    print(f"Evidence     : {evidence_path}")
    print(f"Time         : {alert['timestamp']}")
    print(f"Message      : {alert['message']}")
    print("=" * 65)
    print()

    return alert