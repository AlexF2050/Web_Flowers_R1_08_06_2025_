import os
import shutil

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".pyc"):
            os.remove(os.path.join(root, file))
    for dir in dirs:
        if dir == "__pycache__":
            shutil.rmtree(os.path.join(root, dir))