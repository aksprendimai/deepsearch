# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from haystack.fields import CharField, MultiValueField

from models import IndexRelation


class BlankTemplateCharField(CharField):
    def prepare_template(self, obj):
        return ''

    def prepare(self, obj):
        return ''


class AccessorField(MultiValueField):
    def __init__(self, model, accessor_path, related_model, *args, **kwargs):
        self.null = True
        self._model = model
        self._accessor_path = accessor_path
        self.related_model = related_model  # model at the end of the path

        if 'index_fieldname' not in kwargs:
            index_fieldname = '__'.join([model._meta.app_label, model._meta.module_name] + accessor_path)
            kwargs['index_fieldname'] = index_fieldname

        kwargs['model_attr'] = self._accessor_path[-1]
        super(AccessorField, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '<{0} {1}>'.format(type(self).__name__, self.index_fieldname)

    def prepare(self, obj):
        values = self._collect_objs(obj)
        return self._prepare_values(values)

    def _prepare_values(self, values):
        return set(map(unicode, filter(None, values)))

    def _collect_objs(self, obj):
        """
        Returns objects found at the end of the accessor path. If the path
        ends with a foreign key or a manager attribute name, the returned
        objects will be model instances. If the path ends with a model field
        attribute name, the returned objects will be values of the type of
        that model field.
        """
        current_objs = [obj]
        for accessor in self._accessor_path:
            current_objs = self._collect_attr_values(current_objs, accessor)
            self._update_index_relation(obj, current_objs)
        return current_objs

    def _collect_attr_values(self, objs, attribute):
        values = []
        for instance in objs:
            try:
                attr_value = getattr(instance, attribute)
            except ObjectDoesNotExist:
                continue

            if isinstance(attr_value, models.Manager):
                for r in attr_value.all():
                    values.append(r)
            elif attr_value is not None:
                values.append(attr_value)

        return values

    def _update_index_relation(self, obj, related_objects):
        related_objects = (i for i in related_objects if isinstance(i, models.Model))
        related_objects = (i for i in related_objects if i != obj)  # skip mirrored relations

        for related_object in related_objects:
            IndexRelation.objects.get_or_create(
                related_ct=ContentType.objects.get_for_model(related_object),
                related_id=related_object.pk,
                indexable_ct=ContentType.objects.get_for_model(obj),
                indexable_id=obj.pk)


class RecursiveAccessorField(AccessorField):
    def __init__(
            self, model, accessor_path, related_model,
            recursive_attribute, recursion_depth=10, *args, **kwargs):

        super(RecursiveAccessorField, self).__init__(
            model, accessor_path, related_model, *args, **kwargs)

        self.recursive_attribute = recursive_attribute
        self.recursion_depth = recursion_depth

    def __repr__(self):
        return '<{0} {1} on {2}>'.format(
            type(self).__name__, self.index_fieldname, self.recursive_attribute)

    def _collect_objs(self, obj):
        collected_objs = super(RecursiveAccessorField, self)._collect_objs(obj)

        # Also collect recursively related objects:
        recursive_objs = []
        next = self._collect_attr_values(collected_objs, self.recursive_attribute)

        recursion_level = 0
        while next:
            recursive_objs += next
            next = self._collect_attr_values(next, self.recursive_attribute)

            recursion_level += 1
            if recursion_level > self.recursion_depth:
                break

        collected_objs += recursive_objs
        self._update_index_relation(obj, collected_objs)
        return collected_objs
