
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ddh1api",
    version="0.1a",
    author="Tim Herzog",
    # author_email="author@example.com",
    description="DDH1api provides a rudimentary python interface to the World Bank's Development Data Hub (DDH) intended for internal use by World Bank staff.",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tgherzog/ddh1api",
    packages=setuptools.find_packages(),
    # include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ],
    install_requires=['requests', 'PyYAML'],
    python_requires='>=3.0',
)
