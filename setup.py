from setuptools import find_packages, setup

setup(
    name="FastqHeat",
    version='0.0.1',
    maintainer="Quantori",
    python_requires=">=3.6",
    description="",
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'beautifulsoup4',
        'requests',
        'pandas',
        'pyyaml',
        'urllib3',
    ],
    extras_require={
        "test": ["pytest>=7,<8"],
    },
)
