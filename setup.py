from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in thirvu_bpm_biometric/__init__.py
from thirvu_bpm_biometric import __version__ as version

setup(
	name="thirvu_bpm_biometric",
	version=version,
	description="Biometric",
	author="Thirvusoft",
	author_email="thirvusoft@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
