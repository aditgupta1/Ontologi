from distutils.core import setup

setup(name='concept_query',
    version='1.0',
    description='ConceptQuery',
    packages=[
        'concept_query', 
        'concept_query.core', 
        'concept_query.db', 
        'concept_query.text_parser'
    ],
    package_data={
        'concept_query.text_parser': ['lib/plural_to_singular.json']
    },
)