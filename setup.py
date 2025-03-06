from setuptools import setup


setup(
    setup_requires=['setuptools_scm'],
    name='parsec-python',
    use_scm_version=True,
    author='lunexnocty',
    author_email='lunex_nocty@qq.com',
    description='A Monadic Parser Combinator for Python',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lunexnocty/parsec-python',
    packages=['parsec'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: LGPL-2.1 License',
        'Operating System :: OS Independent',
        'Typing :: Typed',
    ],
    python_requires='>=3.10',
)
