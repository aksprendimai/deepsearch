# -*- coding: utf-8 -*-

from optparse import make_option

from django import db
from django.utils.encoding import force_text
from django.utils.encoding import smart_bytes

from haystack import connections as haystack_connections
from haystack.exceptions import NotHandled
from haystack.management.commands import update_index
from haystack.management.commands.update_index import do_remove, do_update, worker


class Command(update_index.Command):
    help = "Reindex a slice of the queryset (parameters --offset and --limit)."
    base_options = (
        make_option(
            '--offset', action='store', dest='offset',
            default=0, type='int',
            help='Offset of the queryset slice.'),
        make_option(
            '--limit', action='store', dest='limit',
            default=None, type='int',
            help='Limit of the queryset slice.'),
        make_option(
            '--fields', action='store', dest='fields',
            default=None, type='string',
            help='A comma separated list of prefixes or full names of index fields to be indexed. Index all fields if not specified.'),
    )
    option_list = update_index.Command.option_list + base_options

    def handle(self, *items, **options):
        self.offset = options.get('offset')
        self.limit = options.get('limit', None)

        self.fields_to_index = options.get('fields', None)
        if self.fields_to_index is not None:
            self.fields_to_index = self.fields_to_index.split(',')

        super(Command, self).handle(*items, **options)

    def update_backend(self, label, using):
        # shamelessly copy pasted from haystack.management.commands.update_index.Command

        backend = haystack_connections[using].get_backend()

        if self.workers > 0:
            import multiprocessing

        for model in self.get_models(label):
            try:
                index = self.get_index(using, model)
            except NotHandled:
                if self.verbosity >= 2:
                    print("Skipping '%s' - no index." % model)
                continue

            if self.workers > 0:
                # workers resetting connections leads to references to models / connections getting
                # stale and having their connection disconnected from under them. Resetting before
                # the loop continues and it accesses the ORM makes it better.
                db.close_connection()

            qs = self.build_queryset(index, using)

            total = qs.count()

            if self.verbosity >= 1:
                print(u"Indexing %d %s" % (total, force_text(model._meta.verbose_name_plural)))

            pks_seen = set([smart_bytes(pk) for pk in qs.values_list('pk', flat=True)])
            batch_size = self.batchsize or backend.batch_size

            if self.workers > 0:
                ghetto_queue = []

            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)

                if self.workers == 0:
                    do_update(backend, index, qs, start, end, total, self.verbosity)
                else:
                    ghetto_queue.append(('do_update', model, start, end, total, using, self.start_date, self.end_date, self.verbosity))

            if self.workers > 0:
                pool = multiprocessing.Pool(self.workers)
                pool.map(worker, ghetto_queue)
                pool.terminate()

            if self.remove:
                if self.start_date or self.end_date or total <= 0:
                    # They're using a reduced set, which may not incorporate
                    # all pks. Rebuild the list with everything.
                    qs = index.index_queryset().values_list('pk', flat=True)
                    pks_seen = set([smart_bytes(pk) for pk in qs])
                    total = len(pks_seen)

                if self.workers > 0:
                    ghetto_queue = []

                for start in range(0, total, batch_size):
                    upper_bound = start + batch_size

                    if self.workers == 0:
                        do_remove(backend, index, model, pks_seen, start, upper_bound)
                    else:
                        ghetto_queue.append(('do_remove', model, pks_seen, start, upper_bound, using, self.verbosity))

                if self.workers > 0:
                    pool = multiprocessing.Pool(self.workers)
                    pool.map(worker, ghetto_queue)
                    pool.terminate()

    def get_index(self, using, model):
        # determine what index to use
        unified_index = haystack_connections[using].get_unified_index()
        index = unified_index.get_index(model)

        if self.fields_to_index is None:
            return index  # index all fields, use the index as is

        # we do not want to modify the global index instance
        # so let's create a new local instance of the same class with overwrite parameter disabled
        index = type(index)(overwrite_stored_data=False)

        index.retain_fields(self.fields_to_index)

        if not index.fields:
            print(u'{0} - No applicable fields.'.format(type(index).__name__))
            raise NotHandled  # nothing to index

        print(u'{0} - Indexing following fields:'.format(type(index).__name__))
        for field_name in index.fields.keys():
            print(u'  {0}'.format(field_name))

        return index

    def build_queryset(self, index, using):
        qs = index.build_queryset(
            using=using, start_date=self.start_date, end_date=self.end_date)

        if self.limit is not None:
            stop = self.offset + self.limit
            return qs[self.offset:stop]
        elif self.offset > 0:
            return qs[self.offset:]

        return qs
