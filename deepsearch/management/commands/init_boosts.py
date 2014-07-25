# -*- coding: utf-8 -*-

from optparse import make_option

from django.core.management.base import BaseCommand

from haystack import connections

from deepsearch.models import FieldBoost


class Command(BaseCommand):
    help = 'Updates field boosts for all registered index fields.'
    option_list = BaseCommand.option_list + (
        make_option(
            '-n', '--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help='do everything without writing to DB',
        ),
        make_option(
            '-r', '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help='Reset all existing and new boost values to 1.0',
        ),
    )

    def handle(self, *args, **options):
        # load all existing boost values for later reference
        existing_boosts = dict((f.index_fieldname, f.boost) for f in FieldBoost.objects.all())

        if not options['dryrun']:
            FieldBoost.objects.all().delete()

        all_index_fields = connections['default'].get_unified_index().all_searchfields()

        for field in sorted(all_index_fields.keys()):
            params = {'index_fieldname': field}  # user unspecified

            if (not options['reset']) and (field in existing_boosts):
                params['boost'] = existing_boosts[field]

            if not options['dryrun']:
                FieldBoost.objects.create(**params)

            self.stdout.write('{0:100} ({1})\n'.format(
                params['index_fieldname'], params.get('boost', 'default')))
