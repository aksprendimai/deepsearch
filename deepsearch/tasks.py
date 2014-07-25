# -*- coding: utf-8 -*-

from haystack import connections, connection_router
from haystack.exceptions import NotHandled

from main.tasks import app

from models import IndexRelation


@app.task
def update_index(model, pk):
    instance = _get_instance(model, pk)
    _reindex_object(instance)
    _reindex_related(instance)


@app.task
def remove_index(model, pk):
    instance = _get_instance(model, pk)
    for index, using in indexes_for_object(instance):
        index.remove_object(instance, using=using)

    _reindex_related(instance)


def indexes_for_object(instance):
    using_backends = connection_router.for_write(instance=instance)
    for using in using_backends:
        try:
            model = type(instance)
            index = connections[using].get_unified_index().get_index(model)
            yield index, using
        except NotHandled:
            pass


def _get_instance(model, pk):
    """
    Tasks should not accept model instances as they may be out of date.
    """
    instance = model.objects.get(pk=pk)
    return _refresh_instance(instance)


def _refresh_instance(instance):
    """
    Invalidate cache for the instance and reload it.
    """
    type(instance).objects.invalidate(instance)
    return type(instance).objects.get(pk=instance.pk)


def _reindex_object(instance):
    for index, using in indexes_for_object(instance):
        index.update_object(instance, using=using)


def _reindex_related(instance):
    index_relations = IndexRelation.objects.as_related(instance)
    for index_relation in index_relations:
        indexable_object = index_relation.indexable_object
        indexable_object = _refresh_instance(indexable_object)
        _reindex_object(indexable_object)
