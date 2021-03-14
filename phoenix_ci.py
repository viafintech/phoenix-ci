#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""
Phoenix-CI provides easy management of Gitlab CI nodes
on the Hetzner Cloud.
"""

# Import python modules needed for this tool to run properly.
import sys

try:
    import argparse
    import subprocess
    import uuid
    import hcloud

except ImportError as e:
    print("Missing python module: {}".format(e.message))
    sys.exit(255)


__author__ = 'Martin Seener'
__copyright__ = 'Copyright (C) 2019-2021 viafintech GmbH'
__license__ = 'MIT'
__version__ = '1.0.5'
__maintainer__ = 'Martin Seener'
__email__ = 'martin.seener@viafintech.com'
__status__ = 'Production'


def remove_runner(hc, server):
    """
    The remove_runner function takes a hetzner cloud handle (session) and a server definition,
    logs into the server via SSH to unregister this runner from the Gitlab instance.
    After a successful unregister the runner is destroyed (VM deleted from the Cloud).
    """
    serverip = server.public_net.ipv4.ip
    remove_runner = True
    # Login via SSH and try to unregister this runner from Gitlab
    resp = subprocess.run(
        'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@'
        + serverip
        + ' -C "gitlab-runner unregister --all-runners"',
        shell=True,
        stderr=subprocess.DEVNULL
    )
    if resp.returncode != 0:
        remove_runner = False

    # Remove the cloud server/runner entirely (delete)
    response = hc.servers.delete(server)

    return(response.status, remove_runner)


def create_runner(hc, type, datacenter, servertype, image, userdata):
    """
    The create_runner function takes a hetzner cloud handle (session) and some runner definitions to
    create a new cloud server to be used as a Gitlab CI runner.

    Parameters:
    datacenter:  The datacenter where the new Cloud VM should be created
    name:        The name of the new Cloud VM (default: type and a UUID, for ex. docker-2288393hd92dh9hd23d8h92d)
    server_type: The Cloud VM type. This defines the amount of CPU, RAM, Disk of the VM
    image:       The Operating System Base image to be used for spawning the new Cloud VM (e.g. Debian)
    ssh_keys:    A set of SSH Public keys to be installed into the new Cloud VM for remove management
    user_data:   Takes a cloud-init config for further configuration of the new Cloud VM after spawning (e.g. install additional tools)
    labels:      Adds a label depending on the "type" parameter that is true. This is used to easily find corresponding Cloud VMs easier for
                 later removal
    """
    response = hc.servers.create(
        datacenter=hc.datacenters.get_by_name(name=datacenter),
        name='{}-{}'.format(type, str(uuid.uuid4())),
        server_type=hc.server_types.get_by_name(name=servertype),
        image=hc.images.get_by_name(name=image),
        ssh_keys=hc.ssh_keys.get_all(),
        user_data=userdata,
        labels={type: "true"}
    )

    return(response.action.status)


def scale_runner(hc, type, amount, datacenter, servertype, image, userdata):
    """
    The scale_runner function is the tools main function which is responsible to call create_runner or remove_runner functions
    depending of the number of desired runner it got through the tools parameters (e.g. spawn new servers or remove runners).

    Parameters:
    hc:          A valid Hetzner Cloud handle (session)
    type:        The type of Cloud runner to be created. Currently only docker or shell is supported
    amount:      The total desired amount of "type" Cloud runners to have available in the Cloud. Depending on the actual amount currently of
                 currently available runners, the runners are scaled up or down in the cloud
    datacenter:  The datacenter where the new Cloud VM should be created
    server_type: The Cloud VM type. This defines the amount of CPU, RAM, Disk of the VM
    image:       The Operating System Base image to be used for spawning the new Cloud VM (e.g. Debian)
    userdata:    Takes a cloud-init config for further configuration of the new Cloud VM after spawning (e.g. install additional tools)
    """
    # Get all currently available Cloud VMs of a specific type.
    server_list = hc.servers.get_all(label_selector=type)
    # Read the cloud-init config files contents of a specific type.
    with open(userdata, 'r') as file:
        runner_userdata = file.read()

    # Cound the number of currently running Cloud VMs of the specified type.
    count = len(server_list)
    """
    If the available amount of running servers is larger than the desired amount, remove Cloud VM runners one by one until desired number is reached
    by calling the remove_runner function for each server to be removed.

    If the available amount if running servers is lower than the desired amount, spawn a new Cloud VM runner of the desired type until the desired
    number of running Cloud VMs is reached.
    """
    if count > amount:
        for i in range(count - amount):
            print(
                "Deleting {}: ".format(server_list[i].name),
                end='',
                flush=True
            )
            resp, rmr = remove_runner(hc, server_list[i])
            print("{} (Runner unregistered: {})".format(resp, rmr))
    elif count < amount:
        for i in range(amount - count):
            print(
                "Creating new {}-Runner: ".format(type.title()),
                end='',
                flush=True
            )
            resp = create_runner(
                hc,
                type,
                datacenter,
                servertype,
                image,
                runner_userdata
            )
            print(resp)
    else:
        # If the number of running Cloud VMs is equal to the amount of desired runners, do nothing but return the current state of running/desired runners.
        print("{}-Runner: {}/{} up".format(type.title(), count, amount))


def main(args):
    """
    The main function is called before anything else. In the beginning it will collect all parameters given by the user when the tool is started.
    Some arguments have defaults defined if no arguments are given.
    After gathering of all arguments, the arguments are checked for validity, the Hetzner Cloud handle is being created (new API session)
    and all arguments are then handed over to the scale_runner function for further processing.
    """
    parser = argparse.ArgumentParser(
        description='\
        Phoenix-CI provides easy management of\
        Gitlab CI nodes on the Hetzner Cloud. You can\
        manage gitlab-runner nodes with it.',
    )

    parser.add_argument(
        '-t',
        '--token',
        type=str,
        help='Enter the API Token of your Hetzner Cloud project.',
    )
    parser.add_argument(
        '-d',
        '--docker-runner',
        dest='docker_runner',
        type=int,
        default=2,
        help='Enter the amount of CI Runners with the "Docker" executor\
        that you want to have as a positive integer (default: 2).',
    )
    parser.add_argument(
        '-s',
        '--shell-runner',
        dest='shell_runner',
        type=int,
        default=1,
        help='Enter the amount of CI Runners with the "Shell" executor\
        that you want to have as a positive integer (default: 1).',
    )
    """
    Optional arguments for fine tuning creation
    """
    parser.add_argument(
        '--datacenter',
        type=str,
        default='fsn1-dc14',
        help='Enter the name of the desired Hetzner Cloud datacenter\
        to be used for server creation (default: fsn1-dc14)',
    )
    parser.add_argument(
        '--servertype',
        type=str,
        help='Enter the server type to be used\
        for server creation (default: cx21)',
    )
    parser.add_argument(
        '--image',
        type=str,
        default='debian-10',
        help='Enter the server image to be used\
        for server creation (default: debian-10)',
    )
    parser.add_argument(
        '--docker-userdata',
        dest='dockerdata',
        type=str,
        default='/dev/null',
        help='A file containing valid cloud-init userdata\
        for configuring docker runners.',
    )
    parser.add_argument(
        '--shell-userdata',
        dest='shelldata',
        type=str,
        default='/dev/null',
        help='A file containing valid cloud-init userdata\
        for configuring shell runners.',
    )

    """
    Parse all arguments then check validity of some arguments. Afterwards a new Hetzner Cloud handle (Session) is established
    and the arguments are passed over to the scale_runner function for further processing.
    """
    args = parser.parse_args()
    if isinstance(args.token, str) and isinstance(args.docker_runner, int)\
       and isinstance(args.shell_runner, int):
        print('Running Phoenix-CI ' + __version__)
        hc = hcloud.Client(token=args.token)
        amount = {
            'docker': args.docker_runner,
            'shell': args.shell_runner
        }
        userdata = {
            'docker': args.dockerdata,
            'shell': args.shelldata
        }
        if args.servertype == "":
            # If empty type is given, assume default
            args.servertype = "cx21"
        for type in ['docker', 'shell']:
            scale_runner(
                hc,
                type,
                amount[type],
                args.datacenter,
                args.servertype,
                args.image,
                userdata[type]
            )
    else:
        # If no or invalid arguments are given, the tools help is printed.
        parser.print_help()


if __name__ == '__main__':
    main(sys.argv[1:])
