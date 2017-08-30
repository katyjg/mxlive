import json

def merge_accounts(auth, proj):
    """
    Merges user and project data from past MxLIVE installations so the Project model can inherit from the AbstractUser class.
    :param auth: filename pointing to a json file generated by ./manage.py dumpdata auth.user
    :param proj: filename pointing to a json file generated by ./manage.py dumpdata lims.project
    :return: file named merged-accounts.json ready to be installed via ./manage.py loaddata
    """
    fa = open(auth)
    fp = open(proj)
    dauth = json.load(fa)
    dproj = json.load(fp)
    fa.close()
    fp.close()

    auth = {}
    for user in dauth:
        auth[user['fields']['username']] = user['fields']

    merged = []
    for project in dproj:
        project['fields'].update(auth[project['fields']['name']])
        del(project['fields']['user'])
        merged.append(project)

    fm = open('merged-accounts.json','w')
    fm.write(json.dumps(merged, indent=2))
    fm.close()


def cleanup_reports(reports):
    f = open(reports)
    data = json.load(f)
    f.close()

    for d in data:
        d['fields'].pop("strategy")
        d['fields']['sample'] = d['fields'].pop('crystal')
        d['fields']['group'] = d['fields'].pop('experiment')

    f = open("{}-cleaned.json".format(reports.split('.json')[0]), 'w')
    f.write(json.dumps(data, indent=2))
    f.close()


def cleanup(mxlive):
    """
    :param mxlive: filename pointing to a json file generated by ./manage.py dumpdata
    :return: file named mxlive-clean.json ready to be installed via ./manage.py loaddata
    """
    fm = open(mxlive)
    data = json.load(fm)
    fm.close()

    remove_models = ['lims.cocktail','lims.crystalform','lims.project','lims.spacegroup','lims.strategy']
    data = [d for d in data if d['model'] not in remove_models]

    models = ['lims.carrier','lims.beamline','lims.data','lims.dewar','lims.container',
              'lims.shipment','lims.crystal','lims.experiment','lims.componenet','lims.result','lims.scanresult']

    entries = {m: {d['pk']: d for d in data if d['model'] == m} for m in models}

    print "Cleaning up {} dewars".format(len(entries['lims.dewar']))
    # Transfer dewar__storage_location to shipment__storage_location
    for pk, shipment in entries['lims.shipment'].items():
        dewar_locations = [v['fields']['storage_location'] for k, v in entries['lims.dewar'].items() if v['fields']['shipment'] == pk and v['fields']['storage_location']]
        entries['lims.shipment'][pk]['fields']['storage_location'] = ';'.join(dewar_locations)

    print "Cleaning up {} containers".format(len(entries['lims.container']))
    # Transfer container__dewar__shipment to container__shipment
    kind_map = {1: 1, 0: 2, 2: 3, 3: 4}
    for pk, container in entries['lims.container'].items():
        if container['fields'].get('dewar'):
            entries['lims.container'][pk]['fields']['shipment'] = entries['lims.dewar'][container['fields']['dewar']]['fields']['shipment']
        entries['lims.container'][pk]['fields'].pop('dewar')
        entries['lims.container'][pk]['fields'].pop('staff_priority')
        # Transfer container__kind to instance of ContainerType
        entries['lims.container'][pk]['fields']['kind'] = kind_map[container['fields']['kind']]

    print "Cleaning up {} experiments".format(len(entries['lims.experiment']))
    for pk, group in entries['lims.experiment'].items():
        entries['lims.experiment'][pk]['model'] = 'lims.group'
        for f in ['i_sigma','multiplicity','r_meas','resolution','total_angle','delta_angle','staff_priority']:
            entries['lims.experiment'][pk]['fields'].pop(f)
        samples = [e for e in entries['lims.crystal'].values() if e['fields']['experiment'] == pk]
        shipments = [entries['lims.container'][c]['fields'].get('shipment') for c in [s['fields']['container'] for s in samples if s['fields']['container']] if entries['lims.container'][c]['fields'].get('shipment')]
        if shipments:
            shipment = max(set(shipments), key=shipments.count)
            entries['lims.experiment'][pk]['fields']['shipment'] = shipment
        entries['lims.experiment'][pk]['fields']['sample_count'] = len(samples)

    print "Cleaning up {} crystals".format(len(entries['lims.crystal']))
    for pk, sample in entries['lims.crystal'].items():
        entries['lims.crystal'][pk]['model'] = 'lims.sample'
        entries['lims.crystal'][pk]['fields'].pop('crystal_form')
        entries['lims.crystal'][pk]['fields'].pop('cocktail')
        entries['lims.crystal'][pk]['fields'].pop('staff_priority')
        entries['lims.crystal'][pk]['fields']['group'] = entries['lims.crystal'][pk]['fields'].pop('experiment')

    print "Cleaning up {} results".format(len(entries['lims.result']))
    for pk, result in entries['lims.result'].items():
        entries['lims.result'][pk]['fields'].pop('strategy')
        entries['lims.result'][pk]['fields']['sample'] = entries['lims.result'][pk]['fields'].pop('crystal')
        entries['lims.result'][pk]['fields']['group'] = entries['lims.result'][pk]['fields'].pop('experiment')

    print "Cleaning up {} data".format(len(entries['lims.data']))
    for pk, result in entries['lims.data'].items():
        entries['lims.data'][pk]['fields']['sample'] = entries['lims.data'][pk]['fields'].pop('crystal')
        entries['lims.data'][pk]['fields']['group'] = entries['lims.data'][pk]['fields'].pop('experiment')

    print "Cleaning up {} scans".format(len(entries['lims.scanresult']))
    for pk, result in entries['lims.scanresult'].items():
        entries['lims.scanresult'][pk]['fields'].pop('strategy')
        entries['lims.scanresult'][pk]['fields']['sample'] = entries['lims.scanresult'][pk]['fields'].pop('crystal')
        entries['lims.scanresult'][pk]['fields']['group'] = entries['lims.scanresult'][pk]['fields'].pop('experiment')

    new_data = []
    for m in models:
        new_data.extend(entries[m].values())

    filename = open('mxlive-cleaned.json','w')
    filename.write(json.dumps(new_data, indent=2))
    filename.close()


def result_to_report(result):

for r in Result.objects.filter(kind=0):

    screen_details = [{
        'title': 'Predicted Quality and Suggested Strategy',
        'description': """[1] - Data Quality Score for comparing similar data sets. Typically, values >
                0.8 are excellent, > 0.6 are good, > 0.5 are acceptable, > 0.4
                marginal, and &lt; 0.4 are Barely usable
            [2] - This space group was automatically assigned using POINTLESS (see P.R.Evans,
                Acta Cryst. D62, 72-82, 2005). This procedure is unreliable for incomplete datasets
                such as those used for screening. Please Inspect the detailed results below.
            [3] - Data collection strategy and predicted quality was calculated using BEST. See
            A.N. Popov and G.P. Bourenkov Acta Cryst. (2003). D59, 1145-1153, G.P. Bourenkov and A.N. Popov Acta Cryst. (2006). D62, 58-64.
            [4] - {}.
            """.format(r.details['strategy']['resolution_reasoning']),
        'data': [
            {
                'title': 'Observed Parameters',
                'kind': 'table',
                'data': [['Score[1]', r.score],
                         ['Wavelength (A)', r.wavelength],
                         ['Space Group[2]', r.space_group.name],
                         ['Unit Cell (A)', "{} {} {} {} {} {}".format(r.cell_a,r.cell_b, r.cell_c,r.cell_alpha, r.cell_beta,r.cell_gamma)],
                         ['Mosaicity', r.mosaicity],
                         ['Spot deviation', r.sigma_spot],
                         ['Spindle deviation', r.sigma_angle],
                         ['Ice Rings', r.ice_rings]
                ],
                'header': 'column',
                'description': ''
            },
            {
                'title': 'Expected Quality[3]',
                'kind': 'table',
                'data': [['Resolution (A)[4]', r.details.get('strategy',{}).get('resolution')],
                         ['Multiplicity', r.details.get('strategy',{}).get('multiplicity')],
                         ['Completeness', r.details.get('strategy',{}).get('completeness')],
                         ['I/Sigma (I)', r.details.get('strategy',{}).get('i_sigma')],
                         ['R-factor', r.details.get('strategy',{}).get('r_factor')],
                         ['Fraction overloaded', r.details.get('strategy',{}).get('frac_overload')],
                         ],
                'header': 'column',
                'description': ''
            },
            {
                'title': "Kappa and Phi angles for re-orienting the crystal",
                'kind': 'table',
                'data': [['Kappa[*]', 'Phi', 'Vectors (v1,v2)[*]']].extend(r.details.get('crystal_alignment',{}).get('solutions',['','',''])),
                'header': 'row',
                'description': """[*] - Alignment is calculated for the goniometer 'CLS MiniKappa'. The alignment method is v1 parallel to omega, v2 perpendicular to the omega-beam plane.""",
            },
            {
                'title': "Compatible bravais lattice types",
                'kind': 'table',
                'data': [['No.', 'Lattice type', 'Cell Parameters', 'Quality', 'Cell Volume']] + [
                    [id, r.details['compatible_lattices']['type'][i],
                     r.details['compatible_lattices']['unit_cell'][i], r.details['compatible_lattices']['quality'][i],
                     r.details['compatible_lattices']['volume'][i]]
                    for i, id in enumerate(r.details['compatible_lattices']['id'])
                    ],
                'header': 'row',
            },
            {
                'title': "Automatic Space-Group Selection",
                'kind': 'table',
                'data': [['Selected','Candidates','Space Group No.','Probability']] + [
                    [prob == max(r.details['spacegroup_selection']['probability']) and '*' or '',
                     r.details['spacegroup_selection']['name'][i],
                     r.details['spacegroup_selection']['space_group'][i],
                     prob,
                    ]
                for i, prob in enumerate(r.details['spacegroup_selection']['probability'])],
                'header': 'row',
                'description': """The above table contains results from POINTLESS (see Evans, Acta Cryst. D62, 72-82, 2005). Indistinguishable space groups will have similar probabilities. If two or more of the top candidates have the same probability, the one with the fewest symmetry assumptions is chosen. This usually corresponds to the point group,  trying out higher symmetry space groups within the top tier does not require re-indexing the data as they are already in the same setting. For more detailed results, please inspect the output file 'pointless.log'."""
            }
        ]
    },
    {
        'title': "Predicted statistics for suggested strategy by resolution",
        'data': [
            {
                'kind': 'lineplot',
                'data':
                    {
                        'x': ['']+ r.details['predicted_quality']['shell'],
                        'y1': [['Completeness (%)']+ r.details['predicted_quality']['completeness']],
                        'y2': [['R-factor (%)']+ r.details['predicted_quality']['r_factor']]
                    }
            },
            {
                'kind': 'lineplot',
                'data':
                    {
                        'x': ['Resolution Shell']+ r.details['predicted_quality']['shell'],
                        'y1': [['I/Sigma(I)']+ r.details['predicted_quality']['i_sigma']],
                        'y2': [['Multiplicity']+ r.details['predicted_quality']['multiplicity']]
                    },
                'description': "The above plot was calculated by BEST. See A.N. Popov and G.P. Bourenkov Acta Cryst. (2003). D59, 1145-1153, G.P. Bourenkov and A.N. Popov Acta Cryst. (2006). D62, 58-64"
            },
            {
                'kind': 'table',
                'data': [['Shell','Completeness','R-factor','I/Sigma(I)','Multiplicity','Overload Fraction']] + [
                    [shell, r.details['predicted_quality']['completeness'][i],r.details['predicted_quality']['r_factor'][i],r.details['predicted_quality']['i_sigma'][i],r.details['predicted_quality']['multiplicity'][i],r.details['predicted_quality']['frac_overload'][i]]
                    for i, shell in enumerate(r.details['predicted_quality']['shell'])
                 ],
                'header': 'row',
                'description': """I/Sigma - Mean intensity/Sigma of a reflection in shell
                                  R-factor - &Sigma;|I(h,i)-I(h)| / &Sigma;[I(h,i)]"""
            }
        ],
    },
    {
        'title': "Maximum Oscillation width to avoid overlapped spots at different resolutions",
        'data': [
            {
                'kind': 'lineplot',
                'data': {
                    'x': ['Oscillation Angle (deg)']+ r.details['overlap_analysis']['angle'],
                    'y1': [[k]+ v for k, v in r.details['overlap_analysis'].items() if k != 'angle'],
                    'y1-label': 'Maximum Delta (deg)'
                },
                'description': "The above plot was calculated by BEST. See A.N. Popov and G.P. Bourenkov Acta Cryst. (2003). D59, 1145-1153, G.P. Bourenkov and A.N. Popov Acta Cryst. (2006). D62, 58-64 ",
            },
        ]
    },
    {
        'title': "Minimal oscillation ranges for different percentages of data completeness",
        'data': [
            {
                'kind': 'lineplot',
                'data': {
                    'x': ['Starting Angle (deg)']+ r.details['wedge_analysis']['start_angle'],
                    'y1': [[k]+ v for k, v in r.details['wedge_analysis'].items() if k != 'start_angle'],
                    'y1-label': 'Total Oscillation Angle (deg)'
                },
                'description': "The above plot was calculated by BEST. See A.N. Popov and G.P. Bourenkov Acta Cryst. (2003). D59, 1145-1153, G.P. Bourenkov and A.N. Popov Acta Cryst. (2006). D62, 58-64 ",
            },
        ]
    },
    {
        'title': "Analysis of exposure time required versus resolution attained",
        'data': [
            {
                'kind': 'lineplot',
                'data': {
                    'x': ['Exposure Time (s)']+ r.details['exposure_analysis']['exposure_time'],
                    'y1': [['Resolution']+ r.details['exposure_analysis']['resolution']]
                },
                'annotations': [],
                'description': "The above plot was calculated by BEST. See A.N. Popov and G.P. Bourenkov Acta Cryst. (2003). D59, 1145-1153, G.P. Bourenkov and A.N. Popov Acta Cryst. (2006). D62, 58-64 ",
            },
        ]
    }]
    print screen_details, r.pk
    r.analysisreport_set.update(details=screen_details)

