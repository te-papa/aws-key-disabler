echo
echo "**************************************************"
echo "**************************************************"
echo "DEPLOYING LAMBDA CRON Schedule Pattern..."
echo "**************************************************"
echo "**************************************************"
echo
SCRIPT=`basename "$0"`

FUNCTION_NAME=$1
SCHEDULE_RULE_NAME="$2"
SCHEDULE_RULE_DESC="$3"
SCHEDULE_EXPRESSION="$4"
AWS_ACCOUNT_NUMBER=$5
REGION=$6

echo running script with inputs:
echo FUNCTION_NAME=$FUNCTION_NAME
echo SCHEDULE_RULE_NAME="${SCHEDULE_RULE_NAME}"
echo SCHEDULE_RULE_DESC="${SCHEDULE_RULE_DESC}"
echo SCHEDULE_EXPRESSION="${SCHEDULE_EXPRESSION}"
echo AWS_ACCOUNT_NUMBER=$AWS_ACCOUNT_NUMBER
echo REGION=$REGION
echo

echo "STEP1: [${SCRIPT}]"
echo creating event rule with CRON pattern...
echo

EXISTS=$(aws events list-rules --region $REGION --output text --query "length(Rules[?Name=='$SCHEDULE_RULE_NAME'])")
if [[ $EXISTS -eq 0 ]]; then
  EVENT_RULE_ARN=$(aws events put-rule \
                    --name "${SCHEDULE_RULE_NAME}" \
                    --description "${SCHEDULE_RULE_DESC}" \
                    --schedule-expression "${SCHEDULE_EXPRESSION}" \
                    --region $REGION \
                    --output text \
                    --query 'RuleArn')

  echo EVENT_RULE_ARN=$EVENT_RULE_ARN
else
  EVENT_RULE_ARN=$(aws events list-rules --region $REGION --output text --query "Rules[?Name=='$SCHEDULE_RULE_NAME'].Arn")
  echo events rule $SCHEDULE_RULE_NAME already exists:
  echo $EVENT_RULE_ARN
fi

echo
echo "STEP2: [${SCRIPT}]"
echo giving InvokeFunction permission to new EventRule...
echo

aws lambda add-permission \
  --function-name $FUNCTION_NAME \
  --statement-id $FUNCTION_NAME \
  --action 'lambda:InvokeFunction' \
  --principal events.amazonaws.com \
  --source-arn $EVENT_RULE_ARN \
  --region $REGION

echo
echo "STEP3: [${SCRIPT}]"
echo binding new CRON schedule to new Lambda Function...
echo

aws events put-targets \
  --rule $SCHEDULE_RULE_NAME \
  --targets "{\"Id\" : \"1\", \"Arn\": \"arn:aws:lambda:${REGION}:${AWS_ACCOUNT_NUMBER}:function:${FUNCTION_NAME}\"}" \
  --region $REGION

echo

echo "**************************************************"
echo "**************************************************"
echo "SUCCESSFULLY deployed LAMBDA CRON Schedule Pattern!!"
echo "**************************************************"
echo "**************************************************"
echo
sleep 5
