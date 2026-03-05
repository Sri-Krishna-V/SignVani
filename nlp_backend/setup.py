"""
SignVani Setup Script

Install SignVani as a Python package:
    pip install -e .  (development mode)
    pip install .     (production mode)
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text(
    encoding='utf-8') if readme_path.exists() else ''

# Read requirements
requirements_path = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name='signvani',
    version='0.1.0',
    author='SignVani Team',
    description='Speech-to-Indian Sign Language Translator for Raspberry Pi 4',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/your-repo/sign-vani',  # Update with actual repo URL
    packages=find_packages(exclude=['tests*', 'scripts*', 'assets*']),
    python_requires='>=3.8',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-timeout>=2.2.0',
            'pytest-cov>=4.1.0',
            'memory-profiler>=0.61.0',
            'black>=23.12.1',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'signvani=main:main',  # Will create 'signvani' command
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
    ],
    keywords='sign-language speech-recognition asr indian-sign-language raspberry-pi vosk',
    project_urls={
        'Bug Reports': 'https://github.com/your-repo/sign-vani/issues',
        'Source': 'https://github.com/your-repo/sign-vani',
    },
)
