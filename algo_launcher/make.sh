rm -rf  *.pyc logs
pyinstaller -F launcher.py
mkdir algo_launcher
cp ./dist/launcher ./algo_launcher/
cp -r adaptor ./algo_launcher
cp -r doc ./algo_launcher
cp *.json *.so *.dat ./algo_launcher/
cd ./gpu_viewer_tool/
./make.sh
cd ..
cp ./gpu_viewer_tool/gpu_worker_viewer ./algo_launcher/
rm ./gpu_viewer_tool/gpu_worker_viewer
tar zcvf algo_launcher.tar.gz algo_launcher
rm -rf dist  build algo_launcher *.spec
