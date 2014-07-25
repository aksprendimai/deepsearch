How to use
==========

.. seealso::
    :ref:`installation`

We'll demonstrate how :class:`~deepsearch.indexes.DeepSearchIndex`
can be used to index a multi-level hierarchical data structures.
For simplicity and clarity, we'll use a few simple models::

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

An ``Actor`` or ``Director`` is a ``Person``, but there may exist a ``Person``
who is neither of which. Here you could use
:class:`~deepsearch.indexes.LimitedContentTypeIndexMixin` to index
``Person`` objects.

The ``parent`` field of the model ``Genre`` makes it a tree-like structure.
So a ``Genre`` may have its *supergenre*, e.g. *Slasher* is a subgenre of
*Horror*.

Next populate the database with some data::

    Actor(name=u'Mark Hamill').save()
    Actor(name=u'Harrison Ford').save()

    Director(name=u'George Lucas').save()

    Genre(name=u'Speculative fiction').save()
    Genre(
        name=u'Sci-Fi',
        definition=u'Science Fiction',
        parent=Genre.objects.get(name=u'Speculative fiction')).save()
    Genre(
        name=u'Space Opera',
        definition=u'A play on the term "soap opera"',
        parent=Genre.objects.get(name=u'Sci-Fi')).save()

    star_wars = Movie(title=u'Star Wars')
    star_wars.save()

    star_wars.genres.add(Genre.objects.get(name=u'Space Opera'))
    star_wars.directors.add(Director.objects.get(name=u'George Lucas'))
    star_wars.actors.add(Actor.objects.get(name=u'Mark Hamill'))
    star_wars.actors.add(Actor.objects.get(name=u'Harrison Ford'))
    star_wars.save()

Using ``DeepSearchIndex``
-------------------------

We will start with a bare :class:`~deepsearch.indexes.DeepSearchIndex`
for the ``Movie`` model::

    from haystack.indexes import Indexable
    from deepsearch.indexes import DeepSearchIndex
    from example.models import Movie

    class MovieIndex(DeepSearchIndex, Indexable):
        class Meta:
            model = Movie

.. note::
    Index class definitions go to ``search_indexes.py`` file in your app
    directory (along with ``models.py``, ``views.py``, etc). Keep in mind
    that they must also inherit from ``haystack.indexes.Indexable``.
    Otherwise *Haystack* will ignore them.

After rebuilding index, you can inspect indexed data using an app such as
`haystackbrowser <https://github.com/kezabelle/django-haystackbrowser>`_.
Here is the data indexed for the *Star Wars* movie object:

.. code-block:: none

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__genres ['Space Opera']
    example__movie__title ['Star Wars']

You can see that the index collects unique unicode representations (returned
by ``__unicode__`` method) of related objects on the first level. However, you
can also go deeper and include related models' field values by defining the
``includes`` option of the index class::

    class MovieIndex(DeepSearchIndex, Indexable):
        class Meta:
            model = Movie
            includes = {
                'genres': {},
                'directors': {},
                'actors': {},
            }

After rebuilding index, we have:

.. code-block:: none
   :emphasize-lines: 2,4,6-8

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera']
    example__movie__genres__definition ['A play on the term "soap opera"']
    example__movie__genres__name ['Space Opera']
    example__movie__genres__parent ['Sci-Fi']
    example__movie__title ['Star Wars']

``MovieIndex`` now includes fields of related models. For example, the
``definition``, ``name`` and ``parent`` fields of model ``Genre``.

Using ``SubtreeWrapper``
------------------------

Next, we can modify the index to include all of the parent ``Genres``. To do
this use a :class:`~deepsearch.indexes.SubtreeWrapper` class, in this
case :class:`~deepsearch.indexes.Recursive`::

    from deepsearch.indexes import DeepSearchIndex, Recursive

    class MovieIndex(DeepSearchIndex, Indexable):
        class Meta:
            model = Movie
            includes = {
                'genres': {
                    'parent': Recursive({}, on='parent'),
                },
                'directors': {},
                'actors': {},
            }

After rebuilding index, we have:

.. code-block:: none
   :emphasize-lines: 8

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera']
    example__movie__genres__definition ['A play on the term "soap opera"']
    example__movie__genres__name ['Space Opera']
    example__movie__genres__parent ['Sci-Fi', 'Speculative fiction']
    example__movie__title ['Star Wars']

You can see that the index field ``example__movie__genres__parent`` now
contains ``'Speculative fiction'`` which is the parent of ``'Sci-Fi'`` (which
is the parent of ``'Space Opera'``).

.. note:: ``Recursive`` usage is very limited. It only applies on the last
    level of attribute path and collects unicode values only.

We can combine this with :class:`~deepsearch.indexes.Unicode`
wrapper to reduce redundant information about genres::

    from deepsearch.indexes import DeepSearchIndex, Recursive, Unicode

    class MovieIndex(DeepSearchIndex, Indexable):
        class Meta:
            model = Movie
            includes = {
                'genres': Unicode({
                    'parent': Recursive({}, on='parent'),
                }),
                'directors': {},
                'actors': {},
            }

.. code-block:: none
    :emphasize-lines: 5,6

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera']
    example__movie__genres__parent ['Sci-Fi', 'Speculative fiction']
    example__movie__title ['Star Wars']

Or collect all genres into one field::

    class MovieIndex(DeepSearchIndex, Indexable):
        class Meta:
            model = Movie
            includes = {
                'genres': Recursive({}, on='parent'),
                'directors': {},
                'actors': {},
            }

.. code-block:: none
    :emphasize-lines: 5

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera', 'Sci-Fi', 'Speculative fiction']
    example__movie__title ['Star Wars']


More complex cases
------------------

You can use :class:`~deepsearch.indexes.DeepSearchIndex` to follow more
complex and deeply nested structures. When defining ``includes`` tree, keep in
mind that the node names (keys of dicts) are essentially attribute names of
model instances.

.. note:: Having a large ``includes`` tree may lead to **extremely** long
    indexing times. See also :ref:`resume_index <resume-index>` command.

First, let's create another movie object::

    blade_runner = Movie(title=u'Blade Runner')
    blade_runner.save()

    blade_runner.genres.add(Genre.objects.get(name=u'Sci-Fi'))
    blade_runner.actors.add(Actor.objects.get(name='Harrison Ford'))
    blade_runner.save()

Now (even though it is not really meaningful) let's modify ``MovieIndex`` so
that it includes data about other movies in which actors have appeared in::

    class MovieIndex(DeepSearchIndex, Indexable):
        class Meta:
            model = Movie
            includes = {
                'genres': Recursive({}, on='parent'),
                'directors': {},
                'actors': {
                    'movie_set': {},
                },
            }

Note that ``movie_set`` is a backwards relationship manager created by
*Django*.

After rebuilding index, inspect stored data for the movie *Star Wars*:

.. code-block:: none
    :emphasize-lines: 2-5

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__movie_set__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__movie_set__directors ['George Lucas']
    example__movie__actors__movie_set__genres ['Space Opera', 'Sci-Fi']
    example__movie__actors__movie_set__title ['Star Wars', 'Blade Runner']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera', 'Sci-Fi', 'Speculative fiction']
    example__movie__title ['Star Wars']

You can see that the ``MovieIndex`` now has a set of index fields that start
with "``example__movie__actors__movie_set...``". This means that when you search
for *Blade Runner*, *Star Wars* will also appear in the search results because
Harrison Ford plays in both of those two movies.

However, some information may be redundant. Let's mark ``movie_set`` with
``Unicode`` wrapper::

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

This results in fewer index fields:

.. code-block:: none
   :emphasize-lines: 2

    example__movie__actors ['Harrison Ford', 'Mark Hamill']
    example__movie__actors__movie_set ['Star Wars', 'Blade Runner']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors ['George Lucas']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera', 'Sci-Fi', 'Speculative fiction']
    example__movie__title ['Star Wars']

Here we have only one ``example__movie__actors__movie_set`` field which stores
unicode representations of all movies that are related through actors.

As ``actors``, ``directors`` are explicit many-to-many fields of the model
``Movie``, they are included in the index by default (see first example). At
this point we have overridden ``genres`` behavior, but fields ``actors`` and
``directors`` are redundant. So let's exclude them::

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

.. code-block:: none

    example__movie__actors__movie_set ['Star Wars', 'Blade Runner']
    example__movie__actors__name ['Harrison Ford', 'Mark Hamill']
    example__movie__directors__name ['George Lucas']
    example__movie__genres ['Space Opera', 'Sci-Fi', 'Speculative fiction']
    example__movie__title ['Star Wars']

Views
-----

Setting up *Django* views works the usual way as with *Haystack*. However
*deepsearch* comes with a custom search form which allows query-time
field boosting. **It works only with Solr backend and uses DisMax mode.**

How to get started:

1. Add the following code to your urls:

   .. code-block:: python

       from haystack.views import SearchView
       from deepsearch.forms import DeepSearchForm

       # add this to urlpatterns:
       url(r'^search/', SearchView(form_class=DeepSearchForm))

2. Create ``search/search.html`` template:

   .. code-block:: html

       <h2>Search</h2>

       <form method="get" action=".">
          <table>
              {{ form.as_table }}
              <tr>
                  <td>&nbsp;</td>
                  <td>
                      <input type="submit" value="Search">
                  </td>
              </tr>
          </table>

          {% if query %}
              <h3>Results</h3>

              {% for result in page.object_list %}
                  <p>
                      <a href="{{ result.object.get_absolute_url }}">{{ result.object.title }}</a>
                  </p>
              {% empty %}
                  <p>No results found.</p>
              {% endfor %}

              {% if page.has_previous or page.has_next %}
                  <div>
                      {% if page.has_previous %}<a href="?q={{ query }}&amp;page={{ page.previous_page_number }}">{% endif %}&laquo; Previous{% if page.has_previous %}</a>{% endif %}
                      |
                      {% if page.has_next %}<a href="?q={{ query }}&amp;page={{ page.next_page_number }}">{% endif %}Next &raquo;{% if page.has_next %}</a>{% endif %}
                  </div>
              {% endif %}
          {% else %}
              {# Show some example queries to run, maybe query syntax, something else? #}
          {% endif %}
       </form>

3. Your search page should now be accessible. From here you can change the
   template or write you own custom ``SearchView``.

4. You can visit ``/admin/deepsearch/fieldboost/`` to change field
   weight values. As they are stored in the database, you do not need to
   restart the server nor rebuild the index for the new weights to be applied.
