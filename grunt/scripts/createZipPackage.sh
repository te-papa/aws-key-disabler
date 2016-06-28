echo
echo "**************************************************"
echo "**************************************************"
echo "CREATING ZIP PACKAGE for deployment..."
echo "**************************************************"
echo "**************************************************"
echo
SCRIPT=`basename "$0"`

echo "STEP1: [${SCRIPT}]"
echo starting ZIP packaging...

PACKAGE_NAME=AccessKeyRotationPackage.zip
echo PACKAGE_NAME=$PACKAGE_NAME
echo

CURRENT_DIR=`pwd`
echo CURRENT_DIR=$CURRENT_DIR

cd $CURRENT_DIR/../releases
zip -j $PACKAGE_NAME ../lambda/build/RotateAccessKey.py

echo
echo "**************************************************"
echo "**************************************************"
echo "SUCCESSFULLY created LAMBDA ZIP PACKAGE!!"
echo "**************************************************"
echo "**************************************************"
echo
sleep 5
