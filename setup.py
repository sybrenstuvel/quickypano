# -*- encoding: utf8 -*-
import glob
import io
import re
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ).read()


setup(
    name="quickypano",
    version="0.1.0",
    license="BSD",
    description="Simple panorama project creator for Hugin, aimed at 360/180 degree panoramas",
    long_description="%s\n%s" % (read("README.rst"),
                                 re.sub(":obj:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst"))),
    author="Sybren A. Stüvel",
    author_email="sybren@stuvel.eu",
    url="https://bitbucket.com/sybren/quickypano",
    packages=find_packages('.'),
    package_dir={'': 'src'},
    # py_modules=[splitext(basename(i))[0] for i in glob.glob("src/*.py")],
    include_package_data=False,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Utilities",
    ],
    # keywords=[
    #     # eg: "keyword1", "keyword2", "keyword3",
    # ],
    install_requires=[
        read('requirements.txt').split('\n')  # eg: "aspectlib==1.1.1", "six>=1.7",
    ],
    # extras_require={
    #     # eg: 'rst': ["docutils>=0.11"],
    # },
    entry_points={
        "console_scripts": [
            "qp_create = quickypano_cli.create_project:main",
            "qp_stitch = quickypano_cli.stitch:main",
            "qp_switch = quickypano_cli.switch_source:main",
        ]
    }

)
