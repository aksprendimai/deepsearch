# -*- coding: utf-8 -*-

from haystack.indexes import Indexable

from deepsearch.indexes import DeepSearchIndex, Recursive, Unicode

from models import Movie


class MovieIndex(DeepSearchIndex, Indexable):
    class Meta:
        model = Movie
        includes = {
            'genres': Recursive({}, on='parent'),
            'directors': {},
            'actors': {
                'movie_set': Unicode({}),
            },
        }
        excludes = ('directors', 'actors')
