Real-time indexing
==================

.. note::
    Real time indexing requires *Celery*.

To avoid periodically rebuilding the index, *deepsearch* supports
real-time indexing by using *Haystack* signal
processors.  ``signals.DeepSearchSignalProcessor`` class is used to handle
index updates after an object is saved or deleted. By utilizing
:class:`~deepsearch.models.IndexRelation` model it is possible to update
indexed objects when a non-indexed object is modified.

To enable real-time indexing add the following line to ``settings.py``::

    HAYSTACK_SIGNAL_PROCESSOR = 'deepsearch.signals.DeepSearchSignalProcessor'

Tasks
-----

.. function:: deepsearch.tasks.update_index(model, pk)

    Invoked whenever an object is saved.

    If index exists, it updates the object and any other objects it is linked
    with as related in :class:`~deepsearch.models.IndexRelation` table.

.. function:: deepsearch.tasks.remove_index(model, pk)

    Invoked whenever an object is deleted.

    If index exists, removes the object from it and updates any other
    objects it was linked with as related in
    :class:`~deepsearch.models.IndexRelation` table.
