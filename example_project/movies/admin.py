# -*- coding: utf-8 -*-

from django.contrib import admin
from models import Actor, Director, Genre, Movie


class ActorAdmin(admin.ModelAdmin):
    model = Actor

admin.site.register(Actor, ActorAdmin)


class DirectorAdmin(admin.ModelAdmin):
    model = Director

admin.site.register(Director, DirectorAdmin)


class GenreAdmin(admin.ModelAdmin):
    model = Genre

admin.site.register(Genre, GenreAdmin)


class MovieAdmin(admin.ModelAdmin):
    model = Movie

admin.site.register(Movie, MovieAdmin)
