.. _Haystack: http://haystacksearch.org
.. _haystackbrowser: https://github.com/kezabelle/django-haystackbrowser

*deepsearch* is a Haystack_ extension used to
index deep and nested model relationships. Its key features are:

* ``deepsearch.indexes.DeepSearchIndex`` class able to
  index deeply nested related objects and their fields.

* ``deepsearch.models.FieldBoost`` model that stores weights of
  each index field for query-time field boosting.

* ``resume_index`` command able to reindex a slice of all
  objects or only a subset of index fields.

* *Celery* support for real-time indexing.

------------
Installation
------------

Requirements:

* Python >= 2.6
* Django >= 1.4
* django-haystack >= 2.1.0
* South.>= 0.8.1
* celery>=3.1 `(optional)`

Recommended:

* haystackbrowser_ *(to inspect indexed data)*

Setup:

1. Include ``'deepsearch'`` in your ``INSTALLED_APPS``.
2. Configure ``HAYSTACK_CONNECTIONS``.
3. To enable real-time indexing add the following line to ``settings.py``:

   .. code-block:: python

       HAYSTACK_SIGNAL_PROCESSOR = 'deepsearch.signals.DeepSearchSignalProcessor'

4. Create ``search_indexes.py`` in your app directory.

5. ``python manage.py init_boosts`` to update index field weight values. You
   should run this whenever you modify index schema.

6. ``python manage.py rebuild_index`` will update index and
   ``deepsearch.models.IndexRelation`` table.
