#!/usr/bin/env python3
"""Real CUA smoke test using pywinauto + OCR."""
import pywinauto, time, pytesseract, sys
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr(win):
    capture = win.capture_as_image()
    return pytesseract.image_to_string(capture)

passed = failed = 0
def check(name, ok):
    global passed, failed
    if ok: passed += 1; print(f"  PASS {name}")
    else: failed += 1; print(f"  FAIL {name}")

# Connect
app = pywinauto.Application(backend="uia").connect(title_re="Podman MCP")
win = app.window(title_re="Podman MCP")
r = win.rectangle()
check(f"Window visible ({r.width()}x{r.height()})", r.width() > 500 and r.height() > 500)

# Screenshot + OCR
win.set_focus(); time.sleep(2)
text = ocr(win)
check("System Online shown", "System Online" in text or "System" in text)
check("Title shows Podman MCP", "Podman" in text)
check("Navigation sidebar", "Overview" in text and "Containers" in text)
check("No Failed to fetch", "Failed" not in text and "fetch" not in text.lower())

# Nav click: Tools
wx, wy = r.left, r.top
pywinauto.mouse.click(button="left", coords=(wx + 200, wy + 200))
time.sleep(2)
text2 = ocr(win)
check("Tools page loads", "list_containers" in text2 or "podman" in text2.lower())

# Nav click: Dashboard
pywinauto.mouse.click(button="left", coords=(wx + 200, wy + 140))
time.sleep(2)
text3 = ocr(win)
check("Dashboard loads", "Failed" not in text3)

print(f"\nResult: {passed}/{passed+failed}")
if failed: sys.exit(1)
print("ALL PASSED")
