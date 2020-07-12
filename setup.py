import setuptools

# with open("README.md", "r") as fh:
# long_description = fh.read()

setuptools.setup(
    name="okt",
    version="0.0.1",
    py_modules=['okt'],
    install_requires=[
        'Click',
        'requests',
    ],
    entry_points='''
        [console_scripts]
        okt=okt:cli
    ''',
    author="Indranil Jha",
    author_email="indranilokg@gmail.com",
    description="CLI tool for Okta",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/indranilokg/ij-okta-cli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
