import os

# Qt tests run headless (also in CI).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
