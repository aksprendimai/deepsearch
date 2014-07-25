# -*- coding: utf-8 -*-

from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management import call_command

from haystack.management.commands import clear_index

from deepsearch.models import IndexRelation


class Command(BaseCommand):
    help = "Clears IndexRelations table (without prompt)."
    option_list = clear_index.Command.option_list + (
        make_option(
            '--clear-index', action='store_true', dest='clear_index', default=False,
            help='If provided, will invoke Haystack\'s clear_index command.'
        ),
    )

    def handle(self, **options):
        self.stdout.write('Removing all {0} IndexRelations\n'.format(
            IndexRelation.objects.count()))
        IndexRelation.objects.all().delete()
        self.stdout.write('All IndexRelations removed.\n')

        if options['clear_index']:
            self.stdout.write('Invoking clear_index\n')
            call_command('clear_index', **options)
