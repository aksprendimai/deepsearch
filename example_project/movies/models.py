# -*- coding: utf-8 -*-

from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name


class Actor(Person):
    pass


class Director(Person):
    pass


class Genre(models.Model):
    parent = models.ForeignKey('self', null=True)
    name = models.CharField(max_length=200)
    definition = models.TextField()

    def __unicode__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    genres = models.ManyToManyField(Genre)
    directors = models.ManyToManyField(Director)
    actors = models.ManyToManyField(Actor)

    def __unicode__(self):
        return self.title
