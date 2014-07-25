Indexes
===================================

The following classes extend from ``haystack.indexes.ModelSearchIndex``.

.. autoclass:: deepsearch.indexes.FieldsSearchIndex()
    :show-inheritance:

.. autoclass:: deepsearch.indexes.InheritedFieldsSearchIndex()
    :show-inheritance:

.. autoclass:: deepsearch.indexes.RelatedSearchIndex()
    :show-inheritance:
    :members:
    :exclude-members: get_fields

.. autoclass:: deepsearch.indexes.DeepSearchIndex()
    :show-inheritance:

Subtree wrappers
----------------

Subtree wrappers are used to mark nodes in the ``includes`` tree for
extended or custom behavior.

.. autoclass:: deepsearch.indexes.SubtreeWrapper()

.. autoclass:: deepsearch.indexes.Recursive()

.. autoclass:: deepsearch.indexes.Unicode()

Other
-----

.. autofunction:: deepsearch.indexes.dynamic_index(model, base_indexes=(BasicSearchIndex,))

.. autoclass:: deepsearch.indexes.LimitedContentTypeIndexMixin()
