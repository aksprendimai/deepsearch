============
Introduction
============

.. _Haystack: http://haystacksearch.org

*deepsearch* is a Haystack_ extension used to
index deep and nested model relationships. Its key features are:

* ``~deepsearch.indexes.DeepSearchIndex`` class able to
  index deeply nested related objects and their fields.

* ``~deepsearch.models.FieldBoost`` model that stores weights of
  each index field for query-time field boosting.

* ``resume_index`` command able to reindex a slice of all
  objects or only a subset of index fields.

* *Celery* support for real-time indexing.
