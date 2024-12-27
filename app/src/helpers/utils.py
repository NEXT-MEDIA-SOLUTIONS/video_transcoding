#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "io handler"
__version__ = "1.0"

import sys, os, io, json
import subprocess as sp

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.helpers.env import Env
    from src.helpers.log import LOG
except ImportError:
    from ..helpers.env import Env
    from ..helpers.log import LOG

pyv=int(sys.version_info.major)
if pyv not in [2,3]:
    print("ERROR :: Python version not recognized py='%s' => exit(1)" % pyv)
    exit(1)

log_flag = Env.get('APP_LOG')=='true'
cmd_timeout=10*60*60

def save_json(data, path):
    with io.open(path, "w", encoding="utf-8") as f:
        # json.dump(data, f, ensure_ascii=False, indent=4)
        # To get utf8-encoded file as opposed to ascii-encoded in the accepted answer for Python 2 use:
        f.write(json.dumps(data, ensure_ascii=False, indent=5))

def get_error_traceback(e):
    d=None
    if pyv>=3:
        d={
            "filename": str(e.__traceback__.tb_frame.f_code.co_filename),
            "name": str(e.__traceback__.tb_frame.f_code.co_name),
            "line": int(e.__traceback__.tb_lineno),
            "type": str(type(e)),
            "message": str(e)
        }
    else:
        d={
            "filename": str(sys.exc_info()[2].tb_frame.f_code.co_filename),
            "name": str(sys.exc_info()[2].tb_frame.f_code.co_name),
            "line": int(sys.exc_info()[2].tb_lineno),
            "type": str(sys.exc_info()[0].__name__),
            "message": str(e)
        }
    return json.dumps(d)

def bytes_to_str(st):
    if st is None:
        return None
    if isinstance(st, bytes):
        try:
            return  st.decode('utf-8').strip()
        except UnicodeDecodeError:
            return  st.decode('latin-1').strip()
    return str(st).strip()
    
def exec_cmd(cmd, timeout=cmd_timeout):
    """Exécution d'une commande shell dans un process séparé.

    Arguments:
        cmd {str} -- Commande shell à exécuter.

    Returns:
        entier -- Code retour de l'exécution de la commande :
                    str type - Succès: le stdout du commande
                    None - Echec: avec afiche sur le log l'erreur
    """
    LOG.log().info(f"Appel de la commande: {cmd}")
    stdout, stderr, process = None, None, None
    process = sp.Popen(str(cmd), shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except sp.TimeoutExpired:
        # Dans cet exemple, nous lançons une commande externe avec `subprocess.Popen` et utilisons la méthode `communicate()` avec un timeout en secondes. 
        # Si le processus ne se termine pas avant l'expiration du délai, nous tuons le processus avec `process.kill()` et récupérons les sorties standard et d'erreur.
        process.kill()
        stdout, stderr = process.communicate()
        stderr=bytes_to_str(stderr)
        stdout=bytes_to_str(stdout)
        LOG.log().error(f"Le processus a expiré après {timeout} secondes" +
              "\n==> stderr: \n"+stderr+"\n==> stdout: \n"+stdout)
        return False, None, None
    except sp.CalledProcessError as e:
        LOG.log().error(f"Erreur lors de l'appel à la commande: {e}")
        return False, None, None
    except Exception as e:
        LOG.log().error(f"Unexpected lors de l'appel à la commande: {e}")
        return False, None, None

    returncode = int(process.returncode)
    stderr=bytes_to_str(stderr)
    stdout=bytes_to_str(stdout)
    if returncode != 0 and stderr is not None and stderr != '':
        LOG.log().error("Erreur lors de l'appel à la commande; returncode="+str(returncode) +
              "\n==> stderr: \n"+stderr+"\n==> stdout: \n"+stdout)
        return False, stdout, stderr
    # print("\n==> stderr: \n"+bytes_to_str(stderr)+"\n==> stdout: \n"+bytes_to_str(stdout))
    LOG.log().info(f"Succès de la commande {cmd}")
    return True, stdout, stderr


def touch(fname, mode=0o777, dir_fd=None, **kwargs):
    flags = ( os.O_APPEND 
            | os.O_WRONLY  # access mode: write only
            | os.O_CREAT  # create if not exists
            | os.O_TRUNC  # truncate the file to zero
        )
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(
            f.fileno() if os.utime in os.supports_fd else fname,
            dir_fd=None if os.supports_fd else dir_fd,
            **kwargs
        )


def convert_seconds_to_dhms(duration):
    duration=int(duration)
    days, remainder = divmod(duration, 3600*24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(days):02d}D{int(hours):02d}H{int(minutes):02d}M{int(seconds):02d}S"
