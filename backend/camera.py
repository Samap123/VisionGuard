import cv2
import time


# ============================================================
# VisionGuard Camera Configuration
# ============================================================

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


# ============================================================
# OPEN CAMERA
# ============================================================

def open_camera():

    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():

        camera.release()

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )

    if camera.isOpened():

        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH
        )

        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT
        )

        # Keep only the latest frame
        camera.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1
        )

        print("==========================================")
        print("VISIONGUARD CAMERA")
        print("CAMERA OPEN: TRUE")
        print("==========================================")

        return camera

    print("CAMERA OPEN: FALSE")

    return None


# ============================================================
# MJPEG FRAME GENERATOR
# ============================================================

def generate_frames():

    camera = open_camera()

    if camera is None:

        print("ERROR: Unable to access webcam.")

        return


    print("VISIONGUARD VIDEO STREAM STARTED")


    try:

        while True:

            # ------------------------------------------
            # Read camera frame
            # ------------------------------------------

            success, frame = camera.read()


            if not success or frame is None:

                print("WARNING: Frame read failed")

                time.sleep(0.05)

                continue


            # ------------------------------------------
            # VisionGuard overlay
            # ------------------------------------------

            cv2.putText(
                frame,
                "SYSTEM MONITORING",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                "CAM-01 | MAIN GATE",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )


            # ------------------------------------------
            # Encode frame as JPEG
            # ------------------------------------------

            success, buffer = cv2.imencode(
                ".jpg",
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80
                ]
            )


            if not success:

                continue


            frame_bytes = buffer.tobytes()


            # ------------------------------------------
            # MJPEG response frame
            # ------------------------------------------

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: "
                + str(len(frame_bytes)).encode()
                + b"\r\n\r\n"
                + frame_bytes
                + b"\r\n"
            )


    except GeneratorExit:

        print(
            "VISIONGUARD VIDEO STREAM DISCONNECTED"
        )


    except Exception as e:

        print(
            f"VIDEO STREAM ERROR: {e}"
        )


    finally:

        camera.release()

        print(
            "VISIONGUARD CAMERA RELEASED"
        )