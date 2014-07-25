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

For a quick start head to :doc:`example` section.


Reference
---------

.. toctree::
   :maxdepth: 2

   example
   indexes
   models
   commands
   signals

.. _installation:

Installation
------------

Requirements:

* Python >= 2.6
* Django >= 1.4
* django-haystack >= 2.1.0
* South.>= 0.8.1
* celery>=3.1 `(optional)`

Recommended:

* `haystackbrowser <https://github.com/kezabelle/django-haystackbrowser>`_
  `(to inspect indexed data)`

Setup:

1. Include ``'deepsearch'`` in your ``INSTALLED_APPS``.
2. Configure ``HAYSTACK_CONNECTIONS``.
3. To enable real-time indexing add the following line to ``settings.py``:

   .. code-block:: python

       HAYSTACK_SIGNAL_PROCESSOR = 'deepsearch.signals.DeepSearchSignalProcessor'

   See also: :doc:`signals`.

4. Create ``search_indexes.py`` in your app directory.
   See also: :doc:`example`.

5. ``python manage.py init_boosts`` to update index field weight values. You
   should run this whenever you modify index schema. See also: :doc:`commands`.

6. ``python manage.py rebuild_index`` will update index and
   :class:`~deepsearch.models.IndexRelation` table.
