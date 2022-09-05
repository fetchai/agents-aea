import os

for dir, sub_dirs, files in os.walk("packages"):
	if "__init__.py" not in files:
		print(dir)