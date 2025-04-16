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
    ],
    python_requires=">=3.6",
    install_requires=[
        "spotipy>=2.22.1",
        "PyQt5>=5.15.9",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "spotify-migrate=main:main",
        ],
    },
)
