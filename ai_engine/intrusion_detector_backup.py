import cv2
from ultralytics import YOLO

# ==========================================
# VisionGuard - Intrusion Detection Module
# ==========================================

# Load YOLO model
model = YOLO("yolo11n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

# ------------------------------------------
# Restricted Zone
# Format: (x1, y1, x2, y2)
# ------------------------------------------

ZONE_X1 = 150
ZONE_Y1 = 100
ZONE_X2 = 550
ZONE_Y2 = 450

print("===================================")
print("   VISIONGUARD INTRUSION ENGINE")
print("===================================")
print("Camera: CAM-01")
print("Location: Main Gate")
print("Restricted Zone: ACTIVE")
print("Press Q to exit.")
print()

while True:

    # Read camera frame
    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read webcam frame.")
        break

    # Run YOLO
    results = model(frame, verbose=False)

    intrusion_detected = False

    # Process detections
    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            # Class ID
            class_id = int(box.cls[0])

            # Confidence
            confidence = float(box.conf[0])

            # We only care about PERSON
            if class_id != 0:
                continue

            # Bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Person center point
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Check whether person is inside restricted zone
            inside_zone = (
                ZONE_X1 <= center_x <= ZONE_X2
                and
                ZONE_Y1 <= center_y <= ZONE_Y2
            )

            # ----------------------------------
            # Draw person detection
            # ----------------------------------

            if inside_zone:

                intrusion_detected = True

                box_color = (0, 0, 255)
                label = f"INTRUSION {confidence:.2f}"

            else:

                box_color = (0, 255, 0)
                label = f"PERSON {confidence:.2f}"

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

    # ------------------------------------------
    # Draw Restricted Zone
    # ------------------------------------------

    zone_color = (0, 0, 255) if intrusion_detected else (255, 165, 0)

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

    # ------------------------------------------
    # VisionGuard Status Panel
    # ------------------------------------------

    if intrusion_detected:

        status = "INTRUSION DETECTED"
        status_color = (0, 0, 255)

    else:

        status = "AREA SECURE"
        status_color = (0, 200, 0)

    cv2.rectangle(
        frame,
        (20, 20),
        (500, 75),
        (25, 25, 25),
        -1
    )

    cv2.putText(
        frame,
        status,
        (35, 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        status_color,
        2
    )

    # Camera information
    cv2.putText(
        frame,
        "CAM-01 | MAIN GATE",
        (20, frame.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # Show result
    cv2.imshow(
        "VisionGuard - Intrusion Detection",
        frame
    )

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

print("VisionGuard Intrusion Engine stopped.")