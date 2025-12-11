"""Setup configuration for SEC EDGAR Analytics Platform."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sec-edgar-analytics",
    version="0.1.0",
    author="Aakash Bhatt",
    author_email="your-email@example.com",
    description="Production-grade SEC EDGAR financial data analytics platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abhatt13/sec-edgar-analytics",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "google-cloud-storage>=2.14.0",
        "google-cloud-bigquery>=3.14.1",
        "google-cloud-functions>=1.14.0",
        "pyspark>=3.5.0",
        "pandas>=2.1.4",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
    },
)
