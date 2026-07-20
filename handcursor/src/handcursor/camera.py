import cv2
import time
class Camera:
    def __init__(self,index=0, width=640, height=480):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError("Couldnt open camera")

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        ok, frame = self.cap.read()
        if ok: 
            return frame
        return None

    def release(self):
        self.cap.release()


if __name__ == "__main__":
    cam = Camera()
    prev = time.time()

    while True:
        frame = cam.read()
        if frame is None:
            break
        frame = cv2.flip(frame, 1)
        
        now = time.time()
        fps = 1.0 /(now - prev)
        prev = now
        cv2.putText(frame, f"FPS: {fps: .1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)

        cv2.imshow("TEST WINDOW", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()
