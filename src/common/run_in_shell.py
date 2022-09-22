import subprocess, shlex, logging, time, pathlib, sys, os


project_dir = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(project_dir)

from src.common.logger import getLogger
from src.common.rabbitmq_service import PikaPublisher

logger = getLogger(__file__)



def run_shell_command(command:str,channel="/",publish=True):

   
    if publish: 
        pika_pub = PikaPublisher(queue_name=channel)

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
                    if publish:
                        pika_pub.publish( message={'log':line})
                    logger.info(channel + ": " +line)
                time.sleep(0.1)
       
    
    except (OSError,  subprocess.CalledProcessError) as exception:
        logger.exception(channel + ":" +'Exception occured: ' + str(exception))
        logger.error(channel + ":" +'Subprocess failed')
        if publish:
            pika_pub.publish( message={'error': 'Exception occured: ' + str(exception)})
            pika_pub.publish( message={'error':'Subprocess failed!'})
        return False
    else:
        # no exception was raised
        logger.info(channel + ":" +'Subprocess succeded!')
        if publish:
            pika_pub.publish( message={'info': 'Subprocess succeded!'})

    return True

if __name__=="__main__":
    sample_logger_path = os.path.join(project_dir, "src/tests/sample_logging_process.py")
    run_shell_command(command=f'python {sample_logger_path}', channel='test')