import setuptools

with open("README.md", 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="zq-tools",
    version="1.1.0",
    author="zzqq2199",
    author_email="zhouquanjs@qq.com",
    description="A collection of tools for zzqq2199",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["zq_tools", "zq_tools/bogging"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "colorlog >= 6.6",
        "colorful",
        "bogging"
    ]
)