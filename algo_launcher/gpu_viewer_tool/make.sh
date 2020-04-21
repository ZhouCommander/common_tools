rm *.pyc
pyinstaller -F gpu_worker_viewer.py
cp ./dist/gpu_worker_viewer .
rm -rf build dist *.spec
