from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="spotify-data-migration",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for migrating data between Spotify accounts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/spotify_data_migration",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.6",
    install_requires=[
        "spotipy>=2.22.1",
        "PyQt5>=5.15.9",
        "python-dotenv>=1.0.0",
        "cryptography>=39.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "pylint>=2.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "spotify-migrate=src.main:main",
        ],
        "gui_scripts": [
            "spotify-migrate-gui=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
