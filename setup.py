from setuptools import setup

setup(name='blender_kitti',
      version='0.0.1',
      description='Render stuff in Blender.',
      url='http://github.com/risteon/blender_kitti',
      author='Christoph Rist',
      author_email='c.rist@posteo.de',
      license='MIT',
      packages=['blender_kitti', 'blender_kitti_example'],
      zip_safe=False,
      install_requires=[
          'ruamel.yaml',
      ],
      python_requires='>=3.5',
      )
