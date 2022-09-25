import setuptools

with open("README.md", 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="zq-tools",
    version="0.8.3",
    author="zzqq2199",
    author_email="zhouquanjs@qq.com",
    description="A collection of tools for zzqq2199",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["zq_tools"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "colorlog == 6.6"
    ]
)