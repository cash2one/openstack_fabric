#!/usr/bin/env python
# encoding: utf-8

from fabric.api import *
from configs import *

env.user = "root"
env.password = "root"

controller = ['controller']

network = ['network']

compute = [
	'compute01',
	'compute02',
	'compute04',
	'compute05',
	'compute06',
]

nodes = controller + network + compute

with open("/root/.ssh/id_rsa.pub", "r") as f:
	line = f.read()
	with open(AUTH_KEYS, "w") as g:
		g.write(line)

env.roledefs = {
	'controller' : controller,
	'network' : network,
	'compute' : compute,
	'all' : nodes,
}

@roles('all')
def _ssh_keygen_and_gather():
	run("ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa")
	key = run("cat ~/.ssh/id_rsa.pub")
	f = open(AUTH_KEYS, 'a')
	f.write(key + "\n")
	f.close()

@roles('all')
def _dispatch_auth_key():
	put(AUTH_KEYS, '~/.ssh/authorized_keys')
	run('chmod 600 ~/.ssh/authorized_keys')

@roles('all')
def _clean_auth_key():
	run('rm -f /root/.ssh/*')

@roles('all')
def _put_hosts():
	put(HOST_LIST, HOST_LIST)

@roles('all')
def _test_connection():
	run('hostname')

# -----------------------
# 1. add openstack repo
# -----------------------
@roles('all')
@parallel
def _local_repo():
	#backup origin repo
	with cd("/etc/yum.repos.d"):
		run('mkdir backup && mv CentOS-* backup || echo "exits"')
	put(LOCAL_CENTOS7_REPO, CENTOS7_REPO)
	put(LOCAL_EPEL7_REPO, EPEL7_REPO)
	put(LOCAL_OPENSTACK_REPO, OPENSTACK_REPO)
	run('yum clean all')
	run('yum makecache')
	run('yum upgrade -y')

# -----------------------
# 2. install ntp
# -----------------------
@roles('all')
def _setup_ntp():
	run("yum install -y ntp")
	put(LOCAL_NTP_CONFIG, NTP_CONFIG)
	run("systemctl enable ntpd.service")
	run("systemctl restart ntpd.service")
	run("systemctl status ntpd.service")

# -----------------------
# 3. install selinux
# -----------------------
@roles('all')
@parallel
def _setup_selinux():
	run("yum install -y openstack-selinux")

# -----------------------
# 4. install DB on controller
# -----------------------
@roles('controller')
def _setup_database():
	run("yum install -y mariadb mariadb-server MySQL-python")
	put(LOCAL_MY_CONF, MY_CONF)
	run("systemctl enable mariadb.service")
	run("systemctl restart mariadb.service")
	run("systemctl status mariadb.service")
	run("mysqladmin -uroot -p" + MYSQL_PW + " password '" + MYSQL_PW+ "'")



# ========================================== #
#                  tasks                     #
# ========================================== #

def inject_auth():
	execute(_dispatch_auth_key)

def make_auth():
	execute(_ssh_keygen_and_gather)
	execute(_dispatch_auth_key)

def clean_auth():
	execute(_clean_auth_key)

def update_hosts():
	execute(_put_hosts)

def setup_ntp():
	execute(_setup_ntp)

def openstack_repo():
	execute(_local_repo)

def test():
	execute(_test_connection)

def all():
#	execute(_local_repo)
#	execute(_setup_ntp)
#	execute(_setup_selinux)
	execute(_setup_database)

