from distutils.core import setup

setup(
    name='deepsearch',
    version='0.1',
    author='Atviro Kodo Sprendimai',
    # author_email='info@aksprendimai.lt',  # TODO GZL
    packages=['deepsearch'],
    url='https://github.com/aksprendimai/deepsearch',
    license='LICENSE.txt',
    description='A Haystack extension used to index deep and nested model relationships.',
    # long_description=open('README.rst').read(),
    install_requires=[
        "Python >= 2.6",
        "Django >= 1.4.8",
        "django-haystack >= 2.1.0",
        "South >= 0.8",
    ],
)
