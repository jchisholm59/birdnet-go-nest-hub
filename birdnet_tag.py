"""Stamp a label (e.g. "Home 08:32") in the upper-left corner of a bird photo, for the Nest Hub.

Run by Home Assistant's shell_command (see README.md, "Photo tag"):
    python3 /config/birdnet_tag.py <photo url> <label> <output .jpg>
Uses only the Python and Pillow that come with Home Assistant. Exits non-zero on any failure, and the automation then
shows the untouched photo instead.
"""
import io
import os
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFont

url, label, out = sys.argv[1:4]
req = urllib.request.Request(url, headers={"User-Agent": "birdnet-go-nest-hub"})
with urllib.request.urlopen(req, timeout=15) as r:
    img = Image.open(io.BytesIO(r.read())).convert("RGB")

# BirdNET-Go's photos are small (320x240); the Hub scales them up anyway. Doing it here keeps the label sharp.
if img.height < 600:
    img = img.resize((round(img.width * 600 / img.height), 600), Image.LANCZOS)

w, h = img.size
font = ImageFont.load_default(size=max(12, round(h * 0.08)))
pad = round(font.size * 0.4)
margin = round(min(w, h) * 0.03)
left, top, right, bottom = ImageDraw.Draw(img).textbbox((0, 0), label, font=font)
box = (margin, margin, margin + (right - left) + 2 * pad, margin + (bottom - top) + 2 * pad)

# Translucent dark box, white text: readable on sky, snow and leaves alike.
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
d = ImageDraw.Draw(overlay)
d.rounded_rectangle(box, radius=pad, fill=(0, 0, 0, 150))
d.text((box[0] + pad - left, box[1] + pad - top), label, font=font, fill=(255, 255, 255, 255))
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

os.makedirs(os.path.dirname(out), exist_ok=True)
tmp = out + ".tmp"
img.save(tmp, "JPEG", quality=90)
os.replace(tmp, out)   # the Hub never fetches a half-written file
