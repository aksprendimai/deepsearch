# -*- coding: utf-8 -*-

from django.contrib import admin
from django.db.models.fields import FieldDoesNotExist
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _

import haystack

from fields import AccessorField
from indexes import ImplicitAccessor
from models import FieldBoost, IndexRelation


class IndexedModelFilter(admin.filters.SimpleListFilter):
    title = _(u'model')
    parameter_name = 'selected_model'

    def __init__(self, request, params, model, model_admin):
        search_index = haystack.connections['default'].get_unified_index()
        self.all_index_fields = search_index.all_searchfields()
        super(IndexedModelFilter, self).__init__(request, params, model, model_admin)

    @staticmethod
    def parse_model(index_fieldname):
        try:
            app_label, model_name = index_fieldname.split('__')[:2]
        except ValueError:
            return None
        model = get_model(app_label, model_name)
        return model

    def lookups(self, request, model_admin):
        lookup_set = set()
        for index_fieldname in self.all_index_fields.keys():
            if index_fieldname == 'text':
                continue

            model = self.parse_model(index_fieldname)
            prefix = model._meta.app_label + '__' + model._meta.module_name
            verbose_name = model._meta.verbose_name.capitalize()
            lookup_set.add((prefix, verbose_name))

        return sorted(lookup_set)

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(index_fieldname__startswith=self.value())
        return queryset


class FieldBoostAdmin(admin.ModelAdmin):
    list_display = ('model_path', 'model_attr', 'boost')
    list_editable = ('boost',)
    search_fields = ('index_fieldname',)
    list_filter = (IndexedModelFilter,)
    actions = None
    ordering = ('index_fieldname',)
    readonly_fields = ('index_fieldname', 'user')

    def __init__(self, *args, **kwargs):
        super(FieldBoostAdmin, self).__init__(*args, **kwargs)
        search_index = haystack.connections['default'].get_unified_index()
        self.all_index_fields = search_index.all_searchfields()

    def _should_skip(self, field):
        registered = field.index_fieldname in self.all_index_fields
        accessor_type = isinstance(field, AccessorField)
        return (not registered) or (not accessor_type)

    def model_path(self, instance):
        if self._should_skip(instance):
            return instance.index_fieldname

        index_field = self.all_index_fields[instance.index_fieldname]
        model = IndexedModelFilter.parse_model(index_field.index_fieldname)
        accessor = ImplicitAccessor(model, index_field._accessor_path[:-1], {})
        path = accessor._model_path()

        return ' > '.join(item._meta.verbose_name.capitalize() for item in path)

    model_path.short_description = _(u'model')

    def model_attr(self, instance):
        if self._should_skip(instance):
            return instance.index_fieldname

        index_field = self.all_index_fields[instance.index_fieldname]
        try:
            model_field = index_field.related_model._meta.get_field(index_field.model_attr)
            return model_field.verbose_name
        except FieldDoesNotExist:
            return index_field.model_attr

    model_attr.short_description = _(u'field')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(FieldBoost, FieldBoostAdmin)


class IndexRelationAdmin(admin.ModelAdmin):
    list_display = (
        'indexable_ct',
        'indexable_id',
        'indexable_object',
        'related_ct',
        'related_id',
        'related_obj',
    )
    ordering = ('indexable_ct', 'indexable_id')
    list_filter = (
        'indexable_ct',
        'related_ct'
    )
    actions = None

    def related_obj(self, obj):
        """
        Workaround for displaying related_object. Using related_object in
        list display crashes because of tables in separate databases
        """
        related_model = obj.related_ct.model_class()
        try:
            related_object = related_model.objects.get(pk=obj.related_id)
            return unicode(related_object)
        except related_model.DoesNotExist:
            return _(u'Not found')
    related_obj.short_description = _(u'related object')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(IndexRelation, IndexRelationAdmin)
