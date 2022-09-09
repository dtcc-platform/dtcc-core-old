import subprocess, shlex, logging, time, pathlib, sys


project_dir = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(project_dir)

from src.common.logger import getLogger

logger = getLogger(__file__)



def run_shell_command(command:str,channel="/",redis_pub_sub=None):

    pub_redis = False
    if redis_pub_sub is not None: pub_redis=True

    command_args = shlex.split(command)

    logger.info('Subprocess: "' + command + '"')

    try:
        with subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as process:
            while process.poll() is None:
                output = process.stdout.read1().decode('utf-8')
                for i, line in enumerate(output.strip().split('\n')):
                    if pub_redis:
                        redis_pub_sub.publish(channel=channel, message=line)
                    logger.info(channel + ": " +line)
                time.sleep(1)
       
    
    except (OSError,  subprocess.CalledProcessError) as exception:
        logger.exception(channel + ":" +'Exception occured: ' + str(exception))
        logger.error(channel + ":" +'Subprocess failed')
        if pub_redis:
            redis_pub_sub.publish(channel=channel, message='Exception occured: ' + str(exception))
            redis_pub_sub.publish(channel=channel, message='Subprocess failed!')
        return False
    else:
        # no exception was raised
        logger.info(channel + ":" +'Subprocess succeded!')
        if pub_redis:
            redis_pub_sub.publish(channel=channel, message='Subprocess succeded!')

    return True

if __name__=="__main__":
    run_shell_command("ls -la -h")