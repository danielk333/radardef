import setuptools

setuptools.setup(
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"": ["*.ini", "*.txt", "*.npz", "*.npy", "antpos.csv*"]},
    include_package_data=True,
)
