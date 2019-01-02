##############################################################################################
#       Description : This script is to create volumes, qtree's & lun on Netapp Cluster      #
#       Author :   Devender Singh, dev.singh@orange.com                                      #
################### Warning ##################################################################
#               Before running below commands,Please install licenses,                       #
#               check OS version, system configuration etc.                                  #
#     Required Files with this main file: bootlun.csv, bootlun.csv,svmvols.txt,infravols.txt #
##############################################################################################
# Modules Required
import os
import csv
import itertools
#Getting details from file "test.csv"
#
#Static Variables
host='ssh admin@192.168.10.1'
with open('bootlun.csv') as fo:    # Fetching variables from CSV file
      data=csv.DictReader(fo)
      for record in data:
# Dynamic Variables
            cluster=record['cluster']
            nodes=[record['cluster']+'-01',record['cluster']+'-02']
            svmname=record['svmname']
            svmrootvol=record['rootvol']
            svmaggr=record['svmaggr']
            nfsesxip=record['nfsesxip']
            nfsnet=record['esxsubnet']
            nfsesxmask=record['netmask']
            gateway=record['gw']
            iscsiips=[record['iscsiip1'],record['iscsiip2']]
            inetmask=record['iscsinetmask']
            nfs_vlan=record['nfsvlan']
            esx_vlan=record['esxvlan']
            ipspace=record['ipspace']
#            vol=[record['svvol1'],record['svvol2'],record['svvol3'],record['svvol4'],record['svvol5'],record['svvol6'],record['svvol7']]
            
# Please validate All details you Provided
print('Please verify Your Details:\n')
print(host,cluster,nodes,svmname,svmrootvol,svmaggr,nfsesxip,nfsnet,gateway,iscsiips,inetmask,nfs_vlan,esx_vlan,ipspace)
print('\n')
response = input('Do you want to Proceed with above details (y/n):')
if (response != 'y'):
    print('Provided Details are not correct, Please Try Again:')
else:
# creating SVM
    print('%s vserver create -vserver %s -aggregate %s -rootvolume %s -subtype default -ipspace %s -rootvolume-security-style unix -language C.UTF-8 -ns-switch file -nm-switch file -snapshot-policy default -is-repository false'
          %(host,svmname,svmaggr,svmrootvol,ipspace))
    print('%s vserver modify -vserver %s -allowed-protocols nfs,iscsi' %(host,svmname))
    print('%s server status')
    print('%s vol modify -vserver %s -volume %s -snapshot-policy default'%(host,svmname,svmrootvol))
    print('%s snapshot autodelete modify -volume %s -vserver %s -defer-delete none -target-free-space 15 -enabled true'%(host,svmrootvol,svmname,))
    print('%s vserver export-policy create -policyname export_policy_01'%(host))
    print('%s vserver export-policy create -policyname export_policy_02'%(host))
   
# Export Policy
    print('%s vserver export-policy rule create -vserver %s -policyname export_policy_01 -ruleindex 1 -protocol any -clientmatch %s/27" -rorule sys -rwrule none -superuser sys'%(host,svmname,nfsnet))
    print('%s vserver export-policy rule create -vserver %s -policyname export_policy_02 -ruleindex 2 -protocol any -clientmatch %s/27" -rorule sys -rwrule sys -superuser sys'%(host,svmname,nfsnet))
    print('%s vserver nfs create -vserver %s -access true'%(host,svmname))
#
    with open ('svmvols.txt', 'rt') as svmvols:
          for v in svmvols:
                print('%s vol create -volume %s -aggregate %s -size 700GB -state online -type RW -junction-path /%s -vserver %s -space-guarantee none -snapshot-policy none -comment "ESX Boost on SCSI"'
                      %(host,v,svmaggr,v,svmname))
                print('%s sis on -vserver %s -volume %s'%(host,svmname,v))
                print('%s snapshot autodelete modify -volume %s -vserver %s -defer-delete none -target-free-space 15 -enabled true'%(host,v,svmname))

# Creating data interface
    print('%s network interface create -vserver %s -lif lif_file_%s_01 -home-node %s -home-port a0a-%s -failover-group bcast_vlan-%s -data-protocol nfs -role data -firewall-policy data -address %s -netmask %s -status-admin up'
          %(host,svmname,nfs_vlan,nodes[0],nfs_vlan,nfs_vlan,nfsesxip,nfsesxmask))
    print('%s network interface create -vserver %s -lif lif_file_%s_01 -home-node %s -home-port a0a-%s -data-protocol iscsi -role data -firewall-policy data  -address %s -netmask %s -status-admin up'
          %(host,svmname,esx_vlan,nodes[0],esx_vlan,iscsiips[0],inetmask))
    print('%s network interface create -vserver %s -lif lif_file_%s_02 -home-node %s -home-port a0a-%s -data-protocol iscsi -role data -firewall-policy data  -address %s -netmask %s -status-admin up'
          %(host,svmname,esx_vlan,nodes[1],esx_vlan,iscsiips[1],inetmask))
#
# Note: verify size of volumes as per LLD
    with open ('svminfravols.txt', 'rt') as svminfravols:
          for svmvolinfra in svminfravols:
                print('%s vol create -volume %s -aggregate %s -size 2tb -state online -type RW -junction-path /%s -vserver $svm -snapshot-policy none -policy export_policy_01 -comment "Infra datastore Tier1-OBSVM"'
                      %(host,svmvolinfra,svmaggr,svmvolinfra))
                print('%s snapshot autodelete modify -volume %s -vserver %s -defer-delete none -target-free-space 15 -enabled true'
                      %(host,svmvolinfra,svmname))
                print('%s sis on -vserver %s -volume %s'%(host,svmname,svmvolinfra))
#          for qtrevol in svminfravols:
                print('%s qtree create -vserver %s -volume %s -qtree qt01 -security-style unix -export-policy export_policy_02'
                      %(host,svmname,svmvolinfra))
#          for qtrevol1 in svminfravols:
                print('%s vol modify -volume %s -policy export_policy_01'%(host,svmvolinfra))
                print('%s qtree modify -vserver %s -volume %s -qtree qt01 -export-policy  export_policy_02'%(host,svmname,svmvolinfra))
                print('%s vol modify -vserver %s -volume %s -policy export_policy_01'%(host,svmname,svmrootvol))
   # Qtree Creation & Export Policy
    with open ('svmvols.txt', 'rt') as svmvols:
          for qtrevol1 in svmvols:
            print('%s qtree create -vserver %s -volume %s -qtree qt01 -security-style unix'%(host,svmname,qtrevol1))
# Lun Creation
            print('%s lun create -vserver %s -path /vol/%s/qt01/lun01.lun -size 16G -ostype vmware'%(host,svmname,qtrevol1))
            print('%s lun modify -vserver %s -path /vol/%s/qt01/lun01.lun -space-reserve disabled'%(host,svmname,qtrevol1))
#
    print('%s iscsi create -target-alias %s -status-admin up'%(host,svmname))
