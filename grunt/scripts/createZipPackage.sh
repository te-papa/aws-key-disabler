PACKAGE_NAME=AccessKeyRotationPackage.zip

echo
echo starting ZIP packaging...
echo =================================== 

CURRENT_DIR=`pwd`
echo CURRENT_DIR=$CURRENT_DIR

#cd ../lambda/lib/python2.6/site-packages/
#zip -r ../../../../releases/$PACKAGE_NAME boto

cd $CURRENT_DIR/../releases
zip -j $PACKAGE_NAME ../lambda/build/RotateAccessKey.py

echo
echo DONE!
