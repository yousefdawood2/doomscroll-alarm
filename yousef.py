"""
╔══════════════════════════════════════════╗
║      DOOMSCROLLING ALARM v1.0            ║
║      بايثون + OpenCV + Face Detection    ║
╚══════════════════════════════════════════╝

Requirements:
    pip install opencv-python numpy

Run:
    python doomscroll_alarm.py
"""

import cv2
import numpy as np
import time
import os
import sys

# ─── SETTINGS ────────────────────────────────────────────────
ALARM_THRESHOLD   = 5       # ثواني قبل ما الـ alarm يطلع
COOLDOWN_SECS     = 5       # ثواني بعد الـ alarm قبل ما يرجع يشتغل
WINDOW_TITLE      = "DOOMSCROLLING ALARM  |  press Q to quit"
FACE_SCALE        = 1.1
FACE_NEIGHBORS    = 6
FACE_MIN_SIZE     = (80, 80)

# ─── COLORS (BGR) ────────────────────────────────────────────
GREEN   = (0,   255,  65)
RED     = (0,    51, 255)
YELLOW  = (0,   221, 255)
WHITE   = (255, 255, 255)
BLACK   = (0,     0,   0)
DARK_BG = (15,   15,  15)
DIM_GRN = (0,   120,  30)

# ─── LOAD FACE CASCADE ───────────────────────────────────────
def load_cascade():
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        print("[ERROR] لم يتم العثور على ملف haarcascades.")
        print("        تأكد إن opencv-python متنصب صح.")
        sys.exit(1)
    return cv2.CascadeClassifier(cascade_path)

# ─── HELPERS ─────────────────────────────────────────────────
def fmt_time(secs):
    """Convert seconds to MM:SS string"""
    secs = int(max(0, secs))
    return f"{secs//60:02d}:{secs%60:02d}"

def draw_text(img, text, pos, font_scale=0.5, color=GREEN,
              thickness=1, font=cv2.FONT_HERSHEY_SIMPLEX):
    cv2.putText(img, text, pos, font, font_scale, BLACK, thickness+2, cv2.LINE_AA)
    cv2.putText(img, text, pos, font, font_scale, color,  thickness,  cv2.LINE_AA)

def draw_corner_brackets(img, x, y, w, h, color, size=16, thick=2):
    """Draw ⌜⌝⌞⌟ corner brackets around a rectangle"""
    pts = [
        ((x,     y),      (x+size, y),      (x,     y+size)),
        ((x+w,   y),      (x+w-size, y),    (x+w,   y+size)),
        ((x,     y+h),    (x+size, y+h),    (x,     y+h-size)),
        ((x+w,   y+h),    (x+w-size, y+h),  (x+w,   y+h-size)),
    ]
    for corner, p1, p2 in pts:
        cv2.line(img, corner, p1, color, thick, cv2.LINE_AA)
        cv2.line(img, corner, p2, color, thick, cv2.LINE_AA)

def draw_progress_bar(img, x, y, w, h, pct, bg_color, fill_color):
    """Draw a progress bar"""
    cv2.rectangle(img, (x, y), (x+w, y+h), bg_color, -1)
    cv2.rectangle(img, (x, y), (x+w, y+h), fill_color, 1)
    fill_w = int(w * min(pct, 1.0))
    if fill_w > 0:
        cv2.rectangle(img, (x, y+1), (x+fill_w, y+h-1), fill_color, -1)
        # bright edge
        cv2.line(img, (x+fill_w, y+1), (x+fill_w, y+h-2), WHITE, 1)

def draw_scanlines(img, alpha=0.07):
    """Overlay horizontal scanlines for CRT effect"""
    h, w = img.shape[:2]
    for row in range(0, h, 4):
        cv2.line(img, (0, row), (w, row), BLACK, 1)

import threading

# ─── CONTINUOUS ALARM ────────────────────────────────────────
_alarm_event = threading.Event()   # set = شغّل الصفارة، clear = وقّف

def _alarm_worker():
    """Thread يشتغل باستمرار ويصفّر طول ما الـ event مضبوط"""
    if sys.platform == "win32":
        import winsound
        while True:
            if _alarm_event.is_set():
                winsound.Beep(1200, 150)
                winsound.Beep(900,  150)
            else:
                time.sleep(0.05)
    else:
        try:
            import numpy as np
            import pyaudio
            pa = pyaudio.PyAudio()
            stream = pa.open(format=pyaudio.paInt16, channels=1,
                             rate=44100, output=True)
            sample_rate = 44100
            chunk = 512
            t = 0
            while True:
                if _alarm_event.is_set():
                    freq = 1200 if (t // (sample_rate // 4)) % 2 == 0 else 900
                    samples = (32767 * np.sin(
                        2 * np.pi * freq *
                        np.arange(t, t + chunk) / sample_rate
                    )).astype(np.int16)
                    stream.write(samples.tobytes())
                    t += chunk
                else:
                    t = 0
                    time.sleep(0.05)
        except Exception:
            # fallback بدون pyaudio
            while True:
                if _alarm_event.is_set():
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                    time.sleep(0.1)
                else:
                    time.sleep(0.05)

def start_alarm_thread():
    t = threading.Thread(target=_alarm_worker, daemon=True)
    t.start()

def alarm_on():
    _alarm_event.set()

def alarm_off():
    _alarm_event.clear()


# ─── TERMINAL LOG ─────────────────────────────────────────────
class TerminalLog:
    def __init__(self, max_lines=5):
        self.lines  = []
        self.max    = max_lines
        self.colors = []   # per line color

    def add(self, msg, color=GREEN):
        ts = time.strftime("%H:%M:%S")
        self.lines.append(f"[{ts}] {msg}")
        self.colors.append(color)
        if len(self.lines) > self.max:
            self.lines.pop(0)
            self.colors.pop(0)

    def draw(self, img, x, y, line_h=16):
        for i, (line, col) in enumerate(zip(self.lines, self.colors)):
            draw_text(img, line, (x, y + i * line_h),
                      font_scale=0.38, color=col, thickness=1)

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    cascade = load_cascade()
    cap     = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] مش قادر يفتح الكاميرا. تأكد إنها متاحة.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # ابدأ thread الصفارة في الخلفية
    start_alarm_thread()

    global ALARM_THRESHOLD

    # ── State ──────────────────────────────────────────────────
    session_start   = time.time()
    doom_secs       = 0.0
    total_scroll    = 0.0
    alarm_count     = 0
    alarm_active    = False
    alarm_start     = 0.0
    paused          = False
    last_tick       = time.time()
    face_visible    = False
    log             = TerminalLog(max_lines=5)

    log.add("> system initialized. camera active.", GREEN)
    log.add(f"> alarm threshold: {ALARM_THRESHOLD}s", GREEN)
    log.add("> monitoring for doomscrolling behavior...", GREEN)

    print(f"\n{'='*52}")
    print("  DOOMSCROLLING ALARM  |  اضغط Q للخروج")
    print(f"{'='*52}\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)   # mirror
        fh, fw = frame.shape[:2]
        now    = time.time()
        dt     = now - last_tick
        last_tick = now

        # ── Face Detection ─────────────────────────────────────
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray  = cv2.equalizeHist(gray)
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor  = FACE_SCALE,
            minNeighbors = FACE_NEIGHBORS,
            minSize      = FACE_MIN_SIZE,
            flags        = cv2.CASCADE_SCALE_IMAGE
        )

        face_visible = len(faces) > 0

        # ── Doom Logic ─────────────────────────────────────────
        # وشك مش ظاهر = بتبص على التلفون
        if not paused:
            if not face_visible:
                doom_secs    += dt
                total_scroll += dt
            else:
                doom_secs = max(0.0, doom_secs - dt * 0.5)

        # ── Alarm Trigger ──────────────────────────────────────
        # صفّر لما تبص على التلفون (وشك يختفي) وتعدي الـ threshold
        if doom_secs >= ALARM_THRESHOLD and not face_visible and not alarm_active:
            alarm_active = True
            alarm_count += 1
            log.add(f"> !! ALARM #{alarm_count} TRIGGERED !! ارفع راسك!", RED)
            alarm_on()

        # وقّف فور ما وشك يظهر تاني
        if alarm_active and face_visible:
            alarm_active = False
            doom_secs    = 0.0
            alarm_off()
            log.add("> alarm stopped. welcome back!", YELLOW)



        # ─────────────────────────────────────────────────────
        # BUILD THE HUD
        # ─────────────────────────────────────────────────────
        hud_w = 230
        hud   = np.zeros((fh, hud_w, 3), dtype=np.uint8)
        hud[:] = DARK_BG

        # left border glow
        cv2.rectangle(hud, (0, 0), (hud_w-1, fh-1), DIM_GRN, 1)
        cv2.line(hud, (1, 0), (1, fh), (0, 40, 10), 1)

        cy = 18

        # ── Title
        cv2.putText(hud, "DOOMSCROLL", (10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREEN, 1, cv2.LINE_AA)
        cy += 16
        cv2.putText(hud, "DETECTOR v1.0", (10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, DIM_GRN, 1, cv2.LINE_AA)
        cy += 12
        cv2.line(hud, (8, cy), (hud_w-8, cy), DIM_GRN, 1)
        cy += 12

        # ── Stats rows
        def stat_row(label, value, val_color=GREEN):
            nonlocal cy
            draw_text(hud, label,  (10,       cy), 0.38, DIM_GRN, 1)
            draw_text(hud, value,  (hud_w-8 - len(value)*8, cy), 0.38, val_color, 1)
            cv2.line(hud, (8, cy+4), (hud_w-8, cy+4),
                     (0, 40, 10), 1)
            cy += 18

        elapsed = now - session_start
        face_col  = GREEN  if face_visible else DIM_GRN
        face_txt  = "DETECTED" if face_visible else "NOT FOUND"
        stat_row("FACE DETECT",  face_txt,          face_col)
        stat_row("SESSION",      fmt_time(elapsed),  GREEN)
        stat_row("SCROLL TIME",  fmt_time(total_scroll), YELLOW)
        stat_row("ALARMS FIRED", str(alarm_count),   RED if alarm_count else GREEN)

        status_txt = "!! DOOMSCROLLING !!" if alarm_active else \
                     "WARNING"             if doom_secs > ALARM_THRESHOLD*0.6 else \
                     "PAUSED"              if paused else "SAFE"
        status_col = RED    if alarm_active else \
                     YELLOW if doom_secs > ALARM_THRESHOLD*0.6 else \
                     YELLOW if paused else GREEN
        stat_row("STATUS", status_txt, status_col)

        cy += 2
        # ── Doom Meter label
        draw_text(hud, "DOOM METER", (10, cy), 0.38, DIM_GRN)
        cy += 14

        pct = doom_secs / ALARM_THRESHOLD
        bar_col = RED if pct > 0.8 else YELLOW if pct > 0.5 else GREEN
        draw_progress_bar(hud, 10, cy, hud_w-20, 12, pct, (0,30,8), bar_col)
        cy += 24

        # ── Threshold info
        draw_text(hud, f"THRESHOLD: {ALARM_THRESHOLD}s", (10, cy), 0.35, DIM_GRN)
        cy += 16
        draw_text(hud, f"DOOM: {doom_secs:.1f}s / {ALARM_THRESHOLD}s", (10, cy), 0.35, bar_col)
        cy += 20

        cv2.line(hud, (8, cy), (hud_w-8, cy), DIM_GRN, 1)
        cy += 12

        # ── Controls help
        controls = [
            "[Q] QUIT",
            "[P] PAUSE/RESUME",
            "[R] RESET STATS",
            "[+] RAISE THRESHOLD",
            "[-] LOWER THRESHOLD",
        ]
        for c in controls:
            draw_text(hud, c, (10, cy), 0.33, DIM_GRN)
            cy += 13

        cv2.line(hud, (8, cy+4), (hud_w-8, cy+4), DIM_GRN, 1)
        cy += 14

        # ── Terminal log
        draw_text(hud, "TERMINAL LOG:", (10, cy), 0.35, DIM_GRN)
        cy += 14
        log.draw(hud, 6, cy, line_h=14)

        # ─────────────────────────────────────────────────────
        # DRAW ON CAMERA FRAME
        # ─────────────────────────────────────────────────────

        # Draw face boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), GREEN, 2)
            glow = frame.copy()
            cv2.rectangle(glow, (x-2, y-2), (x+w+2, y+h+2), GREEN, 1)
            frame = cv2.addWeighted(frame, 0.85, glow, 0.15, 0)
            draw_corner_brackets(frame, x, y, w, h, WHITE, size=14, thick=2)

        # ── ALARM BANNER ──────────────────────────────────────
        if alarm_active:
            flicker = int(now * 8) % 2 == 0
            if flicker:
                banner_h = 44
                overlay  = frame.copy()
                cv2.rectangle(overlay, (0, 0), (fw, fh), (0, 0, 180), -1)
                frame = cv2.addWeighted(frame, 0.75, overlay, 0.25, 0)
                cv2.rectangle(frame, (fw//2-180, 10), (fw//2+180, 10+banner_h),
                              RED, -1)
                cv2.rectangle(frame, (fw//2-180, 10), (fw//2+180, 10+banner_h),
                              WHITE, 2)
                cv2.putText(frame, "!! DOOMSCROLLING ALARM !!",
                            (fw//2-170, 10+banner_h-12),
                            cv2.FONT_HERSHEY_DUPLEX, 0.75, WHITE, 2, cv2.LINE_AA)

        # ── TOP STATUS BAR ────────────────────────────────────
        cv2.rectangle(frame, (0, 0), (fw, 22), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, 0), (fw, 22), DIM_GRN, 1)
        ts_str = time.strftime("%H:%M:%S")
        draw_text(frame, f"DOOMSCROLL-DETECTOR  |  {ts_str}  |  "
                         f"{'PAUSED' if paused else 'MONITORING'}",
                  (8, 15), 0.4, GREEN if not paused else YELLOW)

        # ── DOOM BAR (bottom of frame) ─────────────────────────
        bar_y = fh - 18
        draw_text(frame, "DOOM:", (6, bar_y+12), 0.4, DIM_GRN)
        draw_progress_bar(frame, 55, bar_y, fw-65, 14,
                          doom_secs/ALARM_THRESHOLD,
                          (0, 20, 5), bar_col)

        # ── CRT Scanlines ─────────────────────────────────────
        draw_scanlines(frame, alpha=0.07)

        # ── Combine frame + HUD side panel ────────────────────
        combined = np.hstack([frame, hud])

        cv2.imshow(WINDOW_TITLE, combined)

        # ─────────────────────────────────────────────────────
        # KEY HANDLING
        # ─────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:
            log.add("> session ended by user.")
            break

        elif key == ord('p'):
            paused = not paused
            msg = "monitoring paused." if paused else "monitoring resumed."
            log.add(f"> {msg}", YELLOW)

        elif key == ord('r'):
            doom_secs = 0.0
            total_scroll = 0.0
            alarm_count = 0
            session_start = now
            log.add("> stats reset.", YELLOW)

        elif key == ord('+') or key == ord('='):
            ALARM_THRESHOLD = min(120, ALARM_THRESHOLD + 5)
            log.add(f"> threshold: {ALARM_THRESHOLD}s", GREEN)

        elif key == ord('-'):
            ALARM_THRESHOLD = max(5, ALARM_THRESHOLD - 5)
            log.add(f"> threshold: {ALARM_THRESHOLD}s", YELLOW)

    # ── Cleanup ────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "="*52)
    print("  SESSION SUMMARY")
    print("="*52)
    total_time = time.time() - session_start
    print(f"  Session duration : {fmt_time(total_time)}")
    print(f"  Scroll time      : {fmt_time(total_scroll)}")
    print(f"  Alarms triggered : {alarm_count}")
    pct = (total_scroll / total_time * 100) if total_time > 0 else 0
    print(f"  Doomscroll %     : {pct:.1f}%")
    print("="*52 + "\n")

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()