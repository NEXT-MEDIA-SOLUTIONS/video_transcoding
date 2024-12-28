#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "environment variables"
__version__ = "1.0"

import os, sys
sys.path.append('.')
workdir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(workdir)

dotenv_file=os.path.join(workdir,".env")
if os.path.isfile(dotenv_file):
    lines=[]
    with open(dotenv_file,'r', encoding="utf-8") as f:
        lines=f.readlines()
    for line in lines:
        line = line.strip()
        if line.startswith("#") or not '=' in line or not line.strip():
            continue

        key, value = line.strip().split('=', 1)
        res = os.getenv(key,None)
        if res is None or res.strip() =='':
            value=value.strip()
            if value.startswith('"'):
                if value.endswith('"'):
                    value=value[1:-1]
                elif '"' in value[1:] :
                    i=value[1:].index('"')+1
                    if value[i+1:].strip().startswith('#'):
                        value=value[1:i]
            elif value.startswith("'"):
                if value.endswith("'"):
                    value=value[1:-1]
                elif "'" in value[1:] :
                    i=value[1:].index("'")+1
                    if value[i+1:].strip().startswith('#'):
                        value=value[1:i]
            else:
                value=value.split("#")[0].strip()

            os.environ[key] = os.path.expandvars(value)
else:
    print(f"env file not found in : '{dotenv_file}' !! exit(1)")
    exit(1)

class Env:

    """This class 'Env' aims to simply the access to your environment variables."""

    @staticmethod
    def get(name, default=None):
        """This function help to return the value of a specific environment variable.
        Parameters:
        name (str) : Name of your environment variable.
        default (any) : Returned value in case your environment variable is not exist.
        Returns:
        any: Returned value of your environment variable.
        """
        value = os.environ.get(name, default)
        if value is None:
            print("<Warning> : Name : \'%s\' of your environment variable not found in \'.env\' file !!!" % name)
        return value

    @staticmethod
    def set(name, value):
        """This function help to set the value for a specific environment variable.
        Parameters:
        name (str) : Name of your environment variable.
        value (any) : Value of your environment variable.
        """
        os.environ[name] = value
        # Write changes to .env file.
        # dotenv.set_key(dotenv_file, name, os.environ[name])

