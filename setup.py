from setuptools import find_packages, setup


def find_required():
    with open("requirements.txt") as f:
        return f.read().splitlines()


def find_dev_required():
    with open("requirements-dev.txt") as f:
        return f.read().splitlines()


setup(
    name="vedro-flaky-steps",
    version="1.1.0",
    description="vedro-flaky-steps plugin for vedro framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Bogdan Polianok",
    author_email="miner34006@gmail.com",
    python_requires=">=3.7",
    url="https://github.com/miner34006/vedro-flaky-steps",
    license="Apache-2.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"vedro_flaky_steps": ["py.typed"]},
    install_requires=find_required(),
    tests_require=find_dev_required(),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
    ],
)
