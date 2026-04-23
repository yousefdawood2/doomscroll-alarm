# ☠️ Doomscrolling Alarm

> **Stop staring at your phone.** A real-time gaze detection alarm that catches you doomscrolling — and won't shut up until you look up.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=flat-square&logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-latest-orange?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey?style=flat-square)

---

## 🧠 How It Works

Uses your webcam + **MediaPipe Face Mesh** to track your eye gaze in real time.

| State | Result |
|-------|--------|
| 👀 Looking at camera | ✅ Safe |
| 📱 Looking down at phone (5 sec) | 🔊 Alarm triggers |
| 👀 Look back up | 🔇 Alarm stops instantly |

No data is sent anywhere. Everything runs **100% locally**.

---

## 🚀 Getting Started

### Install dependencies
```bash
pip install opencv-python numpy mediapipe
```

### Run
```bash
python doomscroll_alarm.py
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `P` | Pause / Resume |
| `R` | Reset stats |
| `+` | Raise alarm threshold |
| `-` | Lower alarm threshold |

---

## 🖥️ Features

- 👁️ **Gaze detection** — knows if you're looking at your phone vs the screen
- 📊 **Live HUD** — shows session time, scroll time, alarms fired & doom meter
- 🔊 **Continuous alarm** — loud siren that only stops when you look up
- 📟 **Terminal log** — real-time event log with timestamps
- 🎛️ **Adjustable threshold** — default 5 seconds, change with `+` / `-`
- 💀 **Session summary** — shows your doomscroll % when you quit

---

## 📦 Requirements

```
opencv-python
numpy
mediapipe
```

---

## 💡 Inspiration

Inspired by the viral TikTok trend of coding apps to fight doomscrolling addiction.  
Built as a fun experiment with computer vision & real-time face tracking.

---

## 📄 License

MIT — do whatever you want with it.
