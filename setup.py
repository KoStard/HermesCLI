from setuptools import setup, find_packages

setup(
    name="hermes-cli",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "anthropic",
        "boto3",
        "google-generativeai",
        "python-docx",
        "PyPDF2",
        "rich",
        "openai",
        "argcomplete"
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
        ],
    },
    test_suite='tests',
)
