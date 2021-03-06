# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Configuration file for JupyterHub
import os
from jupyterhub.spawner import Spawner

c = get_config()

# Set Tornado headers
c.JupyterHub.tornado_settings = {'headers':{'Cache-Control':'no-store', 'Pragma':'no-cache', 'X-Frame-Options': 'DENY', 'X-XSS-Protection': '1', 'X-Content-Type-Options': 'nosniff'}}

# We rely on environment variables to configure JupyterHub so that we
# avoid having to rebuild the JupyterHub container every time we change a
# configuration parameter.
#c.JupyterHub.debug_proxy = True
# Spawn single-user servers as Docker containers
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
# Spawn containers from this image
c.DockerSpawner.container_image = os.environ['DOCKER_NOTEBOOK_IMAGE']
# JupyterHub requires a single-user instance of the Notebook server, so we
# default to using the `start-singleuser.sh` script included in the
# jupyter/docker-stacks *-notebook images as the Docker run command when
# spawning containers.  Optionally, you can override the Docker run command
# using the DOCKER_SPAWN_CMD environment variable.
spawn_cmd = os.environ.get('DOCKER_SPAWN_CMD', "start-singleuser.sh")
c.DockerSpawner.extra_create_kwargs.update({ 'command': spawn_cmd })
# Connect containers to this Docker network
network_name = os.environ['DOCKER_NETWORK_NAME']
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
# Pass the network name as argument to spawned containers
c.DockerSpawner.extra_host_config = { 'network_mode': network_name }

# Copy Required Environment to user container
kg_url = os.environ['KG_URL']
kg_auth_token = os.environ['KG_AUTH_TOKEN']
validate_kg_cert = os.environ['VALIDATE_KG_CERT']
kg_client_key = os.getenv('KG_CLIENT_KEY')
kg_client_cert = os.getenv('KG_CLIENT_CERT')
kg_client_ca = os.getenv('KG_CLIENT_CA')
kg_env_whitelist = os.getenv('KG_ENV_WHITELIST')
c.DockerSpawner.environment = { 'KG_URL': kg_url , 'KG_AUTH_TOKEN': kg_auth_token, 'VALIDATE_KG_CERT': validate_kg_cert, 'KG_CLIENT_KEY': kg_client_key, 'KG_CLIENT_CERT': kg_client_cert, 'KG_CLIENT_CA': kg_client_ca, 'KG_ENV_WHITELIST': kg_env_whitelist}

# Explicitly set notebook directory because we'll be mounting a host volume to
# it.  Most jupyter/docker-stacks *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/work'
c.DockerSpawner.notebook_dir = notebook_dir
# Mount the security directory that the notebook will store TLS certificates in
# for connecting to Jupyter Kernel Gateway with.
security_dir = os.environ.get('DOCKER_SECURITY_DIR') or '/etc/jupyterpki'
####c.DockerSpawner.security_dir = security_dir
# Mount the real user's Docker volume on the host to the notebook user's
# notebook directory in the container
###c.DockerSpawner.volumes = { 'jupyterhub-user-{username}': notebook_dir }
c.DockerSpawner.volumes = { 'jupyterhub-user-{username}': notebook_dir, 'jupyterhub-user-security-{username}': security_dir }
c.DockerSpawner.extra_create_kwargs.update({ 'volume_driver': 'local' })
# Remove containers once they are stopped
c.DockerSpawner.remove_containers = True
# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = 'jupyterhub'
c.JupyterHub.hub_port = 8080

# TLS config
c.JupyterHub.port = 443
c.JupyterHub.ssl_key = os.environ['SSL_KEY']
c.JupyterHub.ssl_cert = os.environ['SSL_CERT']

# Persist hub data on volume mounted inside container
data_dir = os.environ.get('DATA_VOLUME_CONTAINER', '/data')
c.JupyterHub.db_url = os.path.join('sqlite:///', data_dir, 'jupyterhub.sqlite')
c.JupyterHub.cookie_secret_file = os.path.join(data_dir,
    'jupyterhub_cookie_secret')

# Whitlelist users and admins
c.Authenticator.whitelist = whitelist = set()
c.Authenticator.admin_users = admin = set()
c.JupyterHub.admin_access = True
pwd = os.path.dirname(__file__)
with open(os.path.join(pwd, 'userlist')) as f:
    for line in f:
        if not line:
            continue
        parts = line.split()
        if parts:
            name = parts[0]
            whitelist.add(name)
            if len(parts) > 1 and parts[1] == 'admin':
                admin.add(name)
