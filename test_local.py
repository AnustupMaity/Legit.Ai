import sys
import os

sys.path.insert(0, os.path.abspath("api"))

from backend.model.text_detector import _classify, detect_text

print("Testing 'click here to win'")
print(detect_text("click here to win"))

print("Testing normal text")
print(detect_text("This is a normal article about the stock market."))
