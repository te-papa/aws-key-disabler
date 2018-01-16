

# AWS Lambda - IAM Access Key Disabler

![Image of KeyIcon](/docs/images/GitHubTepapaKeyIcon.jpg)

The AWS Key disabler is a Lambda Function that disables AWS IAM User Access Keys after a set amount of time in order to reduce the risk associated with old access keys.

## AWS Lambda Architecture

![Image of Arch](/docs/images/GitHubTepapaLambda.png)

## SysOps Output for EndUser

![Image of iPhoneEmail](/docs/images/GitHubTepapaOutput.png)

## Developer Toolchain

![Image of Toolchain](/docs/images/GitHubTepapaToolchain.png)

## Current Limitations

* A report containing the output (json) of scan will be sent to a single defined sysadmin account, refer to the `report_to` attribute in the `/grunt/package.json` build configuration file.
* Keys are only disabled, not deleted nor replaced

## Prerequisites

This script requires the following components to run.
* Node.js with NPM installed https://nodejs.org/en/
* Gruntjs installed http://gruntjs.com/
* AWSCLI commandline tool installed https://aws.amazon.com/cli/

It also assumes that you have an AWS account with SES enabled, ie domain verified and sandbox mode removed.

## Installation instructions

These instructions are for OSX. Your mileage may vary on Windows and other \*nix.

1. Grab yourself a copy of this script
2. Navigate into the `/grunt` folder
3. Setup the Grunt task runner, e.g. install its deps: `npm install`
4. Fill in the following information in `/grunt/package.json`
	1. Set the `aws_account_number` value to your AWS account id found on https://portal.aws.amazon.com/gp/aws/manageYourAccount
	2. Set the `first_warning` and `last_warning` to the age that the key has to be in days to trigger a warning. These limits trigger an email send to `report_to`
	3. Set the `expiry` to the age in days when the key expires. At this age the key is disabled and an email is triggered to `report_to` notifying this change
	4. Set the `serviceaccount` to the account username you want the script to ignore
	5. Set the `exclusiongroup` to the name of a group assigned to users you want the script to ignore.
	6. Set the `send_completion_report` value to `True` to enable email delivery via SES
	7. Set the `report_to` value to the email address you'd like to receive deletion reports to
	8. Set the `report_from` value to the email address you'd like to use as the sender address for deletion reports. Note that the domain for this needs to be verified in AWS SES.
	9. Set the `deployment_region` to a region that supports Lambda. 
	10 Set the `email_region` to the region that supports SES. Also ensure that the region has SES sandbox mode disabled.
		* See the AWS Region table for support https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/
5. Ensure you can successfully connect to AWS from the CLI, eg run `aws iam get-user` to verify successful connection
6. from the `/grunt` directory run `grunt bumpup && grunt deployLambda` to bump your version number and perform a build/deploy of the Lambda function to the selected region

## Invoke the Lambda Function manually from the commandline using the AWSCLI

Execute the lambda function by name, `AccessKeyRotation`, logging the output of the scan to a file called `scan.report.log`:

`aws lambda invoke --function-name AccessKeyRotation scan.report.log --region us-east-1`
```javascript
{
    "StatusCode": 200
}
```

Use `jq` to render the contents of the `scan.report.log` to the console:

`jq '.' scan.report.log`
```javascript
{
  "reportdate": "2016-06-26 10:37:24.071091",
  "users": [
    {
      "username": "TestS3User",
      "userid": "1",
      "keys": [
        {
          "age": 72,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************Q3GA1"
        },
        {
          "age": 12,
          "changed": false,
          "state": "key is still young",
          "accesskeyid": "**************F3AA2"
        }
      ]
    },
    {
      "username": "BlahUser22",
      "userid": "2",
      "keys": []
    },
    {
      "username": "LambdaFake1",
      "userid": "3",
       "keys": [
        {
          "age": 23,
          "changed": false,
          "state": "key is due to expire in 1 week (7 days)",
          "accesskeyid": "**************DFG12"
        },
        {
          "age": 296,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************4ZASD"
        }
      ]
    },
    {
      "username": "apiuser49",
      "userid": "4",
       "keys": [
        {
          "age": 30,
          "changed": true,
          "state": "key is now EXPIRED! Changing key to INACTIVE state",
          "accesskeyid": "**************ER2E2"
        },
        {
          "age": 107,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************AWQ4K"
        }
      ]
    },
    {
      "username": "UserEMRKinesis",
      "userid": "5",
       "keys": [
        {
          "age": 30,
          "changed": false,
          "state": "key is now EXPIRED! Changing key to INACTIVE state",
          "accesskeyid": "**************MGB41A"
        }
      ]
    },
    {
      "username": "CDN-Drupal",
      "userid": "6",
       "keys": [
        {
          "age": 10,
          "changed": false,
          "state": "key is still young",
          "accesskeyid": "**************ZDSQ5A"
        },
        {
          "age": 5,
          "changed": false,
          "state": "key is still young",
          "accesskeyid": "**************E3ODA"
        }
      ]
    },
    {
      "username": "ChocDonutUser1",
      "userid": "7",
       "keys": [
        {
          "age": 59,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************CSA123"
        }
      ]
    },
    {
      "username": "ChocDonut2",
      "userid": "8",
       "keys": [
        {
          "age": 60,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************FDGD2"
        }
      ]
    },
    {
      "username": "admin.skynet@cyberdyne.systems.com",
      "userid": "9",
       "keys": [
        {
          "age": 45,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************BLQ5GJ"
        },
        {
          "age": 71,
          "changed": false,
          "state": "key is already in an INACTIVE state",
          "accesskeyid": "**************GJFF53"
        }
      ]
    }
  ]
}
```

## Additional configuration option

* You can choose to set the message used for each warning and the final disabling by changing the values under `key_disabler.keystates.<state>.message`
* You can change the length of masking under `key_disabler.mask_accesskey_length`. The access keys are 20 characters in length.

## Troubleshooting

This script is provided as is. We are happy to answer questions as time allows but can't give any promises.

If things don't work ensure that:
* You can authenticate successfully against AWS using the AWSCLI commandline tool
* SES is not in sandbox mode and the sender domain has been verified
* The selected region provides both Lambda and SES https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/

## Bonus Points

Once the Lambda Function has been successfully deployed - the following commands can be performed:

1. `aws lambda list-functions`
2. `openssl dgst -binary -sha256 ..\Releases\AccessKeyRotationPackage.1.0.18.zip | openssl base64`
3. `aws lambda invoke --function-name AccessKeyRotation report.log --region us-east-1`
4. `jq '.' report.log`
5. `jq '.users[] | select(.username=="johndoe")' report.log`
5. `jq '.' report.log | grep age | cut -d':' -f2 | sort -n`

## Bonus Bonus Points

1. `jq 'def maximal_by(f): (map(f) | max) as $mx | .[] | select(f == $mx); .users | maximal_by(.keys[].age)' report.log`
2. `jq 'def minimal_by(f): (map(f) | min) as $mn | .[] | select(f == $mn); .users | minimal_by(.keys[].age)' report.log`
