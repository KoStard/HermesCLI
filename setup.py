from setuptools import setup, find_packages

def read_requirements(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]

setup(
    name="hermes-cli",
    version="0.1.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=read_requirements('requirements.txt'),  # Read dependencies from requirements.txt
    setup_requires=[
        "wheel",
    ],
    entry_points={
        "console_scripts": [
            "hermes=hermes.main:main",
        ],
    },
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-mock',
        ],
    },
    python_requires='>=3.7',
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful command-line tool for interacting with AI models and processing files",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/KoStard/HermesCLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
