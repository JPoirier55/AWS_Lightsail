import argparse
from subprocess import check_output
import json
import datetime
import email_builder


def build_date_str():
    """
    Creates date string that looks like
    02_14_19_H9_M30
    Used to tack on to end to create unique name

    :return: string
    """
    date = datetime.datetime.now()
    mo = date.month
    day = date.day
    year = date.year
    hour = date.hour
    min = date.minute
    date_str = '{0}_{1}_{2}_H{3}-M{4}'.format(mo, day, year, hour, min)
    return date_str


def build_date_str_s3():
    """
    Creates date string that looks like
    02_14_19
    Used to tack on to end of S3 backup

    :return: string
    """
    date = datetime.datetime.now()
    mo = date.month
    day = date.day
    year = str(date.year)[2:]
    date_str = '{0}_{1}_{2}'.format(mo, day, year)
    return date_str


def fetch_instances():
    """
    Gets all instances of lightsail containers
    :return: dict of lightsail containers
    """
    instances = json.loads(check_output("/home/bitnami/.local/bin/aws lightsail get-instances", shell=True))
    inst_names = []
    inst_dict = {}
    for instance in instances['instances']:
        inst_names.append(instance['name'])
        inst_dict[instance['name']] = []
    return inst_dict


def fetch_ec2_volumes():
    """
    Gets all ec2 volumes
    :return: json of all volumes
    """
    return json.loads(check_output("/home/bitnami/.local/bin/aws ec2 describe-volumes", shell=True))


def key_word(item):
    """
    Method to sort dates for S3 backup folders
    :param item: list of folder names
    :return: sorted dict
    """
    return datetime.datetime.strptime(item.split("p_")[1], "%m_%d_%y")


def fetch_snapshots():
    """
    Gets all current lightsail snapshots
    :return: json of snapshots
    """
    return json.loads(check_output("/home/bitnami/.local/bin/aws lightsail get-instance-snapshots", shell=True))


def build_inst_dict():
    """
    Builds list of snapshots for each instance
    and appends to the current inst dict
    :return: inst dict with snapshot list
    """
    inst_dict = fetch_instances()
    snapshots = fetch_snapshots()
    for snapshot in snapshots['instanceSnapshots']:
        inst_dict[snapshot['fromInstanceName']].append(snapshot)
    return inst_dict


def backup_lightsail(test):
    """
    Uses the instance dictionary to create a new snapshot
    and then delete the oldest one if there are greater than
    2 snapshots currently

    :param test: boolean if running test (--t in cli)
    :return: message that sends to email (list of created or deleted items)
    """
    inst_dict = build_inst_dict()
    date_str = build_date_str()
    message = []
    if test:
        message.append("THIS IS A TEST")
    for instance, snapshots in inst_dict.items():
        create_msg = 'Creating: ' + instance + "-" + date_str
        print(create_msg)
        message.append(create_msg)
        if not test:
            check_output(
                "/home/bitnami/.local/bin/aws lightsail create-instance-snapshot --instance-name " + instance + " --instance-snapshot-name "
                + instance + "-" + date_str, shell=True)
        if len(snapshots) > 2:
            sorted_snapshots = sorted(snapshots, key=lambda k: k['createdAt'])
            delete_msg = 'Deleting: ' + sorted_snapshots[0]['name']
            print(delete_msg)
            message.append(delete_msg)
            if not test:
                check_output("/home/bitnami/.local/bin/aws lightsail delete-instance-snapshot --instance-snapshot-name "
                                            + sorted_snapshots[0]['name'], shell=True)
    return message


def backup_ec2(test):
    """
    Backs up Ec2 volumes and deletes the oldest one
    if there are more than 2
    :param test: boolean if running test (--t in cli)
    :return: message that sends to email (list of created or deleted items)
    """
    date_str = build_date_str()
    volumes = fetch_ec2_volumes()
    message = []
    if test:
        message.append("THIS IS A TEST")
    for volume in volumes['Volumes']:
        snaps = json.loads(check_output(
            "/home/bitnami/.local/bin/aws ec2 describe-snapshots --filters Name=volume-id,Values={0}".format(volume['VolumeId']),
            shell=True))
        name_string = 'EC2_Volume_Snapshot_' + str(date_str)
        create_msg = 'Creating: ' + name_string
        print(create_msg)
        message.append(create_msg)
        if not test:
            check_output("/home/bitnami/.local/bin/aws ec2 create-snapshot --volume-id {0} --description {1}".format(volume['VolumeId'], name_string),
                shell=True)
        if len(snaps['Snapshots']) > 2:
            sorted_snapshots = sorted(snaps['Snapshots'], key=lambda k: k['StartTime'])
            delete_msg = 'Deleting: ' + sorted_snapshots[0]['Description']
            message.append(delete_msg)
            print(delete_msg)
            if not test:
                check_output("/home/bitnami/.local/bin/aws ec2 delete-snapshot --snapshot-id {0}".format(sorted_snapshots[0]['SnapshotId']),
                             shell=True)

    return message


def backup_webtools(test):
    return backup_s3(test, 'webtools')


def backup_wordpress(test):
    return backup_s3(test, 'wordpress')


def backup_s3(test, container):
    """
    Backs up S3 folders for both website and webtools
    This method parses the returns of what the AWS cli gives
    It doesnt return a good json to parse, so it must be pieced apart

    :param container: wordpress or webtools
    :param test: boolean if running test (--t in cli)
    :return: message that sends to email (list of created or deleted items)
    """
    if container == 'wordpress':
        s3_upload_location = 's3://axifuel-uploads/'
        s3_backup_location = 's3://axifuel-backups/Website_Backup/'
    else:
        s3_upload_location = 's3://axifuel-webtool/'
        s3_backup_location = 's3://axifuel-backups/Webtools_Backup/'
    json_obj = check_output("/home/bitnami/.local/bin/aws s3 ls " + s3_backup_location, shell=True)
    temp = str(json_obj).split('PRE ')
    backup_arr = []
    message = []
    if test:
        message.append("THIS IS A TEST")
    for folder in temp:
        name = folder.split("/")[0]
        if 'Backup' in name:
            backup_arr.append(name)
    sorted_backup_arr = sorted(backup_arr, key=key_word)
    if len(sorted_backup_arr) > 2:
        oldest = sorted_backup_arr[0]
        delete_msg = 'Deleting ' + oldest
        print(delete_msg)
        if not test:
            check_output("/home/bitnami/.local/bin/aws s3 rm --recursive {0}".format(s3_backup_location + oldest), shell=True)
        message.append(delete_msg)
    date_str = build_date_str_s3()
    create_msg = 'Copying from: ' + s3_upload_location + ' To: ' + s3_backup_location + "Backup_" + date_str
    print(create_msg)
    message.append(create_msg)
    if not test:
        check_output("/home/bitnami/.local/bin/aws s3 mkdir {0}".format(s3_backup_location + "Backup_" + date_str), shell=True)
        check_output("/home/bitnami/.local/bin/aws s3 cp --recursive {0} {1}".format(s3_upload_location,
                                                            s3_backup_location + "Backup_" + date_str), shell=True)
    return message


def run_backup_all(test, email, password):
    """
    Main method to run all backups

    :param email: email to be sent to (default is apikey for sendgrid)
    :param password: password read from pw file for email
    :return: none
    """
    ec2_message = backup_ec2(test)
    lightsail_message = backup_lightsail(test)
    s3_webtools_message = backup_s3(test, 'webtools')
    s3_wordpress_message = backup_s3(test, 'wordpress')
    email_message = ec2_message + lightsail_message + s3_webtools_message + s3_wordpress_message
    if not test:
        email_builder.sendEmail('AWS Backup Completed', ['jake.poirier@axi-international.com'],
                                email_message, email, password)
    else:
        email_builder.sendEmail('AWS Backup TEST', ['jake.poirier@axi-international.com'],
                                email_message, email, password)


def run_backup_name(instance):
    """
    backup single lightsail instance
    Deprecated
    :param instance:
    :return:
    """
    inst_dict = build_inst_dict()
    date_str = build_date_str()
    print('Creating: ' + instance + "-" + date_str)
    check_output("/home/bitnami/.local/bin/aws lightsail create-instance-snapshot --instance-name " +
                 instance + " --instance-snapshot-name " + instance +
                 "-" + date_str, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--b', '--backup', default=False, help='Backup current instances')
    parser.add_argument('--n', '--name', default='All', help='Backup one specific instance')
    parser.add_argument('--t', '--test', default='True', help='Test with only output')
    parser.add_argument('--e', '--email', default='', help='Email Login')

    args = parser.parse_args()
    pw_file = open('/home/bitnami/AWS_Lightsail/password', 'r')
    pw = pw_file.read()
    if args.b == 'True':
        if args.n == 'All':
            if args.t == 'True':
                print('********Running Test***********')
                print(datetime.datetime.now())
                run_backup_all(True, args.e, pw)
            else:
                run_backup_all(False, args.e, pw)
        else:
            run_backup_name(args.n)


