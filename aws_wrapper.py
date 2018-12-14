from subprocess import check_output
import json
import datetime

date = datetime.datetime.now()
mo = date.month
day = date.day
year = date.year
str = '{0}-{1}-{2}'.format(mo, day, year)
instances = json.loads(check_output("aws lightsail get-instances", shell=True))

inst_names = []
inst_dict = {}
for instance in instances['instances']:
    inst_names.append(instance['name'])
    inst_dict[instance['name']] = []

print(inst_names)
snapshots = json.loads(check_output("aws lightsail get-instance-snapshots", shell=True))

for snapshot in snapshots['instanceSnapshots']:
    inst_dict[snapshot['fromInstanceName']].append(snapshot)

for instance, snapshots in inst_dict.items():
    print(json.dumps(json.loads(
        check_output("aws lightsail create-instance-snapshot --instance-name " + instance + " --instance-snapshot-name " + instance + "-" + str,
                     shell=True))))
    if len(snapshots) > 1:
        sorted_snapshots = sorted(snapshots, key=lambda k: k['createdAt'])
        print(json.dumps(json.loads(check_output("aws lightsail delete-instance-snapshot --instance-snapshot-name " + sorted_snapshots[0]['name'], shell=True))))
