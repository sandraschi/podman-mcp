#!/usr/bin/env python3
"""Final CUA verification — screenshot + OCR to confirm frontend reaches backend."""
import pywinauto, time, pytesseract, sys
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

passed = failed = 0
def check(name, ok):
    global passed, failed
    if ok: passed += 1; print(f"  PASS {name}")
    else: failed += 1; print(f"  FAIL {name}")

# Connect to window
app = pywinauto.Application(backend="uia").connect(title_re="Podman MCP")
win = app.window(title_re="Podman MCP")
r = win.rectangle()
check(f"Window {r.width()}x{r.height()}", r.width() > 500)

# Screenshot + OCR
win.set_focus(); time.sleep(2)
text = pytesseract.image_to_string(win.capture_as_image())
print(f"\nOCR text (first 1000 chars):\n{text[:1000]}\n")

check("Podman MCP title", "Podman" in text)
check("System Online (frontend→backend OK)", "System Online" in text or "Connected" in text)
check("No Failed to fetch error", "Failed" not in text and "fetch" not in text.lower())

# Nav click to Containers
wx, wy = r.left, r.top
pywinauto.mouse.click(button="left", coords=(wx + 120, wy + 180))
time.sleep(2)
text2 = pytesseract.image_to_string(win.capture_as_image())
check("Containers page loads", "Containers" in text2 or "container" in text2.lower())

# Nav to Dashboard
pywinauto.mouse.click(button="left", coords=(wx + 120, wy + 140))
time.sleep(2)
text3 = pytesseract.image_to_string(win.capture_as_image())
check("Dashboard back without error", "Failed" not in text3)

print(f"\nResult: {passed}/{passed+failed}")
if failed: sys.exit(1)
print("ALL PASSED")
