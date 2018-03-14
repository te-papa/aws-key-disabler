import boto3
from datetime import datetime
import dateutil.tz
import json
import ast

BUILD_VERSION = '@@buildversion'
AWS_REGION = '@@deploymentregion'
AWS_EMAIL_REGION = '@@emailregion'
SERVICE_ACCOUNT_NAME = '@@serviceaccount'
EMAIL_TO_ADMIN = '@@emailreportto'
EMAIL_FROM = '@@emailreportfrom'
EMAIL_SEND_COMPLETION_REPORT = ast.literal_eval('@@emailsendcompletionreport')
GROUP_LIST = "@@exclusiongroup"

# Length of mask over the IAM Access Key
MASK_ACCESS_KEY_LENGTH = ast.literal_eval('@@maskaccesskeylength')

# First email warning
FIRST_WARNING_NUM_DAYS = @@first_warning_num_days
FIRST_WARNING_MESSAGE = '@@first_warning_message'
# Last email warning
LAST_WARNING_NUM_DAYS = @@last_warning_num_days
LAST_WARNING_MESSAGE = '@@last_warning_message'

# Max AGE days of key after which it is considered EXPIRED (deactivated)
KEY_MAX_AGE_IN_DAYS = @@key_max_age_in_days
KEY_EXPIRED_MESSAGE = '@@key_expired_message'

KEY_YOUNG_MESSAGE = '@@key_young_message'

# ==========================================================

# Character length of an IAM Access Key
ACCESS_KEY_LENGTH = 20
KEY_STATE_ACTIVE = "Active"
KEY_STATE_INACTIVE = "Inactive"

# ==========================================================

#check to see if the MASK_ACCESS_KEY_LENGTH has been misconfigured
if MASK_ACCESS_KEY_LENGTH > ACCESS_KEY_LENGTH:
    MASK_ACCESS_KEY_LENGTH = 16

# ==========================================================
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
    client = boto3.client('ses', region_name=AWS_EMAIL_REGION)
    data = 'The Access Key [%s] belonging to User [%s] has been automatically ' \
           'deactivated due to it being %s days old' % (access_key_id, username, age)
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
                'Text': {
                    'Data': data
                }
            }
        })


def send_completion_email(email_to, finished, deactivated_report):
    client = boto3.client('ses', region_name=AWS_EMAIL_REGION)
    data = 'AWS IAM Access Key Rotation Lambda Function (cron job) finished successfully at %s \n \n ' \
           'Deactivation Report:\n%s' % (finished, json.dumps(deactivated_report, indent=4, sort_keys=True))
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
                'Text': {
                    'Data': data
                }
            }
        })


def mask_access_key(access_key):
    return access_key[-(ACCESS_KEY_LENGTH-MASK_ACCESS_KEY_LENGTH):].rjust(len(access_key), "*")


def lambda_handler(event, context):
    print '*****************************'
    print 'RotateAccessKey (%s): starting...' % BUILD_VERSION
    print '*****************************'
    # Connect to AWS APIs
    client = boto3.client('iam')

    users = {}
    data = client.list_users()
    print data

    userindex = 0

    for user in data['Users']:
        userid = user['UserId']
        username = user['UserName']
        users[userid] = username

    users_report1 = []
    users_report2 = []

    for user in users:
        userindex += 1
        user_keys = []

        print '---------------------'
        print 'userindex %s' % userindex
        print 'user %s' % user
        username = users[user]
        print 'username %s' % username

        # test is a user belongs to a specific list of groups. If they do, do not invalidate the access key
        print "Test if the user belongs to the exclusion group"
        user_groups = client.list_groups_for_user(UserName=username)
        skip = False
        for groupName in user_groups['Groups']:
            if groupName['GroupName'] == GROUP_LIST:
                print 'Detected that user belongs to ', GROUP_LIST
                skip = True
                continue

        if skip:
            print "Do invalidate Access Key"
            continue


        # check to see if the current user is a special service account
        if username == SERVICE_ACCOUNT_NAME:
            print 'detected special service account %s, skipping account...', username
            continue

        access_keys = client.list_access_keys(UserName=username)['AccessKeyMetadata']
        for access_key in access_keys:
            print access_key
            access_key_id = access_key['AccessKeyId']

            masked_access_key_id = mask_access_key(access_key_id)

            print 'AccessKeyId %s' % masked_access_key_id

            existing_key_status = access_key['Status']
            print existing_key_status

            key_created_date = access_key['CreateDate']
            print 'key_created_date %s' % key_created_date

            age = key_age(key_created_date)
            print 'age %s' % age

            # we only need to examine the currently Active and about to expire keys
            if existing_key_status == "Inactive":
                key_state = 'key is already in an INACTIVE state'
                key_info = {'accesskeyid': masked_access_key_id, 'age': age, 'state': key_state, 'changed': False}
                user_keys.append(key_info)
                continue

            key_state = ''
            key_state_changed = False
            if age < FIRST_WARNING_NUM_DAYS:
                key_state = KEY_YOUNG_MESSAGE
            elif age == FIRST_WARNING_NUM_DAYS:
                key_state = FIRST_WARNING_MESSAGE
            elif age == LAST_WARNING_NUM_DAYS:
                key_state = LAST_WARNING_MESSAGE
            elif age >= KEY_MAX_AGE_IN_DAYS:
                key_state = KEY_EXPIRED_MESSAGE
                client.update_access_key(UserName=username, AccessKeyId=access_key_id, Status=KEY_STATE_INACTIVE)
                send_deactivate_email(EMAIL_TO_ADMIN, username, age, masked_access_key_id)
                key_state_changed = True

            print 'key_state %s' % key_state

            key_info = {'accesskeyid': masked_access_key_id, 'age': age, 'state': key_state, 'changed': key_state_changed}
            user_keys.append(key_info)

        user_info_with_username = {'userid': userindex, 'username': username, 'keys': user_keys}
        user_info_without_username = {'userid': userindex, 'keys': user_keys}

        users_report1.append(user_info_with_username)
        users_report2.append(user_info_without_username)

    finished = str(datetime.now())
    deactivated_report1 = {'reportdate': finished, 'users': users_report1}
    print 'deactivated_report1 %s ' % deactivated_report1

    if EMAIL_SEND_COMPLETION_REPORT:
        deactivated_report2 = {'reportdate': finished, 'users': users_report2}
        send_completion_email(EMAIL_TO_ADMIN, finished, deactivated_report2)

    print '*****************************'
    print 'Completed (%s): %s' % (BUILD_VERSION, finished)
    print '*****************************'
    return deactivated_report1

#if __name__ == "__main__":
#    event = 1
#    context = 1
#    lambda_handler(event, context)
