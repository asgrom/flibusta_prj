from setuptools import setup, find_packages

import flibusta_opds

setup(
    name='flibusta_opds',
    version=flibusta_opds.__version__,
    packages=find_packages(),
    url='',
    license='',
    author='Alexandr Gromkov',
    author_email='as.grom@gmail.com',
    description='Просмотр OPDS каталога библиотеки Флибуста',
    long_description=open('README.md').read(),
    include_package_data=True,
    install_requires=['lxml', 'jinja2', 'requests', 'USER_AGENT'],
    entry_points={
        'console_scripts': [
            'flibusta-opds = flibusta_opds.webview:main'
        ]
    }
)
