Introduction
============

*deepsearch* is a `Haystack <http://haystacksearch.org>`_ extension used to
index deep and nested model relationships. Its key features are:

* :class:`~deepsearch.indexes.DeepSearchIndex` class able to
  index deeply nested related objects and their fields.

* :class:`~deepsearch.models.FieldBoost` model that stores weights of
  each index field for query-time field boosting.

* :ref:`resume_index <resume-index>` command able to reindex a slice of all
  objects or only a subset of index fields.

* *Celery* support for real-time indexing.
