#!/bin/bash

# Скрипт для сбора информации по установленным пакетам виртуализации на управляющей ВМ HostedEngine и гипервизорах в среде виртуализации "Ред Виртуализация". 
# Дополнительно с гипервизоров собирается информация по аппаратной конфигурации.
# Скрипт запускается из управляющей ВМ HostedEngine.
# Разработчик: Раздобаров Евгений

OUTPUT_FILE="virt_infra.info"

# Функция сбора данных с локальной ВМ Engine
collect_local_vm_data() {
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo "| HostedEngine VM                                                                        " | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| Hostname                   | " | tee -a $OUTPUT_FILE
    hostname | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| OS Description             | " | tee -a $OUTPUT_FILE
    cat /etc/os-release | grep PRETTY_NAME | cut -c 14- | sed 's/.\{1\}$//' | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| Kernel Version             | " | tee -a $OUTPUT_FILE
    uname -r | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| Ovirt-Engine version       | " | tee -a $OUTPUT_FILE
    rpm -qa 2>/dev/null | grep '^ovirt-engine-[0-9]' | cut -c 14- | sed 's/.\{7\}$//' | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| Ovirt-Engine status        | " | tee -a $OUTPUT_FILE
    systemctl is-active ovirt-engine | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| RAM                        | " | tee -a $OUTPUT_FILE
    dmidecode -t memory | grep Size | awk -F " " '{print $2}' | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| CPU                        | " | tee -a $OUTPUT_FILE
    cat /proc/cpuinfo | grep processor | wc -l | tee -a $OUTPUT_FILE
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
    echo -n "| Certs validirty            | " | tee -a $OUTPUT_FILE
    openssl x509 -text -noout -in /etc/pki/ovirt-engine/ca.pem | grep -A2 Validity | tee -a $OUTPUT_FILE | tail -1 | cut -c 13-
    echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE

}

# Функция сбора дянных с гипервизора
collect_hypervisor_data() {
    local host_name=$1
    if ping -c 3 "$host" &> /dev/null; then
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo "| Host: $host_name                                                                       " | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Hostname                   | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "hostname" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| OS Description             | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "cat /etc/os-release | grep PRETTY_NAME | cut -c 14- | sed 's/.\{1\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Cert valid till            | " | tee -a $OUTPUT_FILE
        openssl x509 -text -noout -in /etc/pki/ovirt-engine/certs/$host_name.cer | grep "Not After" | awk -F " : " '{print $2}' | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Kernel version             | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "uname -r" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE 
        echo -n "| KVM version                | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep kvm-core | cut -c 15- | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE 
        echo -n "| Libvirt version            | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep libvirt-daemon-kvm | cut -c 20- | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| VDSM version               | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep vdsm-common | cut -c 13- | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
	echo -n "| VDSM service status        | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "systemctl is-active vdsmd" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Spice version              | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep spice- | cut -c 14- | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| GlusterFS version          | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep 'glusterfs-[0-9]' | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| CEPH version               | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep librbd | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Open vSwitch version       | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep '^openvswitch-[0-9]' | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
 	echo -n "| Nmstate version            | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "rpm -qa | grep '^nmstate-[0-9]' | sed 's/.\{7\}$//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| RAM installed total (GB)   | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "dmidecode -t 17 | grep 'Size' | grep -v ' Size' | grep -v 'No Module Installed' | cut -d ' ' -f 2" > outhostmem.txt; awk '{ sum+=$1 } END {print sum }' outhostmem.txt | tee -a $OUTPUT_FILE; rm -f outhostmem.txt
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Logical CPU total          | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "cat /proc/cpuinfo | grep processor | wc -l" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
	echo -n "| Physical CPU sockets       | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "cat /proc/cpuinfo | grep 'physical id' | sort -u | wc -l" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| CPU model                  | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "cat /proc/cpuinfo | grep 'model name' | sort -u | cut -d ':' -f 2 | sed 's/^\ *//'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        echo -n "| Server manufacturer        | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "dmidecode --type 1 | grep Manufacturer | cut -d ' ' -f 2" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
	echo -n "| Eth NICs total             | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "ls -al /sys/class/net/ | grep -e 'ens' -e 'eno' | rev | cut -d '/' -f 1 | rev | wc -l" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
	HOSTNET_ARR=($(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name  "ls -al /sys/class/net/ | grep -e 'ens' -e 'eno' | rev | cut -d '/' -f 1 | rev"))
        for i in "${HOSTNET_ARR[@]}"; do
            echo -n "|                            | " | tee -a $OUTPUT_FILE
	    echo $i', speed: '$(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "cat /sys/class/net/$i/speed") 'Mbits, Status: '$(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "cat /sys/class/net/$i/operstate") | tee -a $OUTPUT_FILE
            echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
        done
        #rm -f hostnet
	SD_DISKS_ARR=($(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "hdparm -I /dev/sd[a-z] 2>/dev/null | grep  -B 4 -A 25 'Model Number' | grep 'sd[a-z]' | sed 's/\/dev\///g' | sed  's/://g'"))
	NVME_DISKS_ARR=($(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "lsblk | cut -d ' ' -f 1 | grep -P 'nvme[0-9]n[0-9]$'"))
        if [[ -n "${SD_DISKS_ARR}" ]]; then
            echo -n "| Local Disks total          | " | tee -a $OUTPUT_FILE
            ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "hdparm -I /dev/sd[a-z] 2>/dev/null | grep  -B 4 -A 25 'Model Number' | grep 'sd[a-z]' | sed 's/\/dev\///g' | sed  's/://g' | wc -l" | tee -a $OUTPUT_FILE
            echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
            for i in "${SD_DISKS_ARR[@]}"; do
                disk_size=$(($(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "hdparm -I /dev/$i | grep 'device size with M = 1000\*1000' | cut -d ':' -f 2 | sed 's/^[[:blank:]]*//' | cut -d ' ' -f 1") / 1000))
                echo -n "|                            | " | tee -a $OUTPUT_FILE
                echo $i', Size: '$disk_size' GB, Model: '$(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "hdparm -I /dev/$i | grep 'Model Number' | cut -d ':' -f 2| sed 's/^[[:blank:]]*//'") | tee -a $OUTPUT_FILE
	    	echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
            done
        fi
	if [[ -n "${NVME_DISKS_ARR}" ]]; then
            echo -n "| Local NVME Disks total     | " | tee -a $OUTPUT_FILE
            ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "lsblk | cut -d ' ' -f 1 | grep -P 'nvme[0-9]n[0-9]$' | wc -l" | tee -a $OUTPUT_FILE
            echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
            for i in "${NVME_DISKS_ARR[@]}"; do
                disk_size=$(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "smartctl --all /dev/$i  2>/dev/null | grep 'Total NVM Capacity' | cut -d '[' -f2 | cut -d ' ' -f 1")
                echo -n "|                            | " | tee -a $OUTPUT_FILE
                echo $i', Size: '$disk_size' GB, Model: '$(ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "smartctl --all /dev/$i  2>/dev/null | grep 'Model Number' | cut -d ':' -f 2 | sed 's/^[[:blank:]]*//'") | tee -a $OUTPUT_FILE
                echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
            done
        fi
	echo -n "| VM running total           | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "virsh -r list --all | tail -n +4 | wc -l" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
	echo -n "| Certs validity             | " | tee -a $OUTPUT_FILE
        ssh -q -i /etc/pki/ovirt-engine/keys/engine_id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ConnectionAttempts=1 root@$host_name "echo '$(openssl x509 -text -noout -in /etc/pki/ovirt-engine/certs/$host_name.cer | grep -A2 Validity | tail -1 | cut -c 13-)'" | tee -a $OUTPUT_FILE
        echo "-----------------------------------------------------------------------------------------" | tee -a $OUTPUT_FILE
     else
        echo "Гипервизор $host не доступен" | tee -a $OUTPUT_FILE
    fi
}

# Удаляем старый файл с данными, если существует
[[ -f vm_infra.info ]] && rm -f vm_infra.info

# Собираем даннные с локальной ВМ Engine
collect_local_vm_data

# Получаем информацию о доступных гипервизорах
if [ -d /etc/pki/ovirt-engine/certs ]; then
    CHK_HOSTS="$(ls /etc/pki/ovirt-engine/certs/ | grep -E "*ssh.cer$" | grep -v $(hostname) > /dev/null 2>&1; echo $?)"
    if [ ${CHK_HOSTS} == "0" ]; then
        # Создаем массив с именами гипервизоров
        HOSTS_ARR=($(ls /etc/pki/ovirt-engine/certs/ | grep -E "*ssh.cer$" | grep -v $(hostname) | sed 's/.\{8\}$//'))

        # Собираем данные с гипервизоров
        for host in "${HOSTS_ARR[@]}"; do
            collect_hypervisor_data $host
        done
    fi
fi