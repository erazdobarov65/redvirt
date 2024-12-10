# Скрипт для массового создания и удаления виртуальных машин в среде Ред Виртуализация (oVirt 4.4)
# Запускается из командной строки без аргументов.
# Работает в интерактивном режиме
# !!!Внимание!!!
# Перед использованием скрипта задайте свои значения переменных:
# OVIRT_USER -  пользователь ovirt с админскими правами (на создание ВМ)
# OVIRT_PASS - пароль пользователя
# OVIRT_URL -  адрес API ovirt-engine в виде "https://<hosted-engine>/ovirt-engine/api" где <hosted-engine> - FQDN менеджера виртуализации



#import logging
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
#import re, sys, base64, getopt, socket, csv, os,
import time, requests
import re
#from colorama import Fore, Back, Style, init
#from os.path import exists


# Задаем параметры подключения

OVIRT_USER = "admin@internal" #admin
OVIRT_PASS = ""
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
    cluster_arr_name = []
    cluster_num = 0
    while True:
        for cluster in clusters:
            cluster_num += 1
            cluster_arr.append(cluster.id)
            cluster_arr_name.append(cluster.name)
            print(f"{cluster_num}: {cluster.name}")
        cluster_index = input(f"Введите номер кластера > ")
        try:
            cluster_index = int(cluster_index) - 1
        except ValueError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0
        try:
            CLUSTER_ID = cluster_arr[cluster_index]
            CLUSTER_NAME = cluster_arr_name[cluster_index]
            print(f"Выбран кластер: {CLUSTER_NAME}")
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
    tms_arr_name = []
    tms_num = 0
    while True:
        for tm in tms:
            try:
                if tm.cluster.id == CLUSTER_ID:
                    tms_num += 1
                    tms_arr.append(tm.id)
                    tms_arr_name.append(tm.name)
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
            TMPL_NAME = tms_arr_name[tmpl_index]
            print(f"Выбран шаблон: {TMPL_NAME}")
            return TMPL_ID
            break
        except IndexError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0
        except TypeError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0

# Функция создания новой ВМ с толстыми дисками и в произвольно выбранном домене
def CreateVM_thick(connection,NEW_VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM, SD_ID):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    print (f"Создается новая ВМ: {NEW_VM_NAME}")
    vms_service.add(
        types.Vm(
            name=NEW_VM_NAME,
            memory=MEMORY_VM,
            cluster=types.Cluster(id=CLUSTER_ID),
            storage_domain=types.StorageDomain(id=SD_ID),
            template=types.Template(id=TMPL_ID),
            memory_policy=types.MemoryPolicy(
                guaranteed=MEMORY_VM,
                max=MEMORY_VM * 4,
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
        clone=True #диски толстые.
    )

# Функция создания новой ВМ с тонкими дисками в сторадж домене, где находятся диски шаблона
def CreateVM_thin(connection,NEW_VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM):
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
                max=MEMORY_VM * 4,
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

# Функция для проверки создалась ли ВМ
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
                    print(f"Диски ВМ {VM_NAME} создаются")
                    time.sleep(5)
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


# Функция проверяет запустилась ли ВМ
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
                print(f"Диск переименован: {NEW_VM_NAME}_{disk_id}")
                disk_id += 1

# функция проверки префиксов существующих ВМ
def CheckPrefix(connection, VM_NAME):
    system_service = connection.system_service()
    vms_service = system_service.vms_service()
    vm_name_arr = []
    
    vms = vms_service.list()
    for vm in vms:
        if re.search(VM_NAME.lower(), vm.name.lower()):
            vm_name_arr.append(vm.name)
            #print(f"ВМ {vm.name} уже существует")
    return vm_name_arr

# Функция поиска ВМ на основе префика, введенного пользователем - vm_match
def select_vm(connection, vm_match):

    system_service = connection.system_service()
    vms_service = system_service.vms_service()
    
    vms = vms_service.list()

    vm_arr = []
    vm_arr_name = []
    vm_num = 0
    vm_num_selected =0
    VM_ID_ARR = []
    VM_NAME_ARR = []
    while True:
        for vm in vms:
            if vm_match == '*':
                vm_num += 1
                vm_arr.append(vm.id)
                vm_arr_name.append(vm.name)
                print(f"{vm_num}: {vm.name}, status: {vm.status}")
                #print(vm_num + ' :' +  Fore.RED + vm.name + Style.RESET_ALL + ' , status:' + vm.status)
            elif re.search(vm_match.lower(), vm.name.lower()):
                vm_num += 1
                vm_arr.append(vm.id)
                vm_arr_name.append(vm.name)
                print(f"{vm_num}: {vm.name}, status: {vm.status}")
        if len(vm_arr) == 0:
            return vm_arr
        vm_indexes = input(f"Введите номера ВМ (через пробел) или '*' для выбора всех ВМ > ")
        if vm_indexes == '*':
            print(f"Выбраны ВМ:")
            for vm_name in vm_arr_name:
                vm_num_selected += 1
                print(f"{vm_num_selected}: {vm_name}")
            return vm_arr
        elif vm_indexes == '0':
            print(f"Введен неправильный номер ВМ, повторите снова")
            vm_num = 0
            pass
        else:
            vm_index_list = vm_indexes.split(' ')
            #print(vm_index_list)
            try:
                for vm_index in vm_index_list:
                    VM_ID_ARR.append(vm_arr[int(vm_index) - 1])
                    VM_NAME_ARR.append(vm_arr_name[int(vm_index) - 1])
                print(f"Выбраны ВМ:")
                for vm_name in VM_NAME_ARR:
                    vm_num_selected += 1
                    print(f"{vm_num_selected}: {vm_name}")
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

#Функция выбора сторадж домена
def SelectDomain(connection):
    sds_service = connection.system_service().storage_domains_service()
    sds = sds_service.list()

    sd_arr = []
    sd_arr_name = []
    sd_num = 0
    while True:
        for sd in sds:
            sd_type = sd.type
            sd_type = str(sd_type)
            if sd_type  == "data":
                sd_num += 1
                sd_arr.append(sd.id)
                sd_arr_name.append(sd.name)
                size_avail = round(sd.available / 1024 /1024 /1024)
                size_full = round((sd.committed + sd.available)  / 1024 /1024 /1024)
                print(f"{sd_num}: {sd.name}, полный объем домена {size_full} ГБ, доступный объем {size_avail} ГБ")
        sd_index = input(f"Введите номер домена в котором нужно разместить толстые диски ВМ или введите '0' для создания тонких дисков в домене выбранного шаблона > ")
        try:
            if sd_index == '0':
                SD_ID = 0
                return SD_ID
                break
            else:
                sd_index = int(sd_index) - 1
        except ValueError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0
        try:
            SD_ID = sd_arr[sd_index]
            SD_NAME = sd_arr_name[sd_index]
            print(f"Выбран домен хранения: {SD_NAME}")
            return SD_ID
            break
        except IndexError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0
        except TypeError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0


# Функция удаления выбранных ВМ
def delete_vm(connection, VM_ID_ARR):
    system_service = connection.system_service()
    vms_service = system_service.vms_service()
    
    vms = vms_service.list()

    for vm_id in VM_ID_ARR:
            for vm in vms:
                if vm.id == vm_id:
                    #time.sleep(5)
                    #vm = vms_service.list(search='id={vm_id}')[0]
                    vm_service = vms_service.vm_service(vm.id)
                    vm = vm_service.get()
                    #print(f"ВМ {vm.name}: {vm.status}")
                    if vm.status == types.VmStatus.DOWN:
                        vm_service.remove()
                        print(f"ВМ {vm.name} удалена")
                        time.sleep(1)
                    else:
                        vm_service.stop()
                        print(f"ВМ {vm.name} выключается")
                        time.sleep(3)
                        vm_service.remove()
                        print(f"ВМ {vm.name} удалена")
                        time.sleep(1)
                        

def main():

    # Задаем параметры памяти и ЦПУ ВМ
    #MEMORY_VM = 1 * 1024 *1024 *1024
    #VCPU_VM = 1

    connection = ovirt_connect(OVIRT_URL)
    

    while True:
        VM_ACTION = input(f"Введите требуемое действие ('с'- для создания ВМ, 'd' для удаления ВМ или любую клавишу для выхода) > ")
        if VM_ACTION == 'c':
            CLUSTER_ID = SelectCluster(connection)
            TMPL_ID = SelectTemplate(connection, CLUSTER_ID)
            SD_ID = SelectDomain(connection)

            while True:
                VCPU_VM = input(f"Введите требуемое количество CPU > ")
                try:
                    VCPU_VM = int(VCPU_VM)
                except ValueError:
                    print(f"Введите требуемое количество CPU еще раз")
                else:
                    break

            while True:
                MEMORY_VM = input(f"Введите требуемый объем памяти в ГБ > ")
                try:
                    MEMORY_VM = int(MEMORY_VM) *1024 *1024 *1024
                except ValueError:
                    print(f"Введите требуемый объем памяти еще раз")
                else:
                    break

            while True:
                VM_NUM = input(f"Введите требуемое количество ВМ > ")
                try:
                    VM_NUM = int(VM_NUM) + 1
                except ValueError:
                    print(f"Введите требуемое количество ВМ еще раз")
                else:
                    break

            while True:
                PREFIX_VM_NAME = input(f"Введите префикс названия ВМ > ")
                if bool(re.search(r"\s", PREFIX_VM_NAME)):
                    print(f"Введите ещё раз префикс названия ВМ без пробелов")
                else:
                    VM_NAME_ARR = CheckPrefix(connection,PREFIX_VM_NAME)
                    print(VM_NAME_ARR)
                    try:
                        VM_NUM_ARR = []
                        for VM_NAME in VM_NAME_ARR:
                            m = re.search('-(\d+)$', VM_NAME)
                            VM_NUMBER = m.group(1)
                            VM_NUM_ARR.append(VM_NUMBER)
                        VM_NUM_MAX = int(max(VM_NUM_ARR))
                        VM_NUM_FOR = VM_NUM + int(VM_NUM_MAX)
                        VM_CURRENT_NUM = int(VM_NUM_MAX) + 1

                        VM_NUM_MAX_1 = int(max(VM_NUM_ARR))
                        VM_NUM_FOR_1 = VM_NUM + int(VM_NUM_MAX_1)
                        VM_CURRENT_NUM_1 = int(VM_NUM_MAX_1) + 1

                        VM_NUM_MAX_2 = int(max(VM_NUM_ARR))
                        VM_NUM_FOR_2 = VM_NUM + int(VM_NUM_MAX_2) 
                        VM_CURRENT_NUM_2 = int(VM_NUM_MAX_2) + 1

                        VM_NUM_MAX_3 = int(max(VM_NUM_ARR))
                        VM_NUM_FOR_3 = VM_NUM + int(VM_NUM_MAX_3)
                        VM_CURRENT_NUM_3 = int(VM_NUM_MAX_3) + 1

                    except AttributeError:
                        VM_NUM_MAX = 0
                        VM_NUM_FOR = VM_NUM + VM_NUM_MAX
                        VM_CURRENT_NUM = 1

                        VM_NUM_MAX_1 = 0
                        VM_NUM_FOR_1 = VM_NUM + VM_NUM_MAX_1
                        VM_CURRENT_NUM_1 = 1

                        VM_NUM_MAX_2 = 0
                        VM_NUM_FOR_2 = VM_NUM + VM_NUM_MAX_2
                        VM_CURRENT_NUM_2 = 1

                        VM_NUM_MAX_3 = 0
                        VM_NUM_FOR_3 = VM_NUM + VM_NUM_MAX_3
                        VM_CURRENT_NUM_3 = 1

                    except ValueError:
                        VM_NUM_MAX = 0
                        VM_NUM_FOR = VM_NUM + VM_NUM_MAX
                        VM_CURRENT_NUM = 1

                        VM_NUM_MAX_1 = 0
                        VM_NUM_FOR_1 = VM_NUM + VM_NUM_MAX_1
                        VM_CURRENT_NUM_1 = 1

                        VM_NUM_MAX_2 = 0
                        VM_NUM_FOR_2 = VM_NUM + VM_NUM_MAX_2
                        VM_CURRENT_NUM_2 = 1

                        VM_NUM_MAX_3 = 0
                        VM_NUM_FOR_3 = VM_NUM + VM_NUM_MAX_3
                        VM_CURRENT_NUM_3 = 1
                    break

            while True:
                RENAME_VM_DISKS = input(f"Для переименования дисков ВМ в соответствии с уазанным префиксом, введите 'y' или 'n' - оставить имя дисков из шаблона > ")
                if RENAME_VM_DISKS == 'y':
                    print(f"Диски ВМ будут переименованы в соответствии с указанным префиксом: {PREFIX_VM_NAME}")
                    break
                elif RENAME_VM_DISKS == 'n':
                    print(f"Диски ВМ сохранят имена из шаблона")
                    break
                else:
                    print(f"Введите 'y' или 'n'")

            for i in range(int(VM_NUM_MAX) + 1, VM_NUM_FOR):
                VM_NAME = PREFIX_VM_NAME + '-' + str(VM_CURRENT_NUM)
                #VM_NAME = PREFIX_VM_NAME+'-'+str(i)
                #print(NEW_VM_NAME)

                # Создаем новую ВМ
                if SD_ID != 0: # Если домен хранения выбран произвольный, то с толсыми дисками
                    CreateVM_thick(connection,VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM, SD_ID)
                    VM_CURRENT_NUM += 1
                else: # В противном случае (если выбран 0)с тонкими дисками
                    CreateVM_thin(connection,VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM)
                    VM_CURRENT_NUM += 1
            
            for i in range(int(VM_NUM_MAX_1) + 1, VM_NUM_FOR_1):
                VM_NAME = PREFIX_VM_NAME + '-' + str(VM_CURRENT_NUM_1)

                #Проверяем создалась ли ВМ
                CheckVMAvailable(connection,VM_NAME)
                VM_CURRENT_NUM_1 += 1

            for i in range(int(VM_NUM_MAX_2) + 1, VM_NUM_FOR_2):
                VM_NAME = PREFIX_VM_NAME + '-' + str(VM_CURRENT_NUM_2)

                #Проверяем создались ли диски ВМ
                CheckVMdisk(connection,VM_NAME)
                if RENAME_VM_DISKS == 'y':
                    # Переименовываем диски
                    RenameDisks(connection, VM_NAME)
                VM_CURRENT_NUM_2 += 1

            start_action = input(f"Включить созданные ВМ? ('y' - включить, 'n' - оставить выключенными или любую клавишу для выхода) > ")
            if start_action == 'y':
                for i in range(int(VM_NUM_MAX_3) + 1, VM_NUM_FOR_3):
                    VM_NAME = PREFIX_VM_NAME + '-' + str(VM_CURRENT_NUM_3)
                    StartVM(connection,VM_NAME)
                    VM_CURRENT_NUM_3 += 1
            elif start_action == 'n':
                print(f"Созданные ВМ не будут запущены")
            else:
                exit()
        elif VM_ACTION == 'd':
            while True:
                vm_match = input(f"Введите часть названия ВМ (или '*' для вывода всех ВМ) > ")
                #print(type(vm_match))
                VM_ID_ARR = select_vm(connection, vm_match)
                if len(VM_ID_ARR) == 0:
                    print(f"Не найдено ВМ, соответствующих указанным критериям. Попробуйте еще раз")
                else:
                    delete_vm(connection, VM_ID_ARR)
                    break
        else:
            break
   
    connection.close()

if __name__ == '__main__':

    main()
