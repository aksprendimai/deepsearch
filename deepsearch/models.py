# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _


class FieldBoost(models.Model):
    """
    Stores field weight values which are used during query time. Use command
    ``init_boosts`` to create a single ``FieldBoost`` object for every index
    field.

    ``FieldBoost`` values can be managed in ``FieldBoostAdmin``.
    """
    index_fieldname = models.CharField(
        max_length=255, unique=True, default='', verbose_name=_(u'field'))
    """unique index field name"""

    user = models.ForeignKey(User, null=True, verbose_name=_(u'user'))

    boost = models.FloatField(default=1.0, verbose_name=_(u'weight'))
    """float value for field weight"""

    class Meta:
        verbose_name = _(u'field weight')
        verbose_name_plural = _(u'field weights')

    def __unicode__(self):
        return u"{0} | {1}".format(self.index_fieldname, self.boost)


class IndexRelationManager(models.Manager):
    def _build_queryset(self, instance, ct_field, id_field):
        ct = lambda model: ContentType.objects.get_for_model(model)

        try:
            model = type(instance)
            by_content_type = Q(**{ct_field: ct(model)})
            # An object may be referenced as one of its base model classes
            for base in model._meta.get_parent_list():
                by_content_type |= Q(**{ct_field: ct(base)})

            # Base and derived model instances share the same primary keys
            return self.filter(by_content_type, **{id_field: instance.pk})

        except ValueError:  # instance.pk is not int
            return self.none()

    def as_indexable(self, indexable_object):
        return self._build_queryset(indexable_object, 'indexable_ct', 'indexable_id')

    def as_related(self, related_object):
        return self._build_queryset(related_object, 'related_ct', 'related_id')


class IndexRelation(models.Model):
    """
    Links two objects: an indexable and a related. When an object is being
    indexed, its ``AccessorFields`` store all of the objects, which were
    encountered while following the accessor path, as related. This allows
    "backwards" reindexing. When some object is modified, we can look up
    what objects it is related to and reindex them, keeping the index fresh.

    ``IndexRelation`` objects can be viewed in ``IndexRelationAdmin``.
    """

    indexable_ct = models.ForeignKey(
        ContentType, related_name='+',
        verbose_name=_(u'indexable content type'))
    indexable_id = models.PositiveIntegerField()
    #: ``GenericForeignKey`` to an indexed object.
    indexable_object = generic.GenericForeignKey('indexable_ct', 'indexable_id')

    related_ct = models.ForeignKey(
        ContentType, related_name='+', verbose_name=_(u'related content type'))
    related_id = models.PositiveIntegerField()
    #: ``GenericForeignKey`` to its related object.
    related_object = generic.GenericForeignKey('related_ct', 'related_id')

    objects = IndexRelationManager()

    def __unicode__(self):
        fmt = u'{0}#{1} w/ {2}#{3}'
        return fmt.format(
            self.indexable_ct.model_class().__name__, self.indexable_id,
            self.related_ct.model_class().__name__, self.related_id)

    class Meta:
        unique_together = (
            'related_ct', 'related_id',
            'indexable_ct', 'indexable_id',
        )
        verbose_name = _(u'index relation')
        verbose_name_plural = _(u'index relations')
