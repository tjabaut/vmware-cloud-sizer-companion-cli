#!/usr/bin/env python3
import json
import pandas as pd
from pandas import json_normalize


def data_describe(vm_data):
    vm_data_df = pd.DataFrame(vm_data)
    print(f'\n{vm_data_df}')
    print(f'\nTotal VM: {vm_data_df.vmName.count()}')
    print(f'\nTotal Clusters: {vm_data_df.cluster.nunique()}')
    print(f'\nTotal vCPU: {vm_data_df.vCpu.sum()}')
    print(f'\nTotal vRAM: {vm_data_df.vRam.sum()}')
    print(f'\nTotal used VMDK: {vm_data_df.vmdkUsed.sum()}')
    print(f'\nTotal provisioned VMDK: {vm_data_df.vmdkTotal.sum()}')
    print(f'\n{vm_data_df.describe()}')

def lova_conversion(**kwargs):
    input_path = kwargs['input_path']
    file_name = kwargs['file_name'] 

    vmdata_df = pd.read_excel(f'{input_path}{file_name}', sheet_name="VMs")

    # specify columns to KEEP - all others will be dropped
    vmdata_df.drop(vmdata_df.columns.difference([
        'Cluster','Datacenter','Guest IP1','Guest IP2','Guest IP3','Guest IP4','VM OS',
        'Guest Hostname', 'IsRunning', 'Virtual CPU', 'VM Name', 'Virtual Disk Size (MB)',
        'Virtual Disk Used (MB)', 'Provisioned Memory (MB)', 'Consumed Memory (MB)', 'MOB ID'
        ]), axis=1, inplace=True)

    # rename remaining columns
    vmdata_df.rename(columns = {
        'MOB ID':'vmId',
        'VM Name':'vmName',
        'VM OS':'os',
        'Guest Hostname':'os_name',
        'IsRunning':'vmState',
        'Virtual CPU':'vCpu',
        'Provisioned Memory (MB)':'vRam',
        'Virtual Disk Size (MB)':'vmdkTotal',
        'Virtual Disk Used (MB)':'vmdkUsed',
        'Cluster':'cluster',
        'Datacenter':'virtualDatacenter'
        }, inplace = True)

    # aggregate IP addresses into one column
    vmdata_df["Guest IP1"].fillna("no ip", inplace = True)
    vmdata_df["Guest IP2"].fillna("no ip", inplace = True)
    vmdata_df["Guest IP3"].fillna("no ip", inplace = True)
    vmdata_df["Guest IP4"].fillna("no ip", inplace = True)
    vmdata_df['ip_addresses'] = vmdata_df['Guest IP1'].map(str)+ ', ' + vmdata_df['Guest IP2'].map(str)+ ', ' + vmdata_df['Guest IP3'].map(str)+ ', ' + vmdata_df['Guest IP4'].map(str)
    vmdata_df['ip_addresses'] = vmdata_df.ip_addresses.str.replace(', no ip' , '')
    vmdata_df.drop(['Guest IP1', 'Guest IP2', 'Guest IP3', 'Guest IP4'], axis=1, inplace=True)

    # convert RAM and storage numbers into GB
    vmdata_df['vmdkUsed'] = vmdata_df['vmdkUsed']/1024
    vmdata_df['vmdkTotal'] = vmdata_df['vmdkTotal']/1024
    vmdata_df['vRam'] = vmdata_df['vRam']/1024

    return vmdata_df


def rvtools_conversion(**kwargs):
    input_path = kwargs['input_path']
    file_name = kwargs['file_name'] 

    vmdata_df = pd.read_excel(f'{input_path}{file_name}', sheet_name = 'vInfo')

    # specify columns to KEEP - all others will be dropped
    vmdata_df.drop(vmdata_df.columns.difference([
        'VM ID','Cluster', 'Datacenter','Primary IP Address','OS according to the VMware Tools',
        'DNS Name','Powerstate','CPUs','VM','Provisioned MB','In Use MB','Memory', 'Resource pool', 'Folder'
        ]), axis = 1, inplace = True)

    # rename remaining columns
    vmdata_df.rename(columns = {
        'VM ID':'vmId',
        'VM':'vmName',
        'OS according to the VMware Tools':'os',
        'DNS Name':'os_name',
        'Powerstate':'vmState',
        'CPUs':'vCpu',
        'Memory':'vRam', 
        'Provisioned MB':'vmdkTotal',
        'In Use MB':'vmdkUsed',
        'Primary IP Address':'ip_addresses',
        'Folder':'vmFolder',
        'Resource pool':'resourcePool',
        'Cluster':'cluster', 
        'Datacenter':'virtualDatacenter'
        }, inplace = True)

    # convert RAM and storage numbers into GB
    vmdata_df['vmdkUsed'] = vmdata_df['vmdkUsed']/1024
    vmdata_df['vmdkTotal'] = vmdata_df['vmdkTotal']/1024
    vmdata_df['vRam'] = vmdata_df['vRam']/1024

    return vmdata_df


def workload_profiles(**kwargs):
    vm_data_df = kwargs["vm_data"]
    ct = kwargs["ct"]
    # scope = kwargs["scope"]
    # cap = kwargs["cap"]
    # susvm = kwargs["susvm"]
    profile_config = kwargs["profile_config"]

    #create list for storing file names
    file_list = []

    match profile_config:
        case "clusters":
            print("Creating workload profiles by cluster.")
            cluster_profiles = vm_data_df.groupby('cluster')
            # save resulting dataframes as csv files 
            output_path = './output'
            for cluster, cluster_df in cluster_profiles:
                cluster_df.to_csv(f'{output_path}/cluster_{cluster}.csv')
                file_list.append(f'cluster_{cluster}.csv')
    
        case "virtual datacenter":
            print("Creating workload profiles by virtual data center.")
            vdc_profiles = vm_data_df.groupby('virtualDatacenter')
            # save resulting dataframes as csv files 
            output_path = './output'
            for datacenter, datacenter_df in vdc_profiles:
                datacenter_df.to_csv(f'{output_path}/vdc_{datacenter}.csv')
                file_list.append(f'cluster_{datacenter}.csv')

        case "resource pools":
            print("Creating workload profiles by resource pools.")
            rp_profiles = vm_data_df.groupby('resourcePool')
            # save resulting dataframes as csv files 
            output_path = './output'
            for rp, rp_df in rp_profiles:
                rp_df.to_csv(f'{output_path}/rp_{rp}.csv')
                file_list.append(f'cluster_{rp}.csv')

        case "folders":
            print("Creating workload profiles by folders.")
            folder_profiles = vm_data_df.groupby('vmFolder')
            # save resulting dataframes as csv files 
            output_path = './output'
            for folder, folder_df in folder_profiles:
                folder_df.to_csv(f'{output_path}/vmfolder_{folder}.csv')
                file_list.append(f'cluster_{folder}.csv')

    # set configurations for recommendation calculations
    configurations = {
        "cloudType": ct,
        # "sddcHostType": "AUTO",
        "clusterType": "SAZ",
        "computeOvercommitFactor": 4,
        "cpuHeadroom": 0.15,
        "hyperThreadingFactor": 1.25,
        "memoryOvercommitFactor": 1.25,
        "cpuUtilization": 1,
        "memoryUtilization": 1,
        "storageThresholdFactor": 0.8,
        "compressionRatio": 1.25,
        "dedupRatio": 1.5,
        "ioAccessPattern": None,
        "ioSize": None,
        "ioRatio": None,
        "totalIOPs": None,
        "includeManagementVMs": True,
        "fttFtmType": "AUTO_AUTO",
        "separateCluster": None,
        "instanceSettingsList": None,
        "vmOutlierLimits": {
            "cpuLimit": 0.75,
            "storageLimit": 0.5,
            "memoryLimit": 0.75
        },
        "applianceSize": "AUTO",
        "addonsList": []
    }
    
    # build json objects for recommendation payload
    workloadProfiles = []

    # build the sizerRequest payload, using exported files (from above) to populate the workload profiles
    for file in file_list:
        vm_data_df = pd.read_csv(f'./output/{file}')

        # build the profile
        profile = {}
        profile["profileName"] = file
        profile['separateCluster'] = True
        profile["isEnabled"] = True

        vmList = []

        for ind in vm_data_df.index:
            VMInfo = {}
            VMInfo["vmComputeInfo"] = {}
            VMInfo["vmMemoryInfo"] = {}
            VMInfo["vmStorageInfo"] = {}   
            VMInfo["vmId"] = str(vm_data_df['vmId'][ind])
            VMInfo["vmName"] = str(vm_data_df['vmName'][ind])
            VMInfo["vmComputeInfo"]["vCpu"] = int(vm_data_df['vCpu'][ind])
            VMInfo["vmMemoryInfo"]["vRam"] = int(vm_data_df['vRam'][ind])
            VMInfo["vmStorageInfo"]["vmdkTotal"] = int(vm_data_df['vmdkTotal'][ind])
            VMInfo["vmStorageInfo"]["vmdkUsed"] = int(vm_data_df['vmdkUsed'][ind])
            vmList.append(VMInfo)

        profile['vmList'] = vmList
        workloadProfiles.append(profile)

    sizerRequest = {
        "configurations": configurations,
        "workloadProfiles": workloadProfiles
        }

    return json.dumps(sizerRequest)

####################################
# code / functions for later use
####################################

# import parition or performance data 
    # excel_partition_df = pd.read_excel(file_name, sheet_name="VM Disks")
    # excel_partition_df = excel_partition_df.drop(columns=[
    #     'Datacenter', 'Host','InstanceUUID','IsRunning','vCenter'
    #     ])

    # print(excel_partition_df)

    # excel_perfdata_df = pd.read_excel(file_name, sheet_name="VM Performance")
    # excel_perfdata_df = excel_perfdata_df.drop(columns=[
    #     '% of KB/sec', '% of Memory', '% of vCPU', 'Average IOPS', 'Average KB/sec', 'Average vCPU (GHz)', 'Average vCPU %', 'Avg Memory (MB)',
    #     'Avg Memory %', 'Avg Read IOPS', 'Avg Read Latency', 'Avg Read MB/s', 'Avg Write IOPS', 'Avg Write Latency', 'Avg Write MB/s','Datacenter',
    #     'Host','Max KB/sec', 'Peak Latency', 'Peak Memory (MB)', 'Peak Memory %', 'VM IO Classification'
    #     ], axis=1, inplace=True)

    # print(excel_perfdata_df)

    # vmerge = excel_vmdata_df.merge(excel_perfdata_df, left_on='MOB ID', right_on='MOB ID', suffixes=('_left', '_right'))
    # vmerge = excel_vmdata_df.merge(excel_partition_df, left_on='MOB ID', right_on='MOB ID', suffixes=('_left', '_right'))
    # return vmerge