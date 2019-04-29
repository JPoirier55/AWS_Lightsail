import argparse
from subprocess import check_output
import json
import datetime
import email_builder


def build_date_str():
    date = datetime.datetime.now()
    mo = date.month
    day = date.day
    year = date.year
    hour = date.hour
    min = date.minute
    date_str = '{0}_{1}_{2}_H{3}-M{4}'.format(mo, day, year, hour, min)
    return date_str


def fetch_instances():
    instances = json.loads(check_output("aws lightsail get-instances", shell=True))
    inst_names = []
    inst_dict = {}
    for instance in instances['instances']:
        inst_names.append(instance['name'])
        inst_dict[instance['name']] = []
    return inst_dict


def fetch_ec2_volumes():
    return json.loads(check_output("aws ec2 describe-volumes", shell=True))


def fetch_snapshots():
    return json.loads(check_output("aws lightsail get-instance-snapshots", shell=True))


def build_inst_dict():
    inst_dict = fetch_instances()
    snapshots = fetch_snapshots()
    for snapshot in snapshots['instanceSnapshots']:
        inst_dict[snapshot['fromInstanceName']].append(snapshot)
    return inst_dict


def backup_lightsail(test):
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
                "aws lightsail create-instance-snapshot --instance-name " + instance + " --instance-snapshot-name "
                + instance + "-" + date_str, shell=True)
        if len(snapshots) > 2:
            sorted_snapshots = sorted(snapshots, key=lambda k: k['createdAt'])
            delete_msg = 'Deleting: ' + sorted_snapshots[0]['name']
            print(delete_msg)
            message.append(delete_msg)
            if not test:
                print(json.dumps(
                    json.loads(check_output("aws lightsail delete-instance-snapshot --instance-snapshot-name "
                                            + sorted_snapshots[0]['name'], shell=True))))
    return message


def backup_ec2(test):
    date_str = build_date_str()
    volumes = fetch_ec2_volumes()
    message = []
    if test:
        message.append("THIS IS A TEST")
    for volume in volumes['Volumes']:
        snaps = json.loads(check_output(
            "aws ec2 describe-snapshots --filters Name=volume-id,Values={0}".format(volume['VolumeId']),
            shell=True))
        name_string = 'EC2_Volume_Snapshot_' + str(date_str)
        create_msg = 'Creating: ' + name_string + "-" + date_str
        print(create_msg)
        message.append(create_msg)
        if not test:
            json.loads(check_output(
                "aws ec2 create-snapshot --volume-id {0} --description {1}".format(volume['VolumeId'], name_string),
                shell=True))
        if len(snaps['Snapshots']) > 2:
            sorted_snapshots = sorted(snaps['Snapshots'], key=lambda k: k['StartTime'])
            print(sorted_snapshots[0])
            delete_msg = 'Deleting: ' + sorted_snapshots[0]['Description']
            message.append(delete_msg)
            print(delete_msg)
            if not test:
                json.loads(
                    check_output("aws ec2 delete-snapshot --snapshot-id {0}".format(sorted_snapshots[0]['SnapshotId']),
                                 shell=True))

    return message


def run_backup_all(test):
    ec2_message = backup_ec2(test)
    lightsail_message = backup_lightsail(test)
    email_message = ec2_message + lightsail_message
    if not test:
        email_builder.sendEmail('AWS Backup Completed', ['jake.poirier@axi-international.com'],
                                email_message)
    else:
        email_builder.sendEmail('AWS Backup TEST', ['jake.poirier@axi-international.com'],
                                email_message)


def run_backup_name(instance):
    inst_dict = build_inst_dict()
    date_str = build_date_str()
    print('Creating: ' + instance + "-" + date_str)
    check_output("aws lightsail create-instance-snapshot --instance-name " +
                 instance + " --instance-snapshot-name " + instance +
                 "-" + date_str, shell=True)


def key_word(item):
    return datetime.datetime.strptime(item.split("p_")[1], "%m_%d_%y")


def backup_s3():
    s3_upload_location = 's3://axifuel-uploads/'
    s3_backup_location = 's3://axifuel-backups/Website_Backup/'
    json_obj = check_output("aws s3 ls " + s3_backup_location)
    temp = str(json_obj).split('PRE ')
    backup_arr = []
    for folder in temp:
        name = folder.split("/")[0]
        if 'Backup' in name:
            print(name)
            backup_arr.append(name)
    print(backup_arr)
    sorted_backup_arr = sorted(backup_arr, key=key_word)
    print(sorted_backup_arr)
    oldest = sorted_backup_arr[0]
    print('Deleting ' + oldest)
    # check_output("aws s3 rm --recursive {0}".format(s3_backup_location + oldest), shell=True)
    date_str = build_date_str()

    print('Copying from: ' + s3_upload_location)
    print('To: ' + s3_backup_location + "Backup_" + date_str)
    # check_output("aws s3 mkdir {0}".format(s3_backup_location + "Backup_" + date_str), shell=True)
    check_output("aws s3 cp --recursive {0} {1}".format(s3_upload_location,
                                                        s3_backup_location + "Backup_" + date_str), shell=True)

if __name__ == '__main__':
    backup_s3()
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--b', '--backup', default=False, help='Backup current instances')
    # parser.add_argument('--n', '--name', default='All', help='Backup one specific instance')
    # parser.add_argument('--t', '--test', default='True', help='Test with only output')
    #
    # args = parser.parse_args()
    #
    # if args.b == 'True':
    #     if args.n == 'All':
    #         if args.t == 'True':
    #             print('********Running Test***********')
    #             run_backup_all(True)
    #         else:
    #             run_backup_all(False)
    #     else:
    #         run_backup_name(args.n)


