import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="citrix-adc-frrouting-sync",
    version="0.0.1",
    author="VirtualDesktopDevops",
    author_email="author@example.com",
    description="Advertise RHI enabled Citrix ADC CPX VIP using Frrouting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/virtualdesktopdevops/citrix-adc-frrouting-sync",
    packages=["citrix_adc_frrouting"],
    scripts=['citrixadcfrrsync.py'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=[
          'python-daemon',
          'requests'
      ],
)
