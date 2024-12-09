from setuptools import setup, find_packages

def read_requirements(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]

setup(
    name="hermes-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    setup_requires=[
        "wheel",
    ],
    install_requires=read_requirements('requirements.txt'),
    entry_points={
        "console_scripts": [
            "hermes=hermes.main:main",
        ],
    },
    python_requires='>=3.7',
)
