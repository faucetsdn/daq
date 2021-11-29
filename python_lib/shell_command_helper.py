"""Module to help run shell commands and retrieve output"""

from __future__ import absolute_import
import subprocess
import multiprocessing


class ShellCommandHelper():
    """Hosts methods to run shell commands and retrieve output"""

    TEN_MIN_SEC = 10 * 60

    def __init__(self):
        pass

    def _run_process_command(self, command, capture=False):
        """
        Args:
            command: Takes an str line or list[str] to be run in shell
            capture: Setting to True captures stdout, stderr and return code
        returns:
            Popen object
        """
        command_list = command.split() if isinstance(command, str) else command
        pipeout = subprocess.PIPE if capture else None
        return subprocess.Popen(command_list, stdout=pipeout, stderr=pipeout)

    def _reap_process_command(self, process):
        """
        Args:
            process: Popen object to reap
        returns:
            return code of command, stdout, stderr
        """
        process.wait(timeout=self.TEN_MIN_SEC)
        stdout, stderr = process.communicate()
        strout = str(stdout, 'utf-8') if stdout else None
        strerr = str(stderr, 'utf-8') if stderr else None
        return process.returncode, strout, strerr

    # pylint: disable=too-many-arguments
    def run_cmd(self, cmd, arglist=None, strict=True,
                capture=False, docker_container=None, detach=False):
        """
        Args:
            cmd: command to be executed
            arglist: Additional arguments to add to command
            strict: Raises exception if command execution fails
            capture: Prints out and captures stdout and stderr output of command
            docker_container: Set if command needs to be run within a docker container
        returns:
            return code of command, stdout, stderr
        """
        command = ("docker exec %s " % docker_container) if docker_container else ""
        command = command.split() + ([cmd] + arglist) if arglist else command + cmd
        print('Running command %s' % command)
        if detach:
            self._run_process_command(command, capture=capture)
            return None, None, None
        retcode, out, err = self._reap_process_command(
            self._run_process_command(command, capture=capture))
        if strict and retcode:
            if capture:
                print('stdout: \n%s' % out)
                print('stderr: \n%s' % err)
            raise Exception('Command execution failed: %s' % str(command))
        return retcode, out, err

    def parallelize(self, target, target_args, batch_size=200):
        """
        Parallelizes multiple runs of a target method with multiprocessing.
        Args:
            target_args: List of tuples which serve as args for target.
                        List size determines number of jobs
            target: Target method
            batch_size: Thread pool size
        """
        jobs = []
        for arg_tuple in target_args:
            process = multiprocessing.Process(target=target, args=arg_tuple)
            jobs.append(process)

        batch_start = 0
        while batch_start <= len(jobs):
            batch_end = batch_start + batch_size
            batch_jobs = jobs[batch_start:batch_end]

            for job in batch_jobs:
                job.start()

            for job in batch_jobs:
                job.join()
                job.close()

            batch_start = batch_end
