from setuptools import setup

setup(
    name="blender_kitti",
    version="0.0.1",
    description="Render stuff in Blender.",
    url="http://github.com/risteon/blender_kitti",
    author="Christoph Rist",
    author_email="c.rist@posteo.de",
    license="MIT",
    packages=["blender_kitti", "blender_kitti_examples"],
    zip_safe=False,
    install_requires=["ruamel.yaml", "click", "numpy", "decorator",],
    python_requires=">=3.5",
    entry_points={
        "console_scripts": ["blender_kitti_render=blender_kitti.cli:render"]
    },
)
