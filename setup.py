import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(*rnames)).read()

setup(name='webmailbox',
      version='0.1dev',
      author='Kaizhao Zhang',
      author_email='zhangkaizhao@gmail.com',
      license='MIT',
      description="Web mailbox to manage mails.",
      long_description=(read('README.txt') +
                        '\n\n' +
                        read('CHANGES.txt')),
      classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=['setuptools', 'tornado', 'pymongo', 'redis'],
      extras_require = dict(encoding=['chardet']),
      entry_points={
          'console_scripts':
            ['webmailbox = webmailbox.application:main'],
      }
      )
