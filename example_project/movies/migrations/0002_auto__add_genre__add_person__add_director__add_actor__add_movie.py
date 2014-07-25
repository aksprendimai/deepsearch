# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Genre'
        db.create_table(u'movies_genre', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['movies.Genre'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('definition', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'movies', ['Genre'])

        # Adding model 'Person'
        db.create_table(u'movies_person', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'movies', ['Person'])

        # Adding model 'Director'
        db.create_table(u'movies_director', (
            (u'person_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['movies.Person'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'movies', ['Director'])

        # Adding model 'Actor'
        db.create_table(u'movies_actor', (
            (u'person_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['movies.Person'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'movies', ['Actor'])

        # Adding model 'Movie'
        db.create_table(u'movies_movie', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'movies', ['Movie'])

        # Adding M2M table for field genres on 'Movie'
        m2m_table_name = db.shorten_name(u'movies_movie_genres')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('movie', models.ForeignKey(orm[u'movies.movie'], null=False)),
            ('genre', models.ForeignKey(orm[u'movies.genre'], null=False))
        ))
        db.create_unique(m2m_table_name, ['movie_id', 'genre_id'])

        # Adding M2M table for field directors on 'Movie'
        m2m_table_name = db.shorten_name(u'movies_movie_directors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('movie', models.ForeignKey(orm[u'movies.movie'], null=False)),
            ('director', models.ForeignKey(orm[u'movies.director'], null=False))
        ))
        db.create_unique(m2m_table_name, ['movie_id', 'director_id'])

        # Adding M2M table for field actors on 'Movie'
        m2m_table_name = db.shorten_name(u'movies_movie_actors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('movie', models.ForeignKey(orm[u'movies.movie'], null=False)),
            ('actor', models.ForeignKey(orm[u'movies.actor'], null=False))
        ))
        db.create_unique(m2m_table_name, ['movie_id', 'actor_id'])


    def backwards(self, orm):
        # Deleting model 'Genre'
        db.delete_table(u'movies_genre')

        # Deleting model 'Person'
        db.delete_table(u'movies_person')

        # Deleting model 'Director'
        db.delete_table(u'movies_director')

        # Deleting model 'Actor'
        db.delete_table(u'movies_actor')

        # Deleting model 'Movie'
        db.delete_table(u'movies_movie')

        # Removing M2M table for field genres on 'Movie'
        db.delete_table(db.shorten_name(u'movies_movie_genres'))

        # Removing M2M table for field directors on 'Movie'
        db.delete_table(db.shorten_name(u'movies_movie_directors'))

        # Removing M2M table for field actors on 'Movie'
        db.delete_table(db.shorten_name(u'movies_movie_actors'))


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