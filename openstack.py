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

def get_ipaddr(hostname):
	with open("/etc/hosts", "r") as f:
		for line in f:
			line = line.strip()
			if len(line.split()) == 0: continue
			if line[0] == '#': continue
			ipaddr = line.split()[0]
			host = line.split()[1]
			if host == hostname:
				return ipaddr
		raise Exception("Unknown host")


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

# -----------------------
# 10. install nova on controller
# -----------------------
@roles('controller')
def _setup_nova_controller():
	run("openstack-db --drop --service nova --rootpw root")
	run("openstack-db --init --service nova --rootpw root")
	with shell_env(	OS_TENANT_NAME="admin",
			OS_USERNAME="admin", 
			OS_PASSWORD="admin",
			OS_AUTH_URL="http://controller:35357/v2.0"):
		run("keystone user-create --name nova --pass nova")
		run("keystone user-role-add --user nova --tenant service --role admin")
		run("keystone service-create --name nova --type compute --description 'OpenStack Compute'")

		run("keystone endpoint-create \
			--service-id $(keystone service-list | awk '/ compute / {print $2}') \
			--publicurl http://controller:8774/v2/%\(tenant_id\)s \
			--internalurl http://controller:8774/v2/%\(tenant_id\)s \
			--adminurl http://controller:8774/v2/%\(tenant_id\)s \
			--region regionOne")
	
	run("yum install -y openstack-nova-api openstack-nova-cert openstack-nova-conductor \
		openstack-nova-console openstack-nova-novncproxy openstack-nova-scheduler \
		python-novaclient")
	put(LOCAL_NOVA_CONTROLLER_CONF, NOVA_CONTROLLER_CONF)
	run("su -s /bin/sh -c 'nova-manage db sync' nova")
	run("# systemctl enable openstack-nova-api.service openstack-nova-cert.service \
		openstack-nova-consoleauth.service openstack-nova-scheduler.service \
		openstack-nova-conductor.service openstack-nova-novncproxy.service")
	run("systemctl restart openstack-nova-api.service openstack-nova-cert.service \
		openstack-nova-consoleauth.service openstack-nova-scheduler.service \
		openstack-nova-conductor.service openstack-nova-novncproxy.service")
	run("systemctl status openstack-nova-api.service openstack-nova-cert.service \
		openstack-nova-consoleauth.service openstack-nova-scheduler.service \
		openstack-nova-conductor.service openstack-nova-novncproxy.service")

# -----------------------
# 11. install nova on compute
# -----------------------
@roles('compute')
@parallel
def _setup_nova_compute():
	run("yum install -y openstack-nova-compute sysfsutils")
	put(LOCAL_NOVA_COMPUTE_CONF, NOVA_COMPUTE_CONF)
	ipaddr = get_ipaddr(env.host)
	run("sed -i 's/%MANAGEMENT_INTERFACE_IP_ADDRESS%/" + ipaddr + "/g' " + NOVA_COMPUTE_CONF)
	run("systemctl enable libvirtd.service openstack-nova-compute.service")
	run("systemctl restart libvirtd.service openstack-nova-compute.service")
	run("systemctl status libvirtd.service openstack-nova-compute.service")
	
# -----------------------
# 12. check nova services
# -----------------------
@roles('controller')
def _check_nova_services():
	with shell_env(	OS_TENANT_NAME="admin",
			OS_USERNAME="admin", 
			OS_PASSWORD="admin",
			OS_AUTH_URL="http://controller:35357/v2.0"):
		run("nova service-list")

# -----------------------
# 13. install neutron on controller
# -----------------------
@roles('controller')
def _setup_neutron_controller():
	run("openstack-db --drop --service neutron --rootpw root")
	run("openstack-db --init --service neutron --rootpw root")
	with shell_env(	OS_TENANT_NAME="admin",
			OS_USERNAME="admin", 
			OS_PASSWORD="admin",
			OS_AUTH_URL="http://controller:35357/v2.0"):
		run("keystone user-create --name neutron --pass neutron")
		run("keystone user-role-add --user neutron --tenant service --role admin")
		run("keystone service-create --name neutron --type network --description 'OpenStack Networking'")
		run("keystone endpoint-create \
			--service-id $(keystone service-list | awk '/ network / {print $2}') \
			--publicurl http://controller:9696 \
			--adminurl http://controller:9696 \
			--internalurl http://controller:9696 \
			--region regionOne")

	run("yum install -y openstack-neutron openstack-neutron-ml2 python-neutronclient which")
	put(LOCAL_NEUTRON_CONTROLLER_CONF, NEUTRON_CONTROLLER_CONF)
	put(LOCAL_NEUTRON_ML2_CONTROLLER_CONF, NEUTRON_ML2_CONTROLLER_CONF)

	with shell_env(	OS_TENANT_NAME="admin",
			OS_USERNAME="admin", 
			OS_PASSWORD="admin",
			OS_AUTH_URL="http://controller:35357/v2.0"):
		service_tenant_id = run("keystone tenant-get service | grep id |awk '{print $4}'").strip()
		if len(service_tenant_id) != 32:
			raise Exception("Unknown Tenant")
		run("sed -i 's/%SERVICE_TENANT_ID%/" + service_tenant_id + "/g' " + NEUTRON_ML2_CONTROLLER_CONF)
	run("rm -f /etc/neutron/plugin.ini")
	run("ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini")
	put(LOCAL_NOVA_NEUTRON_UPDATE_CONTROLLER_CONF, NOVA_NEUTRON_UPDATE_CONTROLLER_CONF)

	run("su -s /bin/sh -c 'neutron-db-manage --config-file /etc/neutron/neutron.conf \
		--config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade juno' neutron")
	run("systemctl restart openstack-nova-api.service openstack-nova-scheduler.service \
		openstack-nova-conductor.service")
	run("systemctl status openstack-nova-api.service openstack-nova-scheduler.service \
		openstack-nova-conductor.service")
	run("systemctl enable neutron-server.service")
	run("systemctl restart neutron-server.service")
	run("systemctl status neutron-server.service")

# -----------------------
# 14. install neutron on network
# -----------------------
@roles('network')
def _setup_neutron_network():
	put(LOCAL_SYSCTL_NETWORK_CONF, SYSCTL_NETWORK_CONF)
	run("sysctl -p")
	run("yum install -y openstack-neutron openstack-neutron-ml2 openstack-neutron-openvswitch")
	put(LOCAL_NEUTRON_NETWORK_CONF, NEUTRON_NETWORK_CONF)
	put(LOCAL_NEUTRON_L3_NETWORK_CONF, NEUTRON_NETWORK_L3_CONF)
	put(LOCAL_NEUTRON_DHCP_NETWORK_CONF, NEUTRON_NETWORK_DHCP_CONF)
	put(LOCAL_NEUTRON_METADATA_NETWORK_CONF, NEUTRON_NETWORK_METADATA_CONF)
	put(LOCAL_NEUTRON_ML2_NETWORK_CONF, NEUTRON_ML2_NETWORK_CONF)
	tunnel_ip = run("ip addr show " + EX_BR_INT + " | sed -n '3,3p' | awk '{print $2}' | awk -F'/' '{print $1}'")
	run("sed -i 's/%TUNNELS_INTERFACE_IPADDR%/" + tunnel_ip + "/g' " + NEUTRON_ML2_NETWORK_CONF)
	run("systemctl enable openvswitch.service")
	run("systemctl restart openvswitch.service")
	run("systemctl status openvswitch.service")
	run("ovs-vsctl --if-exists del-br br-ex")
	run("ovs-vsctl add-br br-ex")
	run("ovs-vsctl add-port br-ex " + EX_BR_INT)
	run("rm -f /etc/neutron/plugin.ini")
	run("ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini")
	run("cp /usr/lib/systemd/system/neutron-openvswitch-agent.service \
		/usr/lib/systemd/system/neutron-openvswitch-agent.service.orig")
	run("sed -i 's,plugins/openvswitch/ovs_neutron_plugin.ini,plugin.ini,g' \
		/usr/lib/systemd/system/neutron-openvswitch-agent.service")
	run("systemctl enable neutron-openvswitch-agent.service neutron-l3-agent.service \
		neutron-dhcp-agent.service neutron-metadata-agent.service \
		neutron-ovs-cleanup.service")
	run("systemctl restart neutron-openvswitch-agent.service neutron-l3-agent.service \
		neutron-dhcp-agent.service neutron-metadata-agent.service")
	run("systemctl status neutron-openvswitch-agent.service neutron-l3-agent.service \
		neutron-dhcp-agent.service neutron-metadata-agent.service")

# -----------------------
# 15. install neutron on compute
# -----------------------
@roles('compute')
@parallel
def _setup_neutron_compute():
	put(LOCAL_SYSCTL_COMPUTE_CONF, SYSCTL_COMPUTE_CONF)
	run("sysctl -p")
	run("yum install -y openstack-neutron-ml2 openstack-neutron-openvswitch")
	put(LOCAL_NEUTRON_COMPUTE_CONF, NEUTRON_COMPUTE_CONF)
	put(LOCAL_NEUTRON_ML2_COMPUTE_CONF, NEUTRON_ML2_COMPUTE_CONF)
	tunnel_ip = run("ip addr show " + EX_BR_INT + " | sed -n '3,3p' | awk '{print $2}' | awk -F'/' '{print $1}'")
	run("sed -i 's/%TUNNELS_INTERFACE_IPADDR%/" + tunnel_ip + "/g' " + NEUTRON_ML2_COMPUTE_CONF)
	run("systemctl enable openvswitch.service")
	run("systemctl restart openvswitch.service")
	run("systemctl status openvswitch.service")
	put(LOCAL_NOVA_NEUTRON_UPDATE_COMPUTE_CONF, NOVA_NEUTRON_UPDATE_COMPUTE_CONF)
	run("rm -f /etc/neutron/plugin.ini")
	run("ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini")
	run("cp /usr/lib/systemd/system/neutron-openvswitch-agent.service \
		/usr/lib/systemd/system/neutron-openvswitch-agent.service.orig")
	run("sed -i 's,plugins/openvswitch/ovs_neutron_plugin.ini,plugin.ini,g' \
		/usr/lib/systemd/system/neutron-openvswitch-agent.service")
	run("systemctl restart openstack-nova-compute.service")
	run("systemctl status openstack-nova-compute.service")
	run("systemctl enable neutron-openvswitch-agent.service")
	run("systemctl restart neutron-openvswitch-agent.service")
	run("systemctl status neutron-openvswitch-agent.service")
	
# -----------------------
# 16. install horizon on controller
# -----------------------
@roles('controller')
def _setup_horizon():
	run("yum install -y openstack-dashboard httpd mod_wsgi memcached python-memcached")
	put(LOCAL_HORIZON_CONF, HORIZON_CONF)
	#run("setsebool -P httpd_can_network_connect on")
	run("chown -R apache:apache /usr/share/openstack-dashboard/static")
	run("systemctl enable httpd.service memcached.service")
	run("systemctl restart httpd.service memcached.service")
	run("systemctl status httpd.service memcached.service")


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
#	execute(_setup_keystone)
#	execute(_basic_in_keystone)
#	execute(_keystone_in_keystone)
#	execute(_setup_glance)
#	execute(_setup_nova_controller)
#	execute(_setup_nova_compute)
#	execute(_check_nova_services)
#	execute(_setup_neutron_controller)
#	execute(_setup_neutron_network)
#	execute(_setup_neutron_compute)
	execute(_setup_horizon)

