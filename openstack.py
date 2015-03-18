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
	put(LOCAL_OPENSTACK_DB, OPENSTACK_DB)
	run("chmod 777 " + OPENSTACK_DB)

# -----------------------
# 5. install RabbitMQ on controller
# -----------------------
@roles('controller')
def _setup_rabbitmq():
	run("yum install -y rabbitmq-server")
	run("systemctl enable rabbitmq-server.service")
	run("systemctl restart rabbitmq-server.service")
	run("rabbitmqctl change_password guest guest")
	run("echo '[{rabbit, [{loopback_users, []}]}].' > /etc/rabbitmq/rabbitmq.config")
	run("systemctl restart rabbitmq-server.service")
	run("systemctl status rabbitmq-server.service")

# -----------------------
# 6. install keystone on controller
# -----------------------
@roles('controller')
def _setup_keystone():
	run("openstack-db --drop --service keystone --rootpw root")
	run("openstack-db --init --service keystone --rootpw root")
	run("yum install -y openstack-keystone python-keystoneclient")
	put(LOCAL_KEYSTONE_CONF, KEYSTONE_CONF)
	run("keystone-manage pki_setup --keystone-user keystone --keystone-group keystone")
	run("chown -R keystone:keystone /var/log/keystone")
	run("chown -R keystone:keystone /etc/keystone/ssl")
	run("chmod -R o-rwx /etc/keystone/ssl")
	run("su -s /bin/sh -c 'keystone-manage db_sync' keystone")
	run("systemctl enable openstack-keystone.service")
	run("systemctl restart openstack-keystone.service")
	run("systemctl status openstack-keystone.service")

# -----------------------
# 7. basic info in keystone
# -----------------------
@roles('controller')
def _basic_in_keystone():
	with shell_env(OS_SERVICE_TOKEN='admin', OS_SERVICE_ENDPOINT="http://controller:35357/v2.0"):
		run("keystone tenant-create --name admin --description 'Admin Tenant'")
		run("keystone user-create --name admin --pass admin --email admin@inspur.com")
		run("keystone role-create --name admin")
		run("keystone user-role-add --user admin --tenant admin --role admin")
		run("keystone tenant-create --name demo --description 'Demo Tenant'")
		run("keystone user-create --name demo --tenant demo --pass demo --email demo@inspur.com")
		run("keystone tenant-create --name service --description 'Service Tenant'")
		put(LOCAL_ADMIN_OPENRC, ADMIN_OPENRC)
		put(LOCAL_DEMO_OPENRC, DEMO_OPENRC)

# -----------------------
# 8. keystone info in keystone
# -----------------------
@roles('controller')
def _keystone_in_keystone():
	with shell_env(OS_SERVICE_TOKEN='admin', OS_SERVICE_ENDPOINT="http://controller:35357/v2.0"):
		run("keystone service-create --name keystone --type identity --description 'OpenStack Identity'")
		run("keystone endpoint-create \
			--service-id $(keystone service-list | awk '/ identity / {print $2}') \
			--publicurl http://controller:5000/v2.0 \
			--internalurl http://controller:5000/v2.0 \
			--adminurl http://controller:35357/v2.0 \
			--region regionOne")

# -----------------------
# 9. install glance on controller
# -----------------------
@roles('controller')
def _setup_glance():
	run("openstack-db --drop --service glance --rootpw root")
	run("openstack-db --init --service glance --rootpw root")
	with shell_env(	OS_TENANT_NAME="admin",
			OS_USERNAME="admin", 
			OS_PASSWORD="admin",
			OS_AUTH_URL="http://controller:35357/v2.0"):
		run("keystone user-create --name glance --pass glance")
		run("keystone user-role-add --user glance --tenant service --role admin")
		run("keystone service-create --name glance --type image --description 'OpenStack Image Service'")
		run("keystone endpoint-create \
			--service-id $(keystone service-list | awk '/ image / {print $2}') \
			--publicurl http://controller:9292 \
			--internalurl http://controller:9292 \
			--adminurl http://controller:9292 \
			--region regionOne")
	
	run("yum install -y openstack-glance python-glanceclient")
	put(LOCAL_GLANCE_API_CONF, GLANCE_API_CONF)
	put(LOCAL_GLANCE_REGISTRY_CONF, GLANCE_REGISTRY_CONF)
	run("su -s /bin/sh -c 'glance-manage db_sync' glance")
	run("systemctl enable openstack-glance-api.service openstack-glance-registry.service")
	run("systemctl restart openstack-glance-api.service openstack-glance-registry.service")
	run("systemctl status openstack-glance-api.service openstack-glance-registry.service")
	

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
#	execute(_setup_database)
#	execute(_setup_rabbitmq)
	execute(_setup_keystone)
	execute(_basic_in_keystone)
	execute(_keystone_in_keystone)
	execute(_setup_glance)

