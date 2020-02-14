from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.timezone import make_aware

from mxlive.lims.models import Project, Beamline
from mxlive.schedule.models import Beamtime, BeamlineProject, BeamlineSupport, AccessType

import json
from datetime import datetime, timedelta


SHIFT_MAP = ["08", "16", "00"]
ACCESS_MAP = {
    'remote': "Remote",
    'mail_in': "Mail-In",
    'purchased': "Purchased Access",
    'maintenance': "Maintenance & Commissioning"
}

def get_project_by_name(name):
    return Project.objects.filter((Q(last_name=name['last_name']) & Q(first_name=name['first_name'])) | (
                Q(username__iexact=name['last_name']) | Q(username__iexact=name['first_name']))).first()


def get_project_by_account(account):
    try:
        return Project.objects.filter(username__iexact=account.split(',')[0].strip()).first()
    except:
        return None


def get_end(dt, shift):
    dt = datetime.strptime("{}T{}".format(dt, SHIFT_MAP[shift]), "%Y-%m-%dT%H") + timedelta(hours=8)
    if shift == 2: dt += timedelta(days=1)
    return make_aware(dt)


class Command(BaseCommand):
    help = 'Imports beamtime from the Django 2 website.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):
        bt_file = options['file']
        with open(bt_file) as json_bt:
            data = json.load(json_bt)
            projects = [p for p in data if p['model'] == 'scheduler.proposal']
            beamtime = [p for p in data if p['model'] == 'scheduler.visit']
            support = [p for p in data if p['model'] == 'scheduler.oncall']
            contact_map = { p['pk']: get_project_by_name(p['fields'])
                         for p in data if p['model'] == 'scheduler.supportperson' }
            beamline_map = {1: 2, 2: 1}
            project_map = {}

            for p in projects:
                info = {
                    "number": p['fields']['proposal_id'],
                    "expiration": p['fields']['expiration'][:10],
                    "title": p['fields']['description'],
                    "email": p['fields']['email'],
                    "project": get_project_by_account(p['fields']['account']) or get_project_by_name(p['fields'])
                }
                bp = BeamlineProject.objects.create(**info)
                project_map[p['pk']] = bp

            for p in beamtime:
                info = {
                    'project': p['fields']['proposal'] and project_map[p['fields']['proposal']] or None,
                    'beamline': Beamline.objects.get(pk=beamline_map[p['fields']['beamline']]),
                    'comments': p['fields']['description'],
                    'notify': p['fields']['notify'],
                    'sent': p['fields']['sent'],
                    'start': make_aware(datetime.strptime(
                        "{}T{}".format(p['fields']['start_date'], SHIFT_MAP[p['fields']['first_shift']]),
                        "%Y-%m-%dT%H")),
                    'end': get_end(p['fields']['end_date'], p['fields']['last_shift']),
                }
                bt = Beamtime.objects.create(**info)
                for k, v in ACCESS_MAP.items():
                    if p['fields'][k]: bt.access.add(AccessType.objects.get(name=v))

            for p in support:
                BeamlineSupport.objects.create(staff=contact_map[p['fields']['local_contact']],
                                               date=datetime.strptime(p['fields']['date'], "%Y-%m-%d"))
