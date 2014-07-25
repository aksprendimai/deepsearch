Models
======

.. autoclass:: deepsearch.models.FieldBoost()
    :members:

.. autoclass:: deepsearch.models.IndexRelation()
    :members:

    ``IndexRelation`` objects are updated during indexing. When
    ``full_prepare(obj)`` is invoked on index, it deletes all ``IndexRelation``
    objects where ``obj`` is stored as ``indexable_object``. ``IndexRelation``
    objects are then created on each ``prepare(obj)`` call of ``AccessorField``
    instance.

    .. note::
        This table can grow quite large in your database.
