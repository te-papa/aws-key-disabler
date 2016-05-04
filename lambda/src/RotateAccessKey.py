import boto3
from datetime import datetime
import dateutil.tz
import json
import ast

BUILD_VERSION = '@@buildversion'
AWS_REGION = '@@deploymentregion'
SERVICE_ACCOUNT_NAME = '@@serviceaccount'
EMAIL_TO_ADMIN = '@@emailreportto'
EMAIL_FROM = '@@emailreportfrom'
EMAIL_SEND_COMPLETION_REPORT = ast.literal_eval('@@emailsendcompletionreport')

# ==========================================================

# First email warning
FIRST_WARNING = @@first_warning
# Last email warning
LAST_WARNING = @@last_warning
# Days to expiry
EXPIRY = @@expiry

KEY_STATE_ACTIVE = "Active"
KEY_STATE_INACTIVE = "Inactive"


def tzutc():
    return dateutil.tz.tzutc()


def key_age(key_created_date):
    tz_info = key_created_date.tzinfo
    age = datetime.now(tz_info) - key_created_date

    print 'key age %s' % age

    key_age_str = str(age)
    if 'days' not in key_age_str:
        return 0

    days = int(key_age_str.split(',')[0].split(' ')[0])

    return days


def send_deactivate_email(email_to, username, age, access_key_id):
    client = boto3.client('ses', region_name=AWS_REGION)
    response = client.send_email(
        Source=EMAIL_FROM,
        Destination={
            'ToAddresses': [email_to]
        },
        Message={
            'Subject': {
                'Data': 'AWS IAM Access Key Rotation - Deactivation of Access Key: %s' % access_key_id
            },
            'Body': {
                'Html': {
                'Data': 'The Access Key [%s] belonging to User [%s] has been automatically deactivated due to it being %s days old' % (access_key_id, username, age)
                }
            }
        })


def send_completion_email(email_to, finished, deactivated_report):
    client = boto3.client('ses', region_name=AWS_REGION)
    response = client.send_email(
        Source=EMAIL_FROM,
        Destination={
            'ToAddresses': [email_to]
        },
        Message={
            'Subject': {
                'Data': 'AWS IAM Access Key Rotation - Lambda Function'
            },
            'Body': {
                'Html': {
                'Data': 'AWS IAM Access Key Rotation Lambda Function (cron job) finished successfully at %s\n\nDeactivation Report:\n%s' % (finished, deactivated_report)
                }
            }
        })


def lambda_handler(event, context):
    print '*****************************'
    print 'RotateAccessKey (%s): starting...' % BUILD_VERSION
    print '*****************************'
    # Connect to AWS APIs
    client = boto3.client('iam')

    users = {}
    data = client.list_users()
    print data

    for user in data['Users']:
        userid = user['UserId']
        username = user['UserName']
        users[userid] = username

    users_report = []

    for user in users:
        user_keys = []

        print '---------------------'
        print 'user %s' % user
        username = users[user]
        print 'username %s' % username

        # check to see if the current user is a special service account
        if username == SERVICE_ACCOUNT_NAME:
            print 'detected special service account %s, skipping account...', username
            continue

        access_keys = client.list_access_keys(UserName=username)['AccessKeyMetadata']
        for access_key in access_keys:
            print access_key
            access_key_id = access_key['AccessKeyId']
            print 'AccessKeyId %s' % access_key_id

            existing_key_status = access_key['Status']
            print existing_key_status

            key_created_date = access_key['CreateDate']
            print 'key_created_date %s' % key_created_date

            age = key_age(key_created_date)
            print 'age %s' % age

            # we only need to examine the currently Active and about to expire keys
            if existing_key_status == "Inactive":
                key_state = 'key is already in INACTIVE state'
                key_info = {'accesskeyid': access_key_id, 'age': age, 'state': key_state, 'changed': False}
                user_keys.append(key_info)
                continue

            key_state = ''
            key_state_changed = False
            if age < FIRST_WARNING:
                key_state = 'key is still young'
            elif age == FIRST_WARNING:
                key_state = 'key is due to expire in 1 week (7  days)'
            elif age == LAST_WARNING:
                key_state = 'key is due to expire in 1 day (tomorrow)'
            elif age >= EXPIRY:
                key_state = 'key is now expired! Changing key to INACTIVE state'
                client.update_access_key(Username=username, AccessKeyId=access_key_id, Status=KEY_STATE_INACTIVE)
                send_deactivate_email(EMAIL_TO_ADMIN, username, age, access_key_id)
                key_state_changed = True

            print 'key_state %s' % key_state

            key_info = {'accesskeyid': access_key_id, 'age': age, 'state': key_state, 'changed': key_state_changed}
            user_keys.append(key_info)

        user_info = {'username': username, 'keys': user_keys}
        users_report.append(user_info)

    finished = str(datetime.now())
    deactivated_report = json.dumps({'reportdate': finished, 'users': users_report})
    print 'deactivated_report %s ' % deactivated_report

    if EMAIL_SEND_COMPLETION_REPORT:
        send_completion_email(EMAIL_TO_ADMIN, finished, deactivated_report)

    print '*****************************'
    print 'Completed (%s): %s' % (BUILD_VERSION, finished)
    print '*****************************'
    return True

#if __name__ == "__main__":
#    event = 1
#    context = 1
#    lambda_handler(event, context)
