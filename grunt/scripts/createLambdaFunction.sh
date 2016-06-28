echo
echo "**************************************************"
echo "**************************************************"
echo "DEPLOYING LAMBDA Function..."
echo "**************************************************"
echo "**************************************************"
echo
SCRIPT=`basename "$0"`

LAMBDA_ZIP_PACKAGE_NAME=$1
BUILD_VERSION=$2
FUNCTION_NAME=$3
LAMBDA_ROLE_NAME=$4
LAMBDA_TIMEOUT=$5
LAMBDA_MEMORY=$6
REGION=$7

echo running script with inputs:
echo LAMBDA_ZIP_PACKAGE_NAME=$LAMBDA_ZIP_PACKAGE_NAME
echo BUILD_VERSION=$BUILD_VERSION
echo FUNCTION_NAME=$FUNCTION_NAME
echo LAMBDA_ROLE_NAME=$LAMBDA_ROLE_NAME
echo LAMBDA_TIMEOUT=$LAMBDA_TIMEOUT
echo LAMBDA_MEMORY=$LAMBDA_MEMORY
echo REGION=$REGION
echo

echo "STEP1: [${SCRIPT}]"
echo deploying $LAMBDA_ZIP_PACKAGE_NAME version $BUILD_VERSION lambda ZIP package...
echo

LAMBDA_HANDLER=RotateAccessKey.lambda_handler

EXISTS=$(aws lambda list-functions --region $REGION --query "length(Functions[?FunctionName=='$FUNCTION_NAME'])")
if [[ $EXISTS -eq 1 ]]; then
  echo existing lambda function $FUNCTION_NAME found, deleting first...
  echo
  aws lambda delete-function --function-name $FUNCTION_NAME --region $REGION
fi

echo creating lambda function $FUNCTION_NAME...
echo

LAMBDA_ACCESS_KEY_ROTATION_ROLEARN=$(aws iam get-role --role-name $LAMBDA_ROLE_NAME --output text --query Role.Arn)
echo LAMBDA_ACCESS_KEY_ROTATION_ROLEARN=$LAMBDA_ACCESS_KEY_ROTATION_ROLEARN

LAMBDA_FUNCTION_ARN=$(aws lambda create-function \
                        --region $REGION \
                        --runtime python2.7 \
                        --role $LAMBDA_ACCESS_KEY_ROTATION_ROLEARN \
                        --description "Deactivates old IAM Access Keys - ${BUILD_VERSION}" \
                        --timeout $LAMBDA_TIMEOUT \
                        --memory-size $LAMBDA_MEMORY \
                        --handler $LAMBDA_HANDLER \
                        --zip-file fileb://../releases/$LAMBDA_ZIP_PACKAGE_NAME \
                        --function-name $FUNCTION_NAME \
                        --output text \
                        --query 'FunctionArn')

echo LAMBDA_FUNCTION_ARN=$LAMBDA_FUNCTION_ARN

echo

echo "**************************************************"
echo "**************************************************"
echo "SUCCESSFULLY deployed LAMBDA Function ZIP Package!!"
echo "**************************************************"
echo "**************************************************"
echo
sleep 5
