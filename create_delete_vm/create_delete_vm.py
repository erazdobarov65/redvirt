##############################################################################################################################################
# Скрипт для массового создания и удаления виртуальных машин в выбранном кластере
# Запускается из командной строки без аргументов.
# Работает в интерактивном режиме
# !!!Внимание!!!
# Перед использованием скрипта задайте свои значения переменных:
# OVIRT_USER -  пользователь ovirt с админскими правами (на создание ВМ)
# OVIRT_PASS - пароль пользователя
# OVIRT_URL -  адрес API ovirt-engine в виде "https://<hosted-engine>/ovirt-engine/api" где <hosted-engine> - FQDN менеджера виртуализации
# MEMORY_VM - Объем памяти ВМ в виде "<ГБ> * 1024 *1024 *1024". Геде ГБ - объем в ГБ
# VCPU_VM - Количество виртуальных CPU


#import logging
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
#import re, sys, base64, getopt, socket, csv, os,
import time, requests
import re
#from colorama import Fore, Back, Style, init
#from os.path import exists


# Задаем параметры подключения
OVIRT_USER = "admim@internal" #admin
OVIRT_PASS = "password"
OVIRT_URL = "https://engine.redvirt.tst/ovirt-engine/api"


# Функция соединения с Ovirt
def ovirt_connect(OVIRT_URL):
    connection = sdk.Connection(
        url=OVIRT_URL,
        username=OVIRT_USER,
        password=OVIRT_PASS,
        #ca_file=OVIRT_CA,
        # debug=True,
        # log=logging.getLogger(),
        insecure=True,
    )
    return connection


#Функция выбора кластера, в котором будет создана ВМ
def SelectCluster(connection):
    clusters_service = connection.system_service().clusters_service()
    clusters = clusters_service.list()

    cluster_arr = []
    cluster_num = 0
    while True:
        for cluster in clusters:
            cluster_num += 1
            cluster_arr.append(cluster.id)
            print(f"{cluster_num}: {cluster.name}")
        cluster_index = input(f"Введите номер кластера > ")
        try:
            cluster_index = int(cluster_index) - 1
        except ValueError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0
        try:
            CLUSTER_ID = cluster_arr[cluster_index]
            print(CLUSTER_ID)
            return CLUSTER_ID
            break
        except IndexError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0
        except TypeError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0


#Функция выбора шаблона на базе которого будет создана ВМ
def SelectTemplate(connection, CLUSTER_ID):
    templates_service = connection.system_service().templates_service()
    tms = templates_service.list()

    tms_arr = []
    tms_num = 0
    while True:
        for tm in tms:
            try:
                if tm.cluster.id == CLUSTER_ID:
                    tms_num += 1
                    tms_arr.append(tm.id)
                    print(f"{tms_num}: {tm.name}")
            except AttributeError:
                pass
        tmpl_index = input(f"Введите номер шаблона > ")
        try:
            tmpl_index = int(tmpl_index) - 1
        except ValueError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0
        try:
            TMPL_ID = tms_arr[tmpl_index]
            print(TMPL_ID)
            return TMPL_ID
            break
        except IndexError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0
        except TypeError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0

#Функция создания новой ВМ
def CreateVM(connection,NEW_VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    print (f"Создается новая ВМ: {NEW_VM_NAME}")
    vms_service.add(
        types.Vm(
            name=NEW_VM_NAME,
            memory=MEMORY_VM,
            cluster=types.Cluster(id=CLUSTER_ID),
            template=types.Template(id=TMPL_ID),
            memory_policy=types.MemoryPolicy(
                guaranteed=MEMORY_VM,
                max=MEMORY_VM,
            ),
            cpu=types.Cpu(
                topology=types.CpuTopology(
                    sockets=1,
                    cores=VCPU_VM,
                    threads=1
                )
            ),
            os=types.OperatingSystem(
                boot=types.Boot(
                    devices=[types.BootDevice.HD]
                )
            )
        ),
        clone=False #диски тонкие.
    )


#Функция для проверки создалась ли ВМ
def CheckVMAvailable(connection, VM_NAME):
    #check_vm = 0 # Проверка есть ли уже ВМ с таким именем
    
    while True:
        vms_service = connection.system_service().vms_service()
        vms = vms_service.list()
        for vm in vms:
            if vm.name == VM_NAME:
                print (f"SUCCESS: Виртуальная машина {VM_NAME} создана")
                break         
            else:
                print (f"Виртуальная машина {VM_NAME} создается.")
        break



# Функция для проверки статуса вДиска
def CheckVMdisk(connection,VM_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    for vm in vms:
        vm_name = vm.name
        if vm_name == VM_NAME:

            #Определяем id вДисков, подключенных к ВМ
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                disks_service = connection.system_service().disks_service()
                disk_service = disks_service.disk_service(disk_attachment.disk.id)
                while True:
                    time.sleep(1)
                    disk = disk_service.get()
                    if disk.status == types.DiskStatus.OK:
                        print(f"Диски ВМ {VM_NAME} созданы")
                        break


#Функция включения ВМ
def StartVM(connection,VM_NAME):
    vms_service = connection.system_service().vms_service()
    vm = vms_service.list(search='name=' + VM_NAME)[0]
    vm_service = vms_service.vm_service(vm.id)
    try:
        vm_service.start()
        print(f"ВМ {VM_NAME} запускается")
    except:
        print(f"Error: {VM_NAME}")
        pass


#Функция проверяет запустилась ли ВМ
def CheckVM(connection,NEW_VM_NAME):
    vms_service = connection.system_service().vms_service()
    vm = vms_service.list(search='name=' + NEW_VM_NAME)[0]
    vm_service = vms_service.vm_service(vm.id)
    while True:
        time.sleep(1)
        vm = vm_service.get()
        if vm.status == types.VmStatus.UP:
            break

# Функция переименования дисков
def RenameDisks(connection,NEW_VM_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    for vm in vms:
        vm_name = vm.name
        if vm_name == NEW_VM_NAME:
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()

            #Переименовываем диски
            disk_id = 1
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                #disk = connection.follow_link(disk_attachment.disk)
                #vm_disk_by = disk.provisioned_size
                #vm_disk_gb = vm_disk_by / 1024 / 1024 /1024
                #vm_disk_gb_round = (round (vm_disk_gb))
                #vm_alias = disk.alias

                #Переименовываем системный диск
                disk_attachment_service = disk_attachments_service.attachment_service(disk_attachment.id)
                disk_attachment_service.update(
                    types.DiskAttachment(
                        disk=types.Disk(
                            name=NEW_VM_NAME + '_' + str(disk_id),
                        ),
                    ),
                )
                disk_id += 1

# Функция проверки префиксов ВМ, которые уже существуют в системе
def check_prefix(connection, VM_NAME):
    # Get the reference to the root service:
    system_service = connection.system_service()

    # Find all the virtual machines and store the id and name in a dictionary, so that looking them up later will be faster:
    vms_service = system_service.vms_service()
    
    # Use the "list" method of the "vms" service to list all the virtual machines of the system:
    vms = vms_service.list()
    for vm in vms:
        if re.search(VM_NAME.lower(), vm.name.lower()):
            #print(f"ВМ {vm.name} уже существует")
            return True

# Функция поиска ВМ на основе префика, введенного пользователем - vm_match
def select_vm(connection, vm_match):
    # Get the reference to the root service:
    system_service = connection.system_service()

    # Find all the virtual machines and store the id and name in a dictionary, so that looking them up later will be faster:
    vms_service = system_service.vms_service()
    
    # Use the "list" method of the "vms" service to list all the virtual machines of the system:
    vms = vms_service.list()

    
    vm_arr = []
    vm_num = 0
    VM_ID_ARR = []
    while True:
        for vm in vms:
            if vm_match == '*':
                vm_num += 1
                vm_arr.append(vm.id)
                print(f"{vm_num}: {vm.name}, status: {vm.status}")
                #print(vm_num + ' :' +  Fore.RED + vm.name + Style.RESET_ALL + ' , status:' + vm.status)
            elif re.search(vm_match.lower(), vm.name.lower()):
                vm_num += 1
                vm_arr.append(vm.id)
                print(f"{vm_num}: {vm.name}, status: {vm.status}")
        vm_indexes = input(f"Введите номера ВМ (через пробел) или '*' для выбора всех ВМ> ")
        if vm_indexes == '*':
            return vm_arr
        elif vm_indexes == '0':
            print(f"Введен неправильный номер ВМ, повторите снова")
            vm_num = 0
            pass
        else:
            vm_index_list = vm_indexes.split(' ')
            print(vm_index_list)
            try:
                for vm_index in vm_index_list:
                    VM_ID_ARR.append(vm_arr[int(vm_index) - 1])
                return VM_ID_ARR
                break
            except ValueError:
                print(f"Введен неправильный номер ВМ, повторите снова")
                vm_num = 0
            except IndexError:
                print(f"Введен неправильный номер ВМ, повторите снова")
                vm_num = 0
            except TypeError:
                print(f"Введен неправильный номер ВМ, повторите снова")
                vm_num = 0

# Функция удаления выбранных ВМ
def delete_vm(connection, VM_ID_ARR):
     # Get the reference to the root service:
    system_service = connection.system_service()

    # Find all the virtual machines and store the id and name in a dictionary, so that looking them up later will be faster:
    vms_service = system_service.vms_service()
    
    # Use the "list" method of the "vms" service to list all the virtual machines of the system:
    vms = vms_service.list()

    for vm_id in VM_ID_ARR:
            for vm in vms:
                if vm.id == vm_id:
                    #time.sleep(5)
                    #vm = vms_service.list(search='id={vm_id}')[0]
                    vm_service = vms_service.vm_service(vm.id)
                    vm = vm_service.get()
                    #print(f"ВМ {vm.name}: {vm.status}")
                    if vm.status == types.VmStatus.UP or vm.status == types.VmStatus.WAIT_FOR_LAUNCH or types.VmStatus.POWERING_UP:
                         vm_service.stop()
                         print(f"ВМ {vm.name} выключается")
                         time.sleep(3)
                         vm_service.remove()
                         print(f"ВМ {vm.name} удалена")
                         time.sleep(1)
                    else:
                        vm_service.remove()
                        time.sleep(1)

def main():

    # Задаем параметры памяти и ЦПУ ВМ
    MEMORY_VM = 1 * 1024 *1024 *1024
    VCPU_VM = 1

    connection = ovirt_connect(OVIRT_URL)
  
    while True:
        VM_ACTION = input(f"Введите требуемое действие ('с'- для создания ВМ, 'd' для удаления ВМ или любую клавишу для выхода) >")
        if VM_ACTION == 'c':
            CLUSTER_ID = SelectCluster(connection)
            TMPL_ID = SelectTemplate(connection, CLUSTER_ID)
            while True:
                VM_NUM = input(f"Введите требуемое количество ВМ >")
                try:
                    VM_NUM = int(VM_NUM) + 1
                except ValueError:
                    print(f"Введите требуемое количество ВМ еще раз")
                else:
                    break

            while True:
                PREFIX_VM_NAME = input(f"Введите префикс названия ВМ >")
                if bool(re.search(r"\s", PREFIX_VM_NAME)):
                    print(f"Введите ещё раз префикс названия ВМ без пробелов")
                elif check_prefix(connection, PREFIX_VM_NAME):
                    print(f"Префикс {PREFIX_VM_NAME} уже существует, укажите другой")
                else:
                    break

            for i in range(1, VM_NUM):
                VM_NAME = PREFIX_VM_NAME+'-'+str(i)
                #print(NEW_VM_NAME)

                # Создаем новую ВМ
                CreateVM(connection,VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM)
                #time.sleep(3) # Sleep for 2 seconds

            for i in range(1, VM_NUM):
                VM_NAME = PREFIX_VM_NAME+'-'+str(i)

                #Проверяем создалась ли ВМ
                CheckVMAvailable(connection,VM_NAME)

            for i in range(1, VM_NUM):
                VM_NAME = PREFIX_VM_NAME+'-'+str(i)

                #Проверяем создались ли диски ВМ
                CheckVMdisk(connection,VM_NAME)

            start_action = input(f"Включить созданные ВМ? ('y' - включить, 'n' - оставить выключенными или любую клавишу для выхода): ")
            if start_action == 'y':
                for i in range(1, VM_NUM):
                    VM_NAME = PREFIX_VM_NAME+'-'+str(i)
                    StartVM(connection,VM_NAME)
            elif start_action == 'n':
                print(f"Созданные ВМ не будут запущены")
            else:
                exit()
        elif VM_ACTION == 'd':
            vm_match = input(f"Введите честь названия ВМ (или '*' для вывода всех ВМ): ")
            #print(type(vm_match))
            VM_ID_ARR = select_vm(connection, vm_match)
            delete_vm(connection, VM_ID_ARR)
        else:
            break
   


    connection.close()


if __name__ == '__main__':
    main()
