import os, sys
import paramiko

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
from src.helpers.env import Env
from src.helpers.log import LOG
from src.helpers.utils import get_error_traceback

HOSTNAME= Env.get("SFTP_HOSTNAME")
USERNAME= Env.get("SFTP_USERNAME")
PASSWORD= Env.get("SFTP_PASSWORD")
PORT= int(Env.get("SFTP_PORT",22))

# https://github.com/paramiko/paramiko/blob/main/demos/demo_sftp.py
remote_dir = '/in/'

def sftp_transfer(local_path: str):
    local_path = local_path.replace("\\", "/")
    file_name= local_path.split("/")[-1]
    remote_path = os.path.join(remote_dir, file_name)
    # Get the file size
    file_size = os.stat(local_path).st_size
    LOG.log("SFTP").info(f"File `{file_name}` transfer [START]")
    
    # Create an SFTP client
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOSTNAME, PORT, USERNAME, PASSWORD)
        with  ssh.open_sftp() as sftp:
            try:
                # dirlist on remote host
                dirlist = sftp.listdir(remote_dir)
                print("Dirlist: %s" % dirlist)

                # Check if the file exists on the remote server
                try:
                    # Check if the remote file exists
                    sftp.stat(remote_path)
                    LOG.log("SFTP").warning('File already exists on the remote server. Overwriting...')
                    # If the file already exists, delete it to ensure overwriting
                    sftp.remove(remote_path)
                except IOError:
                    pass

                # Upload a file to the SFTP server
                sftp.put(
                    local_path, 
                    remote_path, 
                    callback=lambda transferred_bytes, total_bytes: 
                        LOG.log("SFTP").debug(f"Transferred {transferred_bytes} / {file_size} bytes, progress: {round(100*transferred_bytes/file_size,2)}%"))

                LOG.log("SFTP").info(f"File `{file_name}` transfer was successful.")
                return True
            except Exception as e:
                LOG.log("SFTP").error(f"File `{file_name}` transfer failed with error: {get_error_traceback(e)}")
    return False

if __name__ == "__main__":
    local_path = r'C:\Users\melkh\Desktop\dukto\workdir\altice_media\Bouygues_TVS\app\data\video_encoded\FR_ORSG_SHIE_SHIN_0005_020_F.mxf'
    sftp_transfer(local_path)

