# Copyright (C) 2021-2024 Arnaud Belcour - Inria, Univ Rennes, CNRS, IRISA Dyliss
# Univ. Grenoble Alpes, Inria, Microcosme
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

from setuptools import setup

setup(
    name='esmecata',
    url='https://github.com/AuReMe/esmecata',
    license='GPLv3+',
    description=
    'EsMeCaTa: Estimating Metabolic Capabilties from Taxonomy',
    author='AuReMe',
    author_email='gem-aureme@inria.fr',
    packages=['esmecata'],
    package_dir={'esmecata': 'esmecata'},
    entry_points={
        'console_scripts': [
            'esmecata = esmecata.__main__:main',
        ]
    },
    install_requires=['biopython', 'bioservices', 'matplotlib',
    'pandas', 'requests', 'ete3', 'seaborn', 'SPARQLWrapper'],
)