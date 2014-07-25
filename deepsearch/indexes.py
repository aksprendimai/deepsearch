# -*- coding: utf-8 -*-

from django.db.models.fields.related import (
    ForeignKey,
    ForeignRelatedObjectsDescriptor,
    ManyRelatedObjectsDescriptor,
    ReverseManyRelatedObjectsDescriptor,
    ReverseSingleRelatedObjectDescriptor,
)
from django.contrib.contenttypes.models import ContentType

from haystack.indexes import ModelSearchIndex, BasicSearchIndex
from haystack.query import SearchQuerySet


from fields import AccessorField, BlankTemplateCharField, RecursiveAccessorField
from models import IndexRelation


class FieldsSearchIndex(ModelSearchIndex):
    text = BlankTemplateCharField(document=True)

    def get_fields(self, fields=None, excludes=None):
        model = self.get_model()
        if fields is None:
            fields = self._get_model_field_names(model)

        declared_fields = getattr(self._meta, 'fields', [])
        if declared_fields:
            fields = [fn for fn in fields if fn in declared_fields]
        declared_excludes = getattr(self._meta, 'excludes', [])
        if declared_excludes:
            fields = [fn for fn in fields if fn not in declared_excludes]

        index_fields = {}
        for field_name in fields:
            if not model._meta.get_field(field_name).primary_key:  # skip primary keys
                new_field = AccessorField(model, [field_name], model, model_attr=field_name)
                index_fields[new_field.index_fieldname] = new_field

        return index_fields

    def _get_model_field_names(self, model):
        field_names = []
        for f in model._meta.local_fields + model._meta.local_many_to_many:
            field_names.append(f.name)
        return field_names


class InheritedFieldsSearchIndex(FieldsSearchIndex):
    """
    Same as ``FieldsSearchIndex`` but also includes fields of base models
    (from ``model._meta.get_parent_list()``).
    """

    def get_fields(self, fields=None, excludes=None):
        model_field_names = set(self._get_model_field_names(self.get_model()))
        base_model_field_names = self._base_model_field_names(self.get_model())
        model_field_names.update(base_model_field_names)
        return super(InheritedFieldsSearchIndex, self).get_fields(fields=model_field_names)

    def _base_model_field_names(self, model):
        """
        Collects field names of parent models.
        """
        base_models = model._meta.get_parent_list()
        inherited_field_names = set()
        for base_model in base_models:
            inherited_field_names.update(self._get_model_field_names(base_model))
        return inherited_field_names


class RelatedSearchIndex(ModelSearchIndex):
    """
    Indexes a model including its related models (forwards and backwards
    through foreign keys). By default it collects the unicode representations
    of all related instances.

    The design is as follows:

    #. You may mark a node in the includes dict with a ``SubtreeWrapper``
       instance.

    #. ``SubtreeWrapper`` wraps a dict (a branch of the includes dict-tree) and
       additionally knows what accessor class to create (``ImplicitAccessor``
       by default).

    #. When ``RelatedSearchIndex.get_fields`` is executed (during its
       ``__init__``), for each ``SubtreeWrapper`` ``create_accessor`` method
       is called (if a wrapper is not used, ``ImplicitAccessor`` is created).

    #. Accessors hold information required to create ``AccessorField``
       instances (specifically, the model being indexed and accessor path to
       the value; the path may lead to a model or a field; in any case
       ``AccessorField`` prepares the unicode representation of the Python
       object at the end of the path). Fields created by ``create_fields``
       call on an accessor are collected and included in the index.

    Additional ``Meta`` options:
        ``model``
            the indexable model (required)
        ``fields``
            a list of model attributes to be indexed
        ``includes``
            a nested dict that specifies multi-level relations that
            should also be included in the index. The value of each dict
            item must also be a dict or a SubtreeWrapper instance.
        ``includes_only``
            index only model fields and includes (default False)
        ``excludes``
            a list of model attributes to be excluded (backwards
            relation attributes may also be specified here)
        ``global_excludes``
            a list of model attributes to be excluded for
            every (non-root) node in the includes tree
    """

    def __init__(self, overwrite_stored_data=True, extra_field_kwargs=None):
        """
        :param overwrite_stored_data:
            when updating an object, overwrite the document stored in the
            index. You may want to disable overwriting if you are updating
            only a part of the document (using a subset of index fields).
            See method ``full_prepare`` for more details.
        """
        super(RelatedSearchIndex, self).__init__(extra_field_kwargs)
        self._overwrite_stored_data = overwrite_stored_data

    def retain_fields(self, prefixes):
        """
        Modifies the index in place. Keeps only those index fields that
        start with any of the specified prefixes (a list of strings).

        :param prefixes: a list of strings
        :type prefixes: tuple or list
        """
        fields_subset = {}
        for field_name, field in self.fields.iteritems():
            if field_name.startswith(tuple(prefixes)):
                fields_subset[field_name] = field
        self.fields = fields_subset

    def full_prepare(self, obj):
        if self._overwrite_stored_data:  # default behavior
            IndexRelation.objects.as_indexable(obj).delete()
            # during full_prepare each field will repopulate IndexRelations
            prepared_data = super(RelatedSearchIndex, self).full_prepare(obj)
            return prepared_data

        # otherwise if self._overwrite_stored_data is False we keep all IndexRelations

        # first we fetch the document as it is stored in the index
        ct_identifier = '{0}.{1}'.format(obj._meta.app_label, obj._meta.module_name)
        indexed_result = SearchQuerySet().filter(django_ct=ct_identifier, django_id=obj.pk)
        document = indexed_result[0].get_stored_fields() if indexed_result else {}

        # next we prepare the data, which may have less fields than the stored document
        prepared_data = super(RelatedSearchIndex, self).full_prepare(obj)
        document.update(prepared_data)  # update stored document with new values
        return document

    def remove_object(self, instance, using=None, **kwargs):
        # invoked on post_delete
        IndexRelation.objects.as_indexable(instance).delete()
        super(RelatedSearchIndex, self).remove_object(instance, using, **kwargs)

    def get_fields(self, fields=None, excludes=None):
        """
        Returns the fields that the base index class created with all of the
        new index fields representing related values.
        """
        index_fields = super(RelatedSearchIndex, self).get_fields(fields, excludes)
        index_fields.update(self._create_accessor_fields())  # will overwrite fields with the same name
        return index_fields

    def _create_accessor_fields(self):
        model = self.get_model()
        index_fields = {}

        includes = getattr(self._meta, 'includes', {})
        declared_accessors = self._collect_declared_paths(includes)

        # TODO don't skip getattr(self._meta, 'fields', [])

        # implicit accessors cover only the first level, so compare them to
        # only the first node of each declared path
        declared_paths = set(each.path[0] for each in declared_accessors)
        excluded = set(getattr(self._meta, 'excludes', [])) | declared_paths

        includes_only = getattr(self._meta, 'includes_only', False)
        implicit_accessors = []
        if not includes_only:
            implicit_accessors = self._collect_implicit_accessors(model)
            implicit_accessors = [i for i in implicit_accessors if i.path[0] not in excluded]

        for accessor in implicit_accessors + declared_accessors:
            for created_field in accessor.create_fields():
                index_fields[created_field.index_fieldname] = created_field

        return index_fields

    def _collect_declared_paths(self, dict_tree):
        """
        Traverses the dict_tree (includes option in Meta) and
        creates an accessor object for each node in the tree.
        Returns a list of accessors.
        """
        accessor_paths = []
        queue = [([], dict_tree)]
        global_excludes = getattr(self._meta, 'global_excludes', {})

        while queue:
            base_path, subtree = queue.pop(0)

            if not subtree:
                continue

            for branch_name, branch in subtree.iteritems():
                path = base_path + [branch_name] if base_path else [branch_name]
                queue.append((path, branch))

                if isinstance(branch, SubtreeWrapper):
                    accessor = branch.create_accessor(self.get_model(), path, excludes=global_excludes)
                else:
                    accessor = ImplicitAccessor(self.get_model(), path, branch, excludes=global_excludes)

                accessor_paths.append(accessor)

        return accessor_paths

    def _collect_implicit_accessors(self, model=None):
        if model is None:
            model = self.get_model()

        many_to_many_accessors = [rel.get_accessor_name() for rel in self._backwards_relations(model)]
        foreign_key_accessors = [f.name for f in self._foreign_keys(model)]

        accessor_names = many_to_many_accessors + foreign_key_accessors
        return [ImplicitAccessor(model, [name], {}, fields_indexing=False) for name in accessor_names]

    def _backwards_relations(self, model):
        relations = model._meta.get_all_related_objects()
        relations += model._meta.get_all_related_many_to_many_objects()
        return relations

    def _foreign_keys(self, model):
        return [f for f in model._meta.fields if isinstance(f, ForeignKey)]


class DeepSearchIndex(RelatedSearchIndex, InheritedFieldsSearchIndex):
    """
    Recommended to use to combine features of ``RelatedSearchIndex``
    and ``InheritedFieldsSearchIndex``.
    """
    text = BlankTemplateCharField(document=True)


class LimitedContentTypeIndexMixin(object):
    """
    Limits model queryset to exclude objects of derived types. Helps when
    you want to have non-overlapping indexes for base and derived models.
    """
    def build_queryset(self, *args, **kwargs):
        queryset = super(LimitedContentTypeIndexMixin, self).build_queryset(*args, **kwargs)
        content_type = ContentType.objects.get_for_model(self.get_model())
        queryset = queryset.filter(content_type=content_type)
        return queryset


def dynamic_index(model, base_indexes=(BasicSearchIndex,)):
    """
    Dynamically creates an index class for the specified model. For example::

        MyModelIndex = dynamic_index(MyModel, (ModelSearchIndex,))

    This is the same as::

        class MyModelIndex(ModelSearchIndex):
            class Meta:
                model = MyModel
    """
    index_name = 'Dynamic{0}Index'.format(model.__name__)
    meta = type('Meta', (object,), {'model': model})
    index_class = type(index_name, base_indexes, {'Meta': meta})
    return index_class


class ImplicitAccessor(object):
    """
    Contains information used to access a related model. Creates index fields.
    """

    # TODO maybe combine accessor and wrapper classes to reduce complexity and confusion

    def __init__(
            self, model, path, subtree,
            field_class=AccessorField, fields_indexing=True, excludes=None):
        """
        model: indexable model, the root of the path
        path: a list of strings (class attribute names),
            which represents a path to a related model
        subtree: a subtree of includes option in Meta of RelatedSearchIndex;
            must implement itermitems method
        field_class: the accessor creates search index fields of this class;
            must be a subclass of AccessorField
        fields_indexing: if True, the accessor will create a search index field
            for each model field in the related model (at the end of the path)
        excludes: if fields_indexing is True, skip these model attributes
            when creating index fields
        """
        self.model = model
        self.path = path
        self.subtree = subtree
        self.field_class = field_class
        self.fields_indexing = fields_indexing
        self.excludes = set(excludes) if excludes is not None else set()

    def __repr__(self):
        return '<{0} {1}.{2}>'.format(
            type(self).__name__, self.model.__name__, '__'.join(self.path))

    def __iter__(self):
        return self.subtree.itermitems()

    def _model_path(self):
        model_path = [self.model]
        for attr in self.path:
            attr_value = getattr(model_path[-1], attr)
            if isinstance(attr_value, ForeignRelatedObjectsDescriptor):  # something_set
                model_path.append(attr_value.related.model)
            elif isinstance(attr_value, ManyRelatedObjectsDescriptor):  # many-to-many
                model_path.append(attr_value.related.model)
            elif isinstance(attr_value, ReverseSingleRelatedObjectDescriptor):  # foreignkey
                model_path.append(attr_value.field.rel.to)
            elif isinstance(attr_value, ReverseManyRelatedObjectsDescriptor):  # many-to-many
                model_path.append(attr_value.field.rel.to)
        return model_path

    @property
    def related_model(self):
        model_path = self._model_path()
        if not self.fields_indexing:
            return model_path[-2] if len(model_path) > 1 else self.model
        return model_path[-1]

    def _create_field(self, model, accessor_path, related_model, *args, **kwargs):
        return self.field_class(model, accessor_path, related_model, *args, **kwargs)

    def create_fields(self):
        if not self.fields_indexing:
            return [self._create_field(self.model, self.path, self.related_model)]

        model_index = dynamic_index(self.related_model, (InheritedFieldsSearchIndex,))
        # FIXME do not include foreign keys that point to the "parent" object (e.g. oid)
        value_attrs = set(f.model_attr for f in model_index().fields.values())
        if None in value_attrs:
            value_attrs.remove(None)  # default haystack document field name
        value_attrs -= self.excludes

        created_fields = []
        for value_attr in value_attrs:
            path = self.path + [value_attr]
            created_fields.append(self._create_field(self.model, path, self.related_model))
        return created_fields


class RecursiveAccessor(ImplicitAccessor):
    """
    When following the accessor path (self.path) recursively includes
    instances accessed by the specified recursive_attribute.
    """

    # FIXME right now only applies at the leaves of the tree
    # TODO does not support fields indexing and excludes parameters

    def __init__(
            self, model, path, subtree,
            recursive_attribute, field_class=RecursiveAccessorField):
        # sets fields_indexing to False
        super(RecursiveAccessor, self).__init__(model, path, subtree, field_class, False)
        self.recursive_attribute = recursive_attribute

    def __repr__(self):
        return '<{0} {1}.{2} on {3}>'.format(
            type(self).__name__, self.model.__name__, self.path, self.recursive_attribute)

    def _create_field(self, model, accessor_path, related_model):
        params = model, accessor_path, related_model, self.recursive_attribute
        return super(RecursiveAccessor, self)._create_field(*params)


class SubtreeWrapper(object):
    """
    May be used to customize ``RelatedSearchIndex``
    ``Meta`` option ``includes``.

    Example usage::

        class MyModelIndex(DeepSearchIndex, Indexable):
            class Meta:
                model = MyModel
                includes = {
                    'some_attr': SubtreeWrapper({  # not really needed here
                        'other_attr': {},
                        'another_attr': {},
                    }),
                    'some_attr': SubtreeWrapper({}, accessor_class=MyCustomAccessor),
                }
    """

    # TODO explicit and excluded fields options

    def __init__(self, subtree, excludes=None, accessor_class=ImplicitAccessor):
        self.subtree = subtree
        self.excludes = set(excludes) if excludes is not None else set()
        self.accessor_class = accessor_class

    def iteritems(self):
        return self.subtree.iteritems()

    def create_accessor(self, model, path, excludes=None):
        """
        :param model: indexable model, the root of the path
        :param list path:
            a list of strings (class attribute names),
            which represents a path to a related model
        :param list excludes:
            (optional) in addition to ``self.excludes``, model attributes
            to skip when creating index fields
        """
        excludes = self.excludes | set(excludes)
        return self.accessor_class(model, path, self.subtree, excludes=excludes)


class Recursive(SubtreeWrapper):
    """
    When traversing accessor path also include objects by following recursive
    relations (recursive field is specified with parameter ``on``).

    .. note:: ``Recursive`` usage is very limited. It only applies on the last
        level of attribute path and collects unicode values only.

    Example usage::

        class MyModelIndex(DeepSearchIndex, Indexable):
            class Meta:
                model = MyModel
                includes = {
                    # recursive values are included in the same index field
                    'some_attr': Recursive({}, on='recursive_attr'),

                    # recursive values are included in a separate index field
                    'other_attr': {
                        'recursive_attr': Recursive({}, on='recursive_attr'),
                    },

                    # we can go deeper:
                    'another_attr': {
                        'recursive_attr': {
                            'recursive_attr': Recursive({}, on='recursive_attr'),
                        },
                    },
                }
    """
    def __init__(self, subtree, on, accessor_class=RecursiveAccessor):
        super(Recursive, self).__init__(subtree, excludes=None, accessor_class=accessor_class)
        self.recursive_attribute = on  # e.g. attribute name of a ForeignKey that points to self

    def create_accessor(self, model, path, excludes=None):
        # ignores excludes
        return self.accessor_class(model, path, self.subtree, self.recursive_attribute)


class Unicode(SubtreeWrapper):
    """
    Index the unicode representation object at the end of the path (does not
    create index fields for each model field).
    """
    def __init__(self, subtree={}, accessor_class=ImplicitAccessor):
        self.subtree = subtree
        self.accessor_class = accessor_class

    def create_accessor(self, model, path, excludes=None):
        # ignores excludes
        return self.accessor_class(model, path, self.subtree, fields_indexing=False)
