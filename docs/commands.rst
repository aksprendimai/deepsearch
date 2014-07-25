Management Commands
===================

``init_boosts``
---------------

.. autoclass:: deepsearch.management.commands.init_boosts.Command()

Creates :class:`~deepsearch.models.FieldBoost` objects for all
registered index fields. If :class:`~deepsearch.models.FieldBoost`
exists, its original weight value remains unchanged. You should run this
whenever you modify index schema.

**Options**

``-r, --reset``
    Reset all existing and new boost values to 1.0

``-n, --dryrun``
    Do everything without saving anything to database.

**Usage**

``python manage.py init_boosts``

``python manage.py init_boosts --dryrun``

``python manage.py init_boosts --reset``

.. _resume-index:

``resume_index``
----------------

.. autoclass:: deepsearch.management.commands.resume_index.Command()
    :show-inheritance:

Extends the ``update_index`` command of *Haystack*, but additionally provides
a few extra options to slice the indexed queryset.

**Options**

``--offset=N``
    Skip first N objects in the queryset.

``--limit=N``
    Index up to N objects.

``--fields=COMMA,SEPARATED,STRINGS``
    Update only those index fields which start with (or are equal to) any of
    the provided strings. This helps shorten reindexing times when you want to
    update the index with only few new index fields. Note that when indexing
    an object, its stored data is fetched from the index (this is called `a
    document`), the subset of fields is then prepared, the document is updated
    with new values and finally resubmitted to the index.

**Usage**

``python manage.py resume_index``
    Same as ``python manage.py update_index``

``python manage.py resume_index --limit=1000``

``python manage.py resume_index --offset=1000 --limit=1000``

``python manage.py resume_index --offset=2000``

``python manage.py resume_index --fields=example__movie__actors``
    Will update index fields ``example__movie__actors__movie_set``,
    ``example__movie__actors__name``, etc. See also: :doc:`example`

``clear_index_relations``
-------------------------

.. autoclass:: deepsearch.management.commands.clear_index_relations.Command()

Clears all :class:`~deepsearch.models.IndexRelation` objects. Does not
prompt for user input.

**Options**

``--clear-index``
    Also invoke ``clear_index`` command of Haystack. Accepts any of its
    parameters.

**Usage**

``python manage.py clear_index_relations``

``python manage.py clear_index_relations --clear-index --noinput``
