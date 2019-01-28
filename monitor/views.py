from django.shortcuts import render
from aws_backup_cli import *
# Create your views here.


def monitor(request):
    out_dict = {}
    for instance, snaps in build_inst_dict().items():
        out_dict[instance] = []
        for snapshot in snaps:
            info_dict = {'name': snapshot['name'],
                         'created': datetime.datetime.fromtimestamp(int(snapshot['createdAt'])).strftime('%Y-%m-%d %H:%M:%S'),
                         'size': snapshot['sizeInGb'],
                         'blueprint': snapshot['fromBlueprintId']}
            out_dict[instance].append(info_dict)
            print(out_dict)

    return render(request, 'monitor.html', {'instances': out_dict})
