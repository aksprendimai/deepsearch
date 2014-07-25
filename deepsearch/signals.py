# -*- coding: utf-8 -*-

import socket

from haystack.signals import RealtimeSignalProcessor

from deepsearch.tasks import update_index, remove_index, indexes_for_object

from models import IndexRelation


def should_reindex(instance):
    indexes = list(indexes_for_object(instance))
    relations = IndexRelation.objects.as_related(instance)
    return (len(indexes) > 0) or (relations.exists())


class DeepSearchSignalProcessor(RealtimeSignalProcessor):
    def handle_save(self, sender, instance, **kwargs):
        if not should_reindex(instance):
            return

        try:
            update_index.delay(type(instance), instance.pk)
        except socket.error:  # RabbitMQ down
            pass  # TODO maybe log this?

    def handle_delete(self, sender, instance, **kwargs):
        if not should_reindex(instance):
            return

        try:
            remove_index.delay(type(instance), instance.pk)
        except socket.error:  # RabbitMQ down
            pass  # TODO maybe log this?
