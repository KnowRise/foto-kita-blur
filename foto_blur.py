import time

import cv2

from hand_tracker import HandTracker
from music_player import MusicPlayer

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Kamera tidak bisa dibuka. Tutup aplikasi lain yang sedang memakai kamera.")
    raise SystemExit(1)

tracker = HandTracker(max_hands=1)
music = MusicPlayer("music.mp3", volume=50)
if not music.available and music.message:
    print(f"Info musik: {music.message}")

current_blur = 1
show_landmarks = True
prev_time = time.perf_counter()
fps = 0.0

try:
    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        hand = tracker.process(img, draw=False)
        peace = hand is not None and hand.is_peace

        target_blur = 61 if peace else 1
        if current_blur < target_blur:
            current_blur = min(current_blur + 6, target_blur)
        elif current_blur > target_blur:
            current_blur = max(current_blur - 6, target_blur)

        blur_kernel = current_blur if current_blur % 2 != 0 else current_blur + 1
        if blur_kernel > 1:
            img = cv2.GaussianBlur(img, (blur_kernel, blur_kernel), 0)

        if show_landmarks and hand is not None:
            tracker.draw(img, hand)

        now = time.perf_counter()
        dt = now - prev_time
        prev_time = now
        if dt > 0:
            fps = fps * 0.9 + (1.0 / dt) * 0.1

        if peace:
            status = "PEACE -> BLUR"
            status_color = (60, 255, 120)
        elif hand is None:
            status = "NORMAL - tangan tidak terdeteksi"
            status_color = (200, 200, 200)
        else:
            status = "NORMAL - tunjukkan peace untuk blur"
            status_color = (235, 235, 235)

        cv2.rectangle(img, (0, 0), (640, 60), (15, 15, 20), -1)
        cv2.putText(
            img, status, (16, 28),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2, cv2.LINE_AA,
        )
        cv2.putText(
            img,
            f"Blur: {current_blur:02d}  FPS: {fps:4.1f}  {music.status_text()}  "
            "D: landmark  M: mute  ESC: keluar",
            (16, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (170, 170, 180), 1, cv2.LINE_AA,
        )

        cv2.imshow("Foto Kita Blur Dance", img)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        if key in (ord("d"), ord("D")):
            show_landmarks = not show_landmarks
        if key in (ord("m"), ord("M")):
            music.toggle_mute()
finally:
    music.close()
    tracker.close()
    cap.release()
    cv2.destroyAllWindows()
