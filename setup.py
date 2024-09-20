from setuptools import setup, find_packages

NAME        = 'AlignmentSoftware'
VERSION     = '0.2.1'
DESCRIPTION = 'Mechanical alignment for optical systems.'
AUTHOR      = 'Pietro Ferraiuolo'
AUTHOR_EMAIL= 'pietro.ferraiuolo@inaf.it'
URL         = 'https://github.com/pietroferraiuolo/AlignmentSoftware'
LICENSE     = 'MIT'
KEYWORDS    = 'Adaptive Optics, Astrophysics, INAF, Arcetri, Alignment'

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(),
    install_requires=required,
    entry_points={
        'console_scripts': [],
    },
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url=URL,
    license=LICENSE,
    keywords=KEYWORDS,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
