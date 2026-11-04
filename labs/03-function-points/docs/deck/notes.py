#!/usr/bin/env python3
"""Add speaker notes from speech.md to a pptx: python notes.py <speech.md> <in.pptx>"""

import re, sys
from pptx import Presentation

speech, path = sys.argv[1:3]
text = open(speech, encoding="utf-8").read()
notes = {
    int(n): body.strip()
    for n, body in re.findall(r"^## Слайд (\d+)\..*?\n(.*?)(?=^## |\Z)", text, re.S | re.M)
}
prs = Presentation(path)
assert len(prs.slides) == len(notes), (len(prs.slides), len(notes))
for i, slide in enumerate(prs.slides, 1):
    slide.notes_slide.notes_text_frame.text = notes[i]
prs.save(path)
print(f"{len(notes)} notes -> {path}")
