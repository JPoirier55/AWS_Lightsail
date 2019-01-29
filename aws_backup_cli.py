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


def fetch_snapshots():
    return json.loads(check_output("aws lightsail get-instance-snapshots", shell=True))


def build_inst_dict():
    inst_dict = fetch_instances()
    snapshots = fetch_snapshots()
    for snapshot in snapshots['instanceSnapshots']:
        inst_dict[snapshot['fromInstanceName']].append(snapshot)
    return inst_dict


def run_backup_all(test):
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
            check_output("aws lightsail create-instance-snapshot --instance-name " + instance + " --instance-snapshot-name "
                         + instance + "-" + date_str, shell=True)
        if len(snapshots) > 2:
            sorted_snapshots = sorted(snapshots, key=lambda k: k['createdAt'])
            delete_msg = 'Deleting: ' + sorted_snapshots[0]['name']
            print(delete_msg)
            message.append(delete_msg)
            if not test:
                print(json.dumps(json.loads(check_output("aws lightsail delete-instance-snapshot --instance-snapshot-name "
                                                     + sorted_snapshots[0]['name'], shell=True))))
    if not test:
        email_builder.sendEmail('AWS Backup Completed', ['jake.poirier@axi-international.com'],
                                message)
    else:
        email_builder.sendEmail('AWS Backup TEST', ['jake.poirier@axi-international.com'],
                                message)

def run_backup_name(instance):
    inst_dict = build_inst_dict()
    date_str = build_date_str()
    print('Creating: ' + instance + "-" + date_str)
    check_output("aws lightsail create-instance-snapshot --instance-name " +
                 instance + " --instance-snapshot-name " + instance +
                 "-" + date_str, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--b', '--backup', default=False, help='Backup current instances')
    parser.add_argument('--n', '--name', default='All', help='Backup one specific instance')
    parser.add_argument('--t', '--test', default='True', help='Test with only output')

    args = parser.parse_args()

    if args.b == 'True':
        if args.n == 'All':
            if args.t == 'True':
                print('********Running Test***********')
                run_backup_all(True)
            else:
                run_backup_all(False)
        else:
            run_backup_name(args.n)


