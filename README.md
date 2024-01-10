# Supaero robotics, 2024

This repository contains the exercices for the robotics class at Supaero, 2024.
The exercices are organized by notebook. Each notebook corresponds to one chapter of the class.
The notebooks are in Python and based on the software [Pinocchio](https://github.com/stack-of-tasks/pinocchio).

## Set up

### Default setup

You **must** use a [virtualenv](https://docs.python.org/3/library/venv.html) or a similar.

For example on ubuntu, you can get started with:
```bash
sudo apt install python3-pip python3-venv
```

Once in your virtual environment, install this package:
```bash
pip install -U pip
pip install .
```

After that, you can start the server with `jupyter notebook`

### Docker

If the default setup is not working for you, you can use the virtualization provided by Docker. A Docker image is provided, and can be started with:

```bash
docker run --rm -p 7000:7000 -p 7001:7001 -p 7002:7002 -p 7003:7003 -p 7004:7004 -p 8888:8888 -v data:/home/user/tp -it gepetto/supaero2024
```

On Linux host systems, you may simply start the Docker with:

```bash
docker run --rm --net host -v data:/home/user/tp -it gepetto/supaero
```

In case of big update, you must update the docker:
```bash
docker pull gepetto/supaero2024
```

### Update the notebooks

If the repository changes (for example when new tutorials are pushes), you need to update your local
version by "pulling" it from the repository.
On a native installation, just go in the folder containing the tutorials and execute `git pull`

With a docker, execute the following:
```bash
docker run --rm -v data:/home/user/tp -it gepetto/supaero git remote set-url origin https://github.com/gepetto/supaero2024
```
Then
```bash
docker run --rm -v data:/home/user/tp -it gepetto/supaero git pull --rebase origin main
```

To avoid conflict when pulling a new version, you should better do your modifications in copy of the original files,
not directly in the original files itself.

## Side notes

### Installing docker

See [how to get Docker](https://docs.docker.com/get-docker/).

## Docker as normal user

To avoid the need to run `sudo docker`:

```bash
sudo usermod -aG docker nmansard
newgrp docker
```

# Join me on \[Matrix\]

[\[Matrix\]](https://matrix.org/) is a distributed chat system that will be used during the class. Consider [creating
an account](https://app.element.io/#/register) and join [the classroom
channel](https://matrix.to/#/#supaero-robotics-2024:laas.fr).

# Set up of the system ... for admin only

## Build and push the docker

Build the docker as specified in Dockerfile. You need the buildkit for that. The following file +/etc/docker/deamon_json+ should contain:
```json
{ "features" : { "buildkit" : true } }
```
Add DOCKER_BUILDKIT=1 in your environment and restart docker.
```bash
sudo systemctl restart docker
export DOCKER_BUILDKIT=1
```
Then build:
```bash
docker build -t gepetto/supaero2024 .
```
Log to Docker-hub using your credentials.
```bash
docker login
```
Use the login corresponding to +https://hub.docker.com/+.
And push it to the Gepetto repository of Docker-hub.
```bash
docker push gepetto/supaero2024
```
