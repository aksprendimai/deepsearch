# -*- coding: utf-8 -*-

from haystack import connections
from haystack.forms import SearchForm
from haystack.inputs import AltParser

from models import FieldBoost


class DeepSearchForm(SearchForm):
    """
    Only compatible with Solr.
    """

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        if not self.cleaned_data.get('q'):
            return self.no_query_found()

        query = self.cleaned_data.get('q')
        query_fields = self.all_searchfields()

        parser = AltParser('dismax', query, qf=query_fields, mm=0)
        sqs = self.searchqueryset.filter(content=parser).highlight()

        if self.load_all:
            sqs = sqs.load_all()
        return sqs

    def get_unified_index(self):
        connection_alias = self.searchqueryset.query._using
        unified_index = connections[connection_alias].get_unified_index()
        return unified_index

    def all_searchfields(self):
        all_fields = self.get_unified_index().all_searchfields()

        fieldnames = []
        for field_name, field_instance in all_fields.iteritems():
            try:
                field_boost = FieldBoost.objects.get(index_fieldname=field_name)
                boost = field_boost.boost
            except FieldBoost.DoesNotExist:
                boost = 1.0

            query_field = field_name + '^' + str(boost)
            fieldnames.append(query_field)

        return ' '.join(fieldnames)
