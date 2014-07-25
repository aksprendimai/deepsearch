# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):
        orm.Actor(name=u'Mark Hamill').save()
        orm.Actor(name=u'Harrison Ford').save()

        orm.Director(name=u'George Lucas').save()

        orm.Genre(name=u'Speculative fiction').save()
        orm.Genre(
            name=u'Sci-Fi',
            definition=u'Science Fiction',
            parent=orm.Genre.objects.get(name=u'Speculative fiction')).save()
        orm.Genre(
            name=u'Space Opera',
            definition=u'A play on the term "soap opera"',
            parent=orm.Genre.objects.get(name=u'Sci-Fi')).save()

        star_wars = orm.Movie(title=u'Star Wars')
        star_wars.save()

        star_wars.genres.add(orm.Genre.objects.get(name=u'Space Opera'))
        star_wars.directors.add(orm.Director.objects.get(name=u'George Lucas'))
        star_wars.actors.add(orm.Actor.objects.get(name=u'Mark Hamill'))
        star_wars.actors.add(orm.Actor.objects.get(name=u'Harrison Ford'))
        star_wars.save()

        blade_runner = orm.Movie(title=u'Blade Runner')
        blade_runner.save()

        blade_runner.genres.add(orm.Genre.objects.get(name=u'Sci-Fi'))
        blade_runner.actors.add(orm.Actor.objects.get(name='Harrison Ford'))
        blade_runner.save()

    def backwards(self, orm):
        orm.Movie.objects.all().delete()
        orm.Person.objects.all().delete()
        orm.Actor.objects.all().delete()
        orm.Director.objects.all().delete()
        orm.Genre.objects.all().delete()

    models = {
        u'movies.actor': {
            'Meta': {'object_name': 'Actor', '_ormbases': [u'movies.Person']},
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['movies.Person']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'movies.director': {
            'Meta': {'object_name': 'Director', '_ormbases': [u'movies.Person']},
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['movies.Person']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'movies.genre': {
            'Meta': {'object_name': 'Genre'},
            'definition': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['movies.Genre']", 'null': 'True'})
        },
        u'movies.movie': {
            'Meta': {'object_name': 'Movie'},
            'actors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['movies.Actor']", 'symmetrical': 'False'}),
            'directors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['movies.Director']", 'symmetrical': 'False'}),
            'genres': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['movies.Genre']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'movies.person': {
            'Meta': {'object_name': 'Person'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['movies']
    symmetrical = True
