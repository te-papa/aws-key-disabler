echo
echo "**************************************************"
echo "**************************************************"
echo "DEPLOYING LAMBDA IAM Policy and Role..."
echo "**************************************************"
echo "**************************************************"
echo
SCRIPT=`basename "$0"`

LAMBDA_POLICY_NAME=$1
LAMBDA_ROLE_NAME=$2
REGION=$3

echo running script with inputs:
echo LAMBDA_POLICY_NAME=$LAMBDA_POLICY_NAME
echo LAMBDA_ROLE_NAME=$LAMBDA_ROLE_NAME
echo REGION=$REGION

#=============================================

echo
echo "STEP1: [${SCRIPT}]"
echo creating IAM $LAMBDA_POLICY_NAME policy...

EXISTS=$(aws iam list-policies --query "length(Policies[?PolicyName=='$LAMBDA_POLICY_NAME'])")
if [[ $EXISTS -eq 0 ]]; then
  LAMBDA_ACCESS_KEY_ROTATION_POLICY=$(python -c """import json; print json.dumps({
      'Version': '2012-10-17',
      'Statement': [
          {
              'Effect': 'Allow',
              'Action': [
                  'logs:CreateLogGroup',
                  'logs:CreateLogStream',
                  'logs:PutLogEvents'
              ],
              'Resource': 'arn:aws:logs:*:*:*'
          },
          {
              'Effect': 'Allow',
              'Action': [
                  'iam:ListUsers',
                  'iam:ListGroupsForUser',
                  'iam:ListAccessKeys',
                  'iam:UpdateAccessKey'
              ],
              'Resource': '*'
          },
          {
              'Effect': 'Allow',
              'Action': [
                  'ses:SendEmail'
              ],
              'Resource': '*'
          }
      ]
  })""")

  # create the execution role and save its ARN for later:
  LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN=$(aws iam create-policy \
                                            --region $REGION \
                                            --policy-name $LAMBDA_POLICY_NAME \
                                            --policy-document "$LAMBDA_ACCESS_KEY_ROTATION_POLICY" \
                                            --output text \
                                            --query 'Policy.Arn')

  echo LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN=$LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN
else
  LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN=$(aws iam list-policies --output text --query "Policies[?PolicyName=='$LAMBDA_POLICY_NAME'].Arn")
  echo policy $LAMBDA_POLICY_NAME already exists:
  echo $LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN
fi

#=============================================

echo
echo "STEP2: [${SCRIPT}]"
echo creating IAM $LAMBDA_ROLE_NAME role...

EXISTS=$(aws iam list-roles --query "length(Roles[?RoleName=='$LAMBDA_ROLE_NAME'])")
if [[ $EXISTS -eq 0 ]]; then
  ASSUME_ROLE_POLICY=$(python -c """import json; print json.dumps({
    'Version': '2012-10-17',
    'Statement': [
      {
        'Effect': 'Allow',
        'Principal': {
          'Service': 'lambda.amazonaws.com'
        },
        'Action': 'sts:AssumeRole'
      }
    ]
  })""")

  # create the execution role and save its ARN for later:
  LAMBDA_ACCESS_KEY_ROTATION_ROLE_ARN=$(aws iam create-role \
                                          --region $REGION \
                                          --role-name "$LAMBDA_ROLE_NAME" \
                                          --assume-role-policy-document "$ASSUME_ROLE_POLICY" \
                                          --output text \
                                          --query 'Role.Arn')

  echo LAMBDA_ACCESS_KEY_ROTATION_ROLE_ARN=$LAMBDA_ACCESS_KEY_ROTATION_ROLE_ARN
else
  LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN=$(aws iam list-roles --output text --query "Roles[?RoleName=='$LAMBDA_ROLE_NAME'].Arn")
  echo role $LAMBDA_ROLE_NAME already exists:
  echo $LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN
fi

#=============================================

echo
echo "STEP3: [${SCRIPT}]"
echo attaching IAM $LAMBDA_POLICY_NAME policy to $LAMBDA_ROLE_NAME role...

ATTACHED=$(aws iam list-attached-role-policies --role-name $LAMBDA_ROLE_NAME --query "length(AttachedPolicies[?PolicyName=='$LAMBDA_POLICY_NAME'])")
if [[ $ATTACHED -eq 0 ]]; then
  aws iam attach-role-policy \
    --region $REGION \
    --policy-arn "$LAMBDA_ACCESS_KEY_ROTATION_POLICY_ARN" \
    --role-name "$LAMBDA_ROLE_NAME"
else
  ATTACHMENT=$(aws iam list-attached-role-policies --role-name $LAMBDA_ROLE_NAME --query "AttachedPolicies[?PolicyName=='$LAMBDA_POLICY_NAME']")
  echo policy $LAMBDA_POLICY_NAME already attached to role $LAMBDA_ROLE_NAME:
  echo $ATTACHMENT
fi

echo

echo "**************************************************"
echo "**************************************************"
echo "SUCCESSFULLY deployed LAMBDA IAM Policy and Role!!"
echo "**************************************************"
echo "**************************************************"
echo
sleep 5
