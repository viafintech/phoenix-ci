![phoenix_icon](phoenix_icon.png)
# Phoenix-CI
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/viafintech/phoenix-ci) ![GitHub repo size](https://img.shields.io/github/repo-size/viafintech/phoenix-ci)

Phoenix-CI is a small python-based tool to automate the creation and removal of Gitlab CI runners on the Hetzner Cloud.
Phoenix-CI was originally developed in May 2019 and has been used since then in production by viafintech GmbH for almost all of their CI jobs - except some that require explicit virtualization for Qemu/VirtualBox.

Phoenix-CI helped us to reduce our monthly CI costs by about 45%* while increasing ability to run parallel jobs and thus also increasing speed for each job. By default one CI job will run on one runner at a time to also reduce interference and fight for resources.

\*We compared costs from a single Hetzner EX41S-SSD (4C/8T Core i7-6700, 64GB, 500GB SSD) to 9 CX21 Cloud servers

Read more about Phoenix-CI in our [dedicated blogpost here](https://www.sysorchestra.com/introducing-phoenix-ci-for-gitlab-for/).

# How does it work?
Phoenix-CI is a simple python script that utilizes the Hetzner Cloud API to dynamically spawn dedicated gitlab-runner instances for your Gitlab CI without the need and operational costs of Kubernetes.
For example, it runs in the morning on business days to spawn up fresh runners for the day by a simple Gitlab CI Schedule. At the end of the day another Schedule runs to remove the runners again and deleting the cloud servers to save money. While removing runners in the evening you can also define how many runners you expect to be there, so you can have some spare servers available during the night in case you need to run emergency CI jobs quickly.

Once a week you can also run a full cleanup jobs where you can tell Phoenix-CI to reduce the number of runners to zero. So the next schedule on a monday will spawn fresh runners in the morning.

# What does it support?
Phoenix-CI currently supports spawning docker (DinD) runners and shell runners but it can easily be extended using own cloud-init configs.
It also supports defining which types of cloud servers you want to spawn (default is CX21), in which Hetzner Cloud location (default is Falkenstein) and with which operating system (default is Debian 10).

# Requirements
Phoenix-CI is built to run from two or more Gitlab Schedule Pipelines. One project-specific gitlab-runner is needed to run Phoenix-CI. As a best practice you could run that single gitlab-runner also directly on the Gitlab instance itself and limit it to only run the Phoenix-CI repository.
This runner must be able to run python3 and needs python-virtualenv and pip to install it's required modules on each run.

# Steps to configure Phoenix-CI
Follow the steps below to install Phoenix-CI to your on-premise Gitlab. There is currently no official support for hosted Gitlab.
For a more in-depth explanation of the steps including pictures, please read [this Blogpost for a setup on Debian 10](https://sysorchestra.com/).

- Make sure that you have at least one gitlab-runner "shell" instance running for this project, for example on the Gitlab main instance with the following requirements
  - Install `python3`, `python3-virtualenv` and `virtualenv` package (tested on Debian)
  - Become `gitlab-runner` user and generate an ed25519 keypair using `ssh-keygen -t ed25519` and just press enter when asked for location and password
- Clone this repository into your Gitlab instance and configure the gitlab-runner to only run this project for scaling new gitlab-runner instances on the Hetzner Cloud as well as disable "Shared Runners" in the project's CI configuration.
- Edit the cloud-config files depending on your needs or create a new one. The 2 examples will work just fine though.
- Go to project settings -> CI/CD -> Variables and create the following variables needed to properly run Phoenix-CI
  - CI_MASTER_SSHKEY: The master ssh key used by Phoenix-CI to login to a machine and unregister it from Gitlab
    - Insert the `id_ed25519.pub` contents here that you generated in step 1
  - CI_REGISTRATION_TOKEN: Gitlabs CIs runner registration token which can be found in the Admin area under Runners
  - CI_REGISTRATION_URL: Gitlab CIs runner registration URL which also can be found in the Admin area under Runners
  - HCLOUD_TOKEN: The Hetzner Cloud token to be used to create the Hetzner Cloud handle/session
    - Create a separate Hetzner Cloud project for these runners, e.g. "Phoenix-CI"
    - Then see [here](https://docs.hetzner.cloud/#overview-getting-started) for details how to create an API ke for this project
- Go to CI/CD -> Schedules and create a schedule to scale up runners (Docker in this example)
  - Define a time when they should be spawned/deleted as a cron-time
  - Create at least 2 variables named `CI_DOCKER_RUNNER` and `CI_SHELL_RUNNER` with the amount of desired runners (can be zero though!) and CI_RUN with the value 1
    - The CI_RUN variable is checked if a scheduled run is intentionally initiated or not
- Create another Schedule to downscale runners with the same variables but a lower desired amount of runners or zero to completely remove all runners. If you want to hold back runners for emergency runs just use values of 1 or 2 to scale the amount down.

You can also define more schedules depending on your actual needs. You can also define individual schedules for work days and weekends or for times during the day when there should be no Cloud VMs running at all to save money.

# .gitlab-ci.yml

The default .gitlab-ci.yml is automatically used to run a scheduled job. It will check if the current run is desired or not by the CI_RUN variable and if so, it replaces the cloud-inits placeholder config parts with the actual variables defined in step 4 above.
Afterwards it initializes a virtual python environment and installs all required external tools needed to run the phoenix_ci.py script. The script is ultimately invoked with all parameters given by the schedule variables.

# License and Contributions
We distribute the whole Phoenix-CI project under the [MIT license](LICENSE). All contributions are welcome.
