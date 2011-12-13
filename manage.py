#!/usr/bin/env python
import os
from migrate.versioning.shell import main

if __name__ == '__main__':
  url = os.environ.get('DATABASE_URL','postgresql://localhost/flows')
  repository=os.environ.get('REPOSITORY','.')
  main(debug='False',url=url,repository=repository)
