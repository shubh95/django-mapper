from setuptools import setup, find_packages

setup(
    name='django-mapper',
    version='1.1.5',
    description='A utility class for mapping data between Django models',
    author='Shubham Vashisht',
    author_email='shubhvas95@gmail.com',
    url='https://github.com/shubh95/django-mapper',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=[
        'Django>=2.2',
    ],
)

