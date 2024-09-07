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
        "PyPDF2==3.0.1",
        "rich",
        "openai",
        "argcomplete",
        "pyyaml",
        "pyreadline3; sys_platform == 'win32'",
        "ollama",
        "pdfminer.six",
        "markdownify",
        "groq",
        "python-docx",
    ],
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
    description="A powerful command-line tool for interacting with AI models, processing files, and executing workflows",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/KoStard/HermesCLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
