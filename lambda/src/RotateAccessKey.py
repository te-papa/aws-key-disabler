import boto3
from datetime import datetime
import dateutil.tz
import json
import ast
import sys
import re
import logging
import os

# Setting logger configuration
logger = logging.getLogger('')
logger.setLevel(logging.INFO)

# Regex
VALID_EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Variables
BUILD_VERSION = '2.0.0'
AWS_REGION = 'us-east-1'
SERVICE_ACCOUNT_NAME = ''  # WIP - To add username to skip invalidation process
# WIP - To add email address to end final report (weekly)
EMAIL_TO_ADMIN = os.environ['EMAIL_TO_ADMIN']
# WIP - To add email address used by ses to send alerts to users about keys
EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_SEND_COMPLETION_REPORT = ast.literal_eval('False')
# WIP - To add group name to ignore users belonging to this group for
# disabling keys
GROUP_LIST = ''

# Length of mask over the IAM Access Key
MASK_ACCESS_KEY_LENGTH = ast.literal_eval('16')

KEY_YOUNG_MESSAGE = 'key is still young'

# First email warning
FIRST_WARNING_NUM_DAYS = 75

# Email SPAMMER PER HOUR
KEY_AGE_SPAMMER_IN_DAYS = 89

# Max AGE days of key after which it is considered to be DISABLED
KEY_MAX_AGE_IN_DAYS = 90
KEY_DISABLED_MESSAGE = 'key is now Disabled! Changing key to INACTIVE state'

# Max AGE days of key after which it is considered EXPIRED
KEY_EXPIRE_AGE_IN_DAYS = 100
KEY_EXPIRED_MESSAGE = 'key Expiration is overdue, key will be deleted now!'


# Character length of an IAM Access Key
ACCESS_KEY_LENGTH = 20
KEY_STATE_ACTIVE = "Active"
KEY_STATE_INACTIVE = "Inactive"


# check to see if the MASK_ACCESS_KEY_LENGTH has been misconfigured
if MASK_ACCESS_KEY_LENGTH > ACCESS_KEY_LENGTH:
    MASK_ACCESS_KEY_LENGTH = 16


def create_warning(days_left) -> str:
    return f'key is due to be disable in {90-int(days_left)} days'


def validate_email(email_address) -> bool:
    # pass the regular expression
    # and the string into the fullmatch() method
    if re.fullmatch(VALID_EMAIL_REGEX, email_address):
        return True

    else:
        return False


def tzutc():
    return dateutil.tz.tzutc()


def key_age(key_created_date) -> int:
    tz_info = key_created_date.tzinfo
    age = datetime.now(tz_info) - key_created_date
    # logger.info(f'Key Age: {age}')
    key_age_str = str(age)
    if 'days' not in key_age_str:
        return 0
    days = int(key_age_str.split(',')[0].split(' ')[0])
    return days


def send_notification_email(username, age, access_key_id, key_state) -> None:
    pass
    # client = boto3.client('ses', region_name=AWS_REGION)
    # data = f"The Access Key {access_key_id} belonging to User {username} is being alerted as it is {age} days old and {key_state}\n"
    # confluence_uri = "https://cloudhealthtech.atlassian.net/l/c/fmVzKSSV"
    # if validate_email(username):
    #     response = client.send_email(
    #         Source=EMAIL_FROM,
    #         Destination={
    #             'ToAddresses': [username]
    #         },
    #         Message={
    #             'Subject': {
    #                 'Data': f'Access key {access_key_id} is {age} days old.'
    #             },
    #             'Body': {
    #                 'Html': {
    #                     'Data': f"<!DOCTYPE html><html><body><p>{data}<br><br>Reference Link -<br>{confluence_uri}</p></body></html>"
    #                 }
    #             }
    #         })
    #     logger.info(
    #         f"send_notification_email response for {username}: {json.dumps(response, indent=4, default=str)}")
    #     return f"Email Sent! to {username}"
    # logger.info(f"Can't send email : {username} is a invalid email")


def send_completion_email(email_to, deactivated_report) -> None:
    pass
    # client = boto3.client('ses', region_name=AWS_REGION)
    # response = client.send_email(
    #     Source=EMAIL_FROM,
    #     Destination={
    #         'ToAddresses': [email_to]
    #     },
    #     Message={
    #         'Subject': {
    #             'Data': 'AWS IAM Access Key Rotation - Lambda Function'
    #         },
    #         'Body': {
    #             'Html': {
    #                 'Data': f"<!DOCTYPE html><html><body><h1>SECURITY IAM CREDENTIAL REPORT<h1><h2>AWS IAM Access Key Rotation Lambda Function Deactivation<br></h2>Report:\n\n\n{deactivated_report}</body></html>"
    #             }
    #         }
    #     })
    # logger.info(
    #     f"send_completion_email response: {json.dumps(response, indent=4, default=str)}")


def mask_access_key(access_key) -> str:
    return access_key[-(ACCESS_KEY_LENGTH - MASK_ACCESS_KEY_LENGTH):].rjust(len(access_key), "*")


def create_email_report(report_data) -> str:
    report_date_line = f"<tr><th>REPORTDATE</th><td colspan='2'>{report_data['reportdate']}</td></tr>\n"
    report = f"<tr><th colspan='3'>USERS</th></tr>\n"
    for usr in report_data["users"]:
        for key in usr["keys"]:
            report += f"<tr><th rowspan='5'>USERNAME = {usr['username']}</th></tr>\n"
            for data in key:
                report += f"<tr><th>{data.upper()}</th><td>{key[data]}</td></tr>\n"
    return f"<table border=1 style='width:100%'>{report_date_line}{report}</table>"


def lambda_handler(event, lambda_context):
    logger.info(f"Event: {event}")
    logger.info(f'RotateAccessKey ({BUILD_VERSION}): starting...')

    # Connect to AWS APIs
    client = boto3.client('iam')
    users = {}

    paginator = client.get_paginator("list_users")
    response_iterator = paginator.paginate()
    data = {}
    for response in response_iterator:
        data.update(response)
    # logger.info(json.dumps(data, indent=4, default=str))
    userindex = 0

    for user in data['Users']:
        userid = user['UserId']
        username = user['UserName']
        users[userid] = username

    # logger.info(json.dumps(users, indent=4, default=str))

    users_report1 = []
    users_report2 = []

    logger.info(
        f"Test if the user belongs to the exclusion group: {GROUP_LIST}")
    for user in users:
        userindex += 1
        user_keys = []
        username = users[user]
        # logger.info(f'\nuserindex: {userindex} \nuser: {user} \nusername: {username}')

        # Test if a user belongs to a specific list of groups. If they do,
        # don't invalidate the access key
        user_groups = client.list_groups_for_user(UserName=username)
        skip = False
        for groupName in user_groups['Groups']:
            if groupName['GroupName'] == GROUP_LIST:
                logger.warning(
                    f'Detected that {username} belongs to: {GROUP_LIST} \nuserindex: {userindex} \nuser: {user} \nusername: {username}')
                skip = True
                continue

        if skip:
            logger.warning("Don't invalidate Access Key")
            continue

        # check to see if the current user is a special service account
        if username == SERVICE_ACCOUNT_NAME:
            logger.warning(
                f'Detected special service account {username}, skipping account...')
            continue

        access_keys = client.list_access_keys(UserName=username)[
            'AccessKeyMetadata']
        for access_key in access_keys:
            access_key_id = access_key['AccessKeyId']
            masked_access_key_id = mask_access_key(access_key_id)
            existing_key_status = access_key['Status']
            key_created_date = access_key['CreateDate']
            age = key_age(key_created_date)
            logger.info(
                f'\nuserindex: {userindex} \nuser: {user} \nusername: {username} \nAccessKeyId: {masked_access_key_id} \nExistingKeyStatus: {existing_key_status} \nkey_created_date: {key_created_date} \nAge: {age}')
            # we only need to examine the currently Active and about to expire
            # keys
            if existing_key_status == "Inactive" and age < KEY_EXPIRE_AGE_IN_DAYS:
                key_state = 'key is already in an INACTIVE state'
                key_info = {
                    'accesskeyid': masked_access_key_id,
                    'age': age,
                    'state': key_state,
                    'changed': False}
                user_keys.append(key_info)
                continue

            key_state = ''
            key_state_changed = False
            if age < FIRST_WARNING_NUM_DAYS:
                key_state = KEY_YOUNG_MESSAGE
            elif age >= FIRST_WARNING_NUM_DAYS and age < KEY_AGE_SPAMMER_IN_DAYS:
                key_state = create_warning(age)
                if not event['check_for_outdated_keys']:
                    send_notification_email(
                        username, age, masked_access_key_id, key_state)
            elif age == KEY_AGE_SPAMMER_IN_DAYS:
                key_state = create_warning(age)
                send_notification_email(
                    username, age, masked_access_key_id, key_state)
            elif age >= KEY_MAX_AGE_IN_DAYS and age < KEY_EXPIRE_AGE_IN_DAYS:
                key_state = KEY_DISABLED_MESSAGE
                if event['check_for_outdated_keys']:
                    # client.update_access_key(
                    #     UserName=username,
                    #     AccessKeyId=access_key_id,
                    #     Status=KEY_STATE_INACTIVE)
                    send_notification_email(
                        username, age, masked_access_key_id, key_state)
                    key_state_changed = True
                    continue
                # client.update_access_key(
                #     UserName=username,
                #     AccessKeyId=access_key_id,
                #     Status=KEY_STATE_INACTIVE)
                send_notification_email(
                    username, age, masked_access_key_id, key_state)
                key_state_changed = True
            elif age >= KEY_EXPIRE_AGE_IN_DAYS:
                key_state = KEY_EXPIRED_MESSAGE
                # client.delete_access_key(UserName=username, AccessKeyId=access_key_id)
                send_notification_email(
                    username, age, masked_access_key_id, key_state)
                key_state_changed = True
            key_info = {
                'accesskeyid': masked_access_key_id,
                'age': age,
                'state': key_state,
                'changed': key_state_changed}
            user_keys.append(key_info)
        user_info_with_username = {
            'userid': userindex,
            'username': username,
            'keys': user_keys}
        user_info_without_username = {'userid': userindex, 'keys': user_keys}
        users_report1.append(user_info_with_username)
        users_report2.append(user_info_without_username)

    if userindex == len(user) and event['check_for_outdated_keys']:
        sys.exit()

    if len(users_report1) > 0 and len(users_report2) > 0:
        EMAIL_SEND_COMPLETION_REPORT = True
        finished = str(datetime.now())
        deactivated_report1 = {'reportdate': finished, 'users': users_report1}
        logger.info(
            f'\n\nDeactivated_Report1: {json.dumps(deactivated_report1, indent=4, default=str)}')

    if EMAIL_SEND_COMPLETION_REPORT and not event['check_for_outdated_keys']:
        deactivated_report2 = {'reportdate': finished, 'users': users_report1}

        send_completion_email(EMAIL_TO_ADMIN,
                              create_email_report(deactivated_report2))

    logger.info(f'Completed ({BUILD_VERSION, finished})')
    return deactivated_report1
