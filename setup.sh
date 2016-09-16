# To run the VQA Browser, you need MSCOCO images.
# If you already have MSCOCO images in you local directory, simply make a
# simulink to the directory. You can also download images and generate
# simulink by running this script.
cd data
./get_mscoco.sh
cd ..

cd static
ln -s ../data/MSCOCO/images
cd ..
