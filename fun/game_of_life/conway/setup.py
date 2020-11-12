from setuptools import setup
setup(name='life',
      packages=['life'],
      python_requires= '>=3.6',
      install_requires=['pytest', 'Pillow', 'sh'],
      entry_points={'console_scripts' : [

          'to_grid = life.stage:to_grid',

          'as_neighborhoods = life.stage:as_neighborhoods',

          'to_png = life.show:to_png',

          ]})
