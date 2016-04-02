#!/usr/bin/env python
# encoding: utf-8

LOCAL_NTP_CONFIG = "./ntp.conf"
NTP_CONFIG = "/etc/ntp.conf"

LOCAL_MY_CONF = "./my.cnf"
MY_CONF = "/etc/my.cnf"
MYSQL_PW = "root"

EX_BR_INT = "eno2"

CINDER_LVM_DISK = "/dev/sdb"

LOCAL_OPENSTACK_DB = "./scripts/openstack-db"
OPENSTACK_DB = "/usr/local/bin/openstack-db"
LOCAL_ADMIN_OPENRC= "./scripts/admin-openrc.sh"
ADMIN_OPENRC = "/root/admin-openrc.sh"
LOCAL_DEMO_OPENRC= "./scripts/demo-openrc.sh"
DEMO_OPENRC = "/root/demo-openrc.sh"

LOCAL_KEYSTONE_CONF = "./keystone.conf"
KEYSTONE_CONF = "/etc/keystone/keystone.conf"

LOCAL_GLANCE_API_CONF = "./glance/glance-api.conf" 
GLANCE_API_CONF = "/etc/glance/glance-api.conf"
LOCAL_GLANCE_REGISTRY_CONF = "./glance/glance-registry.conf"
GLANCE_REGISTRY_CONF = "/etc/glance/glance-registry.conf"

LOCAL_NOVA_CONTROLLER_CONF = "./nova/nova-controller.conf"
NOVA_CONTROLLER_CONF = "/etc/nova/nova.conf"

LOCAL_NOVA_COMPUTE_CONF = "./nova/nova-compute.conf"
NOVA_COMPUTE_CONF = "/etc/nova/nova.conf"

LOCAL_NEUTRON_CONTROLLER_CONF = "./neutron-controller/neutron.conf"
NEUTRON_CONTROLLER_CONF = "/etc/neutron/neutron.conf"
LOCAL_NEUTRON_ML2_CONTROLLER_CONF = "./neutron-controller/ml2_conf.ini"
NEUTRON_ML2_CONTROLLER_CONF = "/etc/neutron/plugins/ml2/ml2_conf.ini"
LOCAL_NOVA_NEUTRON_UPDATE_CONTROLLER_CONF = "./neutron-controller/nova-controller.conf"
NOVA_NEUTRON_UPDATE_CONTROLLER_CONF = "/etc/nova/nova.conf"

LOCAL_SYSCTL_NETWORK_CONF = "./neutron-network/sysctl.conf"
SYSCTL_NETWORK_CONF = "/etc/sysctl.conf"
LOCAL_NEUTRON_NETWORK_CONF = "./neutron-network/neutron.conf"
NEUTRON_NETWORK_CONF = "/etc/neutron/neutron.conf"
LOCAL_NEUTRON_L3_NETWORK_CONF = "./neutron-network/l3_agent.ini"
NEUTRON_NETWORK_L3_CONF = "/etc/neutron/l3_agent.ini"
LOCAL_NEUTRON_DHCP_NETWORK_CONF = "./neutron-network/dhcp_agent.ini"
NEUTRON_NETWORK_DHCP_CONF = "/etc/neutron/dhcp_agent.ini"
LOCAL_NEUTRON_METADATA_NETWORK_CONF = "./neutron-network/metadata_agent.ini"
NEUTRON_NETWORK_METADATA_CONF = "/etc/neutron/metadata_agent.ini"
LOCAL_NEUTRON_ML2_NETWORK_CONF = "./neutron-network/ml2_conf.ini"
NEUTRON_ML2_NETWORK_CONF = "/etc/neutron/plugins/ml2/ml2_conf.ini"

LOCAL_SYSCTL_COMPUTE_CONF = "./neutron-compute/sysctl.conf"
SYSCTL_COMPUTE_CONF = "/etc/sysctl.conf"
LOCAL_NEUTRON_COMPUTE_CONF = "./neutron-compute/neutron.conf"
NEUTRON_COMPUTE_CONF = "/etc/neutron/neutron.conf"
LOCAL_NEUTRON_ML2_COMPUTE_CONF = "./neutron-compute/ml2_conf.ini"
NEUTRON_ML2_COMPUTE_CONF = "/etc/neutron/plugins/ml2/ml2_conf.ini"
LOCAL_NOVA_NEUTRON_UPDATE_COMPUTE_CONF = "./neutron-compute/nova.conf"
NOVA_NEUTRON_UPDATE_COMPUTE_CONF = "/etc/nova/nova.conf"

LOCAL_CINDER_CONTROLLER_CONF = "./cinder-controller/cinder.conf"
CINDER_CONTROLLER_CONF = "/etc/cinder/cinder.conf"

LOCAL_CINDER_BLOCK_CONF = "./cinder-block/cinder.conf"
CINDER_BLOCK_CONF = "/etc/cinder/cinder.conf"

LOCAL_HORIZON_CONF = "./horizon/local_settings"
HORIZON_CONF = "/etc/openstack-dashboard/local_settings"

AUTH_KEYS = "./authorized_keys"
HOST_LIST = "/etc/hosts"

LOCAL_CENTOS7_REPO = "./repos/centos7.repo"
CENTOS7_REPO = "/etc/yum.repos.d/CentOS-Base.repo"
LOCAL_EPEL7_REPO = "./repos/epel7.repo"
EPEL7_REPO = "/etc/yum.repos.d/epel.repo"

LOCAL_OPENSTACK_REPO = "./repos/openstack.repo"
OPENSTACK_REPO = "/etc/yum.repos.d/rdo-release.repo"
