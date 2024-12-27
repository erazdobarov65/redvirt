##############################################################################################################################################
# Скрипт для массового добавления дисков к выбранной включенной ВМ и в выбранный домен хранения
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
from datetime import datetime


# Задаем параметры подключения

OVIRT_USER = "admin@internal" #admin
OVIRT_PASS = ""
OVIRT_URL = "https://engine.redvirt.tst/ovirt-engine/api"

#Выключаем варнинги при проверке url без серта
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


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


# Функция поиска и выбора нескольких ВМ на основе префикса, введенного пользователем - vm_match
def SelectVM(connection, vm_match):

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
            return vm_arr_name
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
                return VM_NAME_ARR
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

# Функция поиска и выбора одиночной ВМ на основе префикса, введенного пользователем - vm_match
def SelectSingleVM(connection, vm_match):

    system_service = connection.system_service()
    vms_service = system_service.vms_service()
    
    vms = vms_service.list()

    vm_arr = []
    vm_arr_name = []
    vm_num = 0
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
            break
        vm_index = input(f"Введите номер нужной ВМ > ")
        if vm_index == '0':
            print(f"Введен неправильный номер ВМ, повторите снова")
            vm_num = 0
            pass
        else:
            #vm_index_list = vm_indexes.split(' ')
            #print(vm_index_list)
            try:
                VM_ID = vm_arr[int(vm_index) - 1]
                VM_NAME = vm_arr_name[int(vm_index) - 1]
                print(f"Выбрана ВМ: {VM_NAME}")
                return VM_NAME
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
    sd_num = 0
    while True:
        for sd in sds:
            sd_type = sd.type
            sd_type = str(sd_type)
            if sd_type  == "data":
                sd_num += 1
                sd_arr.append(sd.id)
                size_avail = round(sd.available / 1024 /1024 /1024)
                size_full = round((sd.committed + sd.available)  / 1024 /1024 /1024)
                print(f"{sd_num}: {sd.name}, полный объем домена {size_full} ГБ, доступный объем {size_avail} ГБ")
        sd_index = input(f"Введите номер домена > ")
        try:
            sd_index = int(sd_index) - 1
        except ValueError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0
        try:
            SD_ID = sd_arr[sd_index]
            #print(SD_ID)
            return SD_ID
            break
        except IndexError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0
        except TypeError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0

#Функция добавления диска к ВМ
def AddDisk(connection, VM_NAME, DISK_NAME, DISK_SIZE, DISK_DESCRIPTION, SD_ID, DISK_TYPE):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    #today = datetime.today().date()
    for vm in vms:
        if vm.name== VM_NAME and DISK_TYPE == 't':
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachment = disk_attachments_service.add(
                types.DiskAttachment(
                    disk=types.Disk(
                        name=DISK_NAME,
                        description=DISK_DESCRIPTION,
                        format=types.DiskFormat.COW,
                        provisioned_size=DISK_SIZE,
                        wipe_after_delete=True,
                        storage_domains=[
                            types.StorageDomain(
                                id=SD_ID,
                            ),
                        ],
                    ),
                    interface=types.DiskInterface.VIRTIO_SCSI,
                    bootable=False,
                    active=True,
                ),
            )
            # Проверяем создание диска:
            #print (f"INFO: Ждем создания диска ВМ {DISK_NAME}")
            disks_service = connection.system_service().disks_service()
            disk_service = disks_service.disk_service(disk_attachment.disk.id)
            disk=disk_service.get()
            if disk.status:
                print(f"Диск {DISK_NAME} создан")
            #while True:
            #    time.sleep(3)
            #   disk = disk_service.get()
            #   if disk.status == types.DiskStatus.OK:
            #       break

        elif vm.name== VM_NAME and DISK_TYPE == 'r':
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachment = disk_attachments_service.add(
                types.DiskAttachment(
                    disk=types.Disk(
                        name=DISK_NAME,
                        description=DISK_DESCRIPTION,
                        format=types.DiskFormat.RAW,
                        sparse=False,
                        backup=None,
                        provisioned_size=DISK_SIZE,
                        wipe_after_delete=True,
                        storage_domains=[
                            types.StorageDomain(
                                id=SD_ID,
                            ),
                        ],
                    ),
                    interface=types.DiskInterface.VIRTIO_SCSI,
                    bootable=False,
                    active=True,
                ),
            )

            # Проверяем создание диска:
            #print (f"INFO: Ждем создания диска ВМ {DISK_NAME}")
            disks_service = connection.system_service().disks_service()
            disk_service = disks_service.disk_service(disk_attachment.disk.id)
            disk = disk_service.get()
            if disk.status:
                print(f"Диск {DISK_NAME} создан")
            #while True:
            #    time.sleep(3)
            #    disk = disk_service.get()
            #    if disk.status == types.DiskStatus.OK:
            #       break

# Функция проверки имени диска
def CheckVMdisk(connection,VM_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    #DISK_NAME = VM_NAME+'_'+str(DISK_START)
    disk_name_arr = []
    for vm in vms:
        vm_name = vm.name
        if vm_name == VM_NAME:
            #Определяем id вДисков, подключенных к ВМ
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                disk = connection.follow_link(disk_attachment.disk)
                disk_name_arr.append(disk.name)
            #print(disk_name_arr)
            return disk_name_arr
                #if disk.name == DISK_NAME:
                    #m = re.search('_(.*)', DISK_NAME)
                    #disk_number = m.group(1)
                    #print(disk_number)
                    #return disk_number

# Функция выбора диска по имени ВМ               
def DiskSelectByVM(connection,VM_NAME):
    sds_service = connection.system_service().storage_domains_service()
    sds = sds_service.list()

    sd_dict = {}
    for sd in sds:
        sd_dict[sd.name] = sd.id
    
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    disk_arr = []
    disk_arr_name = []
    disk_num = 0
    disk_num_selected = 0
    DISK_ID_ARR = []
    DISK_NAME_ARR = []
    for vm in vms:
        vm_name = vm.name
        if vm_name == VM_NAME:
            #Определяем id вДисков, подключенных к ВМ
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                disk = connection.follow_link(disk_attachment.disk)
                disks_service = connection.system_service().disks_service()
                disk_service = disks_service.disk_service(disk_attachment.disk.id)
                disksd = disk_service.get()
                sd_id = disksd.storage_domains[0].id
                for k, v in sd_dict.items():
                    if v == sd_id:
                        sd_name = k
                #sdomain = disksd.storage_domains=[types.StorageDomain(id)]
                #print(sd_id)
                disk_num += 1
                disk_arr.append(disk.id)
                disk_arr_name.append(disk.name)
                disk_size = disk.provisioned_size /1024 /1024 /1024
                print(f"{disk_num}: {disk.name}, Размер диска: {disk_size} ГБ, Формат: {disk.format}, Домен: {sd_name}")
            disk_indexes = input(f"Введите номера дисков (через пробел) или '*' для выбора всех дисков > ")
            if disk_indexes == '*':
                print(f"Выбраны диски:")
                for disk_name in disk_arr_name:
                    disk_num_selected += 1
                    print(f"{disk_num_selected}: {disk_name}")
                return disk_arr
            else:
                disk_index_list = disk_indexes.split(' ')
                for disk_index in disk_index_list:
                    DISK_ID_ARR.append(disk_arr[int(disk_index) - 1])
                    DISK_NAME_ARR.append(disk_arr_name[int(disk_index) - 1])
                print(f"Выбраны диски:")
                for disk_name in DISK_NAME_ARR:
                    disk_num_selected += 1
                    print(f"{disk_num_selected}: {disk_name}")
                return DISK_ID_ARR
            
# Функия выбора имени диска по их именам
def DiskSelectByDisk(connection,disk_match):

    sds_service = connection.system_service().storage_domains_service()
    sds = sds_service.list()

    sd_dict = {}
    for sd in sds:
        sd_dict[sd.name] = sd.id

    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    disk_dict = {}
    disk_dict_name = {}
    disk_num = 0
    disk_num_selected = 0
    DISK_ID_DICT = {}
    DISK_NAME_DICT = {}
    while True:
        for vm in vms:
            #Определяем id вДисков, подключенных к ВМ
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments: 
                disk = connection.follow_link(disk_attachment.disk)
                
                if disk_match == '*':
                    disks_service = connection.system_service().disks_service()
                    disk_service = disks_service.disk_service(disk_attachment.disk.id)
                    disksd = disk_service.get()
                    sd_id = disksd.storage_domains[0].id
                    for k, v in sd_dict.items():
                        if v == sd_id:
                            sd_name = k
                    disk_num += 1
                    disk_dict[disk.id] = vm.name
                    disk_dict_name[disk.id] = disk.name
                    disk_size = disk.provisioned_size /1024 /1024 /1024
                    print(f"{disk_num}: Имя ВМ: {vm.name}, Диск: {disk.name}, Размер: {disk_size} ГБ, Формат: {disk.format}, Домен {sd_name}")
                elif re.search(disk_match.lower(), disk.name.lower()):
                    disks_service = connection.system_service().disks_service()
                    disk_service = disks_service.disk_service(disk_attachment.disk.id)
                    disksd = disk_service.get()
                    sd_id = disksd.storage_domains[0].id
                    for k, v in sd_dict.items():
                        if v == sd_id:
                            sd_name = k
                    disk_num += 1
                    disk_dict[disk.id] = vm.name
                    disk_dict_name[disk.id] = disk.name
                    disk_dict_name[disk.id] = disk.name
                    disk_size = disk.provisioned_size /1024 /1024 /1024
                    print(f"{disk_num}: Имя ВМ: {vm.name}, Диск: {disk.name}, Размер: {disk_size} ГБ, Формат: {disk.format}, Домен {sd_name}")
        if len(disk_dict) == 0:
            return disk_dict
        disk_indexes = input(f"Введите номера дисков (через пробел) или '*' для выбора всех дисков > ")
        if disk_indexes == '*':
            print(f"Выбраны диски:")
            for disk_name, vm_name in disk_dict_name.items():
                disk_num_selected += 1
                print(f"{disk_num_selected}: Диск {disk_name}: ВМ {vm_name}")
            return disk_dict
        elif disk_indexes == '0':
            print(f"Введен неправильный номер диска, повторите снова")
            disk_num = 0
            pass
        else:
            disk_index_list = disk_indexes.split(' ')
            print(disk_index_list)
            try:
                for disk_index in disk_index_list:
                    index = int(disk_index) - 1
                    k, v = list(disk_dict.items())[index]
                    #print(k, v)
                    DISK_ID_DICT[k] = v
                    kn, vn = list(disk_dict_name.items())[index]
                    DISK_NAME_DICT[kn] = vn
                print(f"Выбраны диски:")
                for disk_name in DISK_NAME_DICT.values():
                    disk_num_selected += 1
                    print(f"{disk_num_selected}: {disk_name}")
                #print(DISK_NAME_DICT)
                return DISK_ID_DICT
                break
            except ValueError:
                print(f"Введен неправильный номер диска1, повторите снова")
                disk_num = 0
            except IndexError:
                print(f"Введен неправильный номер диска2, повторите снова")
                disk_num = 0
            except TypeError:
                print(f"Введен неправильный номер диска3, повторите снова")
                disk_num = 0

# Функция удаления диска             
def DeleteDisk(connection, DISK_ID, VM_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    for vm in vms:
        vm_name = vm.name
        if vm_name == VM_NAME:
            # Получаем ссылку на объект disks service и находим нужные диски:
            disks_service = connection.system_service().disks_service()
            disks = disks_service.list()

            for disk in disks:
                if disk.id == DISK_ID:
                    # Находим объект disk attachment для интересующего диска:
                    vm_service = vms_service.vm_service(vm.id)
                    disk_attachments_service = vm_service.disk_attachments_service()
                    disk_attachments = disk_attachments_service.list()

                    disk_attachment = next(
                        (a for a in disk_attachments if a.disk.id == DISK_ID), None
                    )
                    # Деактивируем найденный диск
                    # Или выводим сообщение если диск не подключен
                    if disk_attachment is not None:
                        # Получам ссылку на службу, управляющую найденным объектом disk attachment 
                        disk_attachment_service = disk_attachments_service.attachment_service(disk_attachment.id)

                        # Декативируем подключение диска disk attachment
                        disk_attachment_service.update(types.DiskAttachment(active=False))

                        # Ждем завершения операция отключения (деактивации подключения):
                        while True:
                            time.sleep(3)
                            disk_attachment = disk_attachment_service.get()
                            if disk_attachment.active == False:
                                print (f"Диск {disk.name} отключен от ВМ {VM_NAME}")
                                break
                    else:
                        print (f"Диск {disk.name} не привреплен к ВМ")

    storage_domains_service = connection.system_service().storage_domains_service()
    sds = storage_domains_service.list()
    for sd in sds:
        #Определяем id вДисков, подключенных к ВМ
        sd_service = storage_domains_service.storage_domain_service(sd.id)
        sd_disks_service = sd_service.disks_service()
        sds_disks_service = sd_disks_service.list()
        #print(sds_disks_service)
        for disk in sds_disks_service:
            if disk.id == DISK_ID:
                sd_disks_service.disk_service(disk.id).remove()
                print(f"Удален диск: {disk.name}")
    
# Функция перемещения диска             
def MoveDisk(connection, DISK_ID, SD_ID):

    sds_service = connection.system_service().storage_domains_service()
    sds = sds_service.list()

    sd_dict = {}
    for sd in sds:
        sd_dict[sd.name] = sd.id
    for k, v in sd_dict.items():
        if v == SD_ID:
            SD_NAME = k

    print(f"Для перемещения выбран домен: {SD_NAME}")
    disks_service = connection.system_service().disks_service()
    disks = disks_service.list()
    for disk in disks:
        if disk.id == DISK_ID:
            disk_service = disks_service.disk_service(disk.id)
            sd = disk_service.get()
            sd_id = sd.storage_domains[0].id
            #print(sd_id)
            if sd_id == SD_ID:
                print(f"Диск {disk.name} уже находится в домене {SD_NAME}")
                break
            else:
                try:
                    disk_service.move(storage_domain=types.StorageDomain(id=SD_ID))
                    print(f"Диск {disk.name} перемещается в домен {SD_NAME}")
                except sdk.Error:
                    print(f"Диск {disk.name} невозможно перенести в домен {SD_NAME}")


def main():

    connection = ovirt_connect(OVIRT_URL)
    #VM_NAME = SelectVM(connection)
    while True:
        VM_ACTION = input(f"Введите требуемое действие для дисков ВМ ('a'- добавление, 'd' - удаление, 'm' - перемещение, или любую клавишу для выхода) > ")
        if VM_ACTION == 'a':
            SD_ID = SelectDomain(connection)
            #today = datetime.today().date()
            while True:
                vm_match = input(f"Введите часть названия ВМ (или '*' для вывода всех ВМ) > ")
                #print(type(vm_match))
                VM_NAME_ARR = SelectVM(connection, vm_match)
                if len(VM_NAME_ARR) == 0:
                    print(f"Не найдено ВМ, соответствующих указанным критериям. Попробуйте еще раз")
                else:        
                    while True:
                        DISK_SIZE = input(f"Введите требуемый размер диска (ГБ) > ")
                        try:
                            DISK_SIZE = int(DISK_SIZE) * 2**30
                        except ValueError:
                            print(f"Введите требуемый размер диска еще раз")
                        else:
                            break
                    #print(DISK_SIZE)
                    while True:
                        DISK_TYPE = input(f"Для создания тонкого диска введите 't', для толстого введите 'r' > ")
                        if DISK_TYPE == 't':
                            print(f"Будут созданы тонкие диски")
                            break
                        elif DISK_TYPE == 'r':
                            print(f"Будут созданы толстые диски")
                            break
                        else:
                            print(f"Введите 't' или 'r'")
                    while True:
                        DISK_NUM = input(f"Введите требуемое количество дисков > ")
                        try:
                            DISK_NUM = int(DISK_NUM)
                        except ValueError:
                            print(f"Введите требуемое количество дисков еще раз")
                        else:
                            break
                            
                    #print(DISK_NUM) 
                    for VM_NAME in VM_NAME_ARR:
                        #DISK_START = 1
                        DISK_NAME_ARR = CheckVMdisk(connection,VM_NAME)
                        DISK_NUM_ARR = []
                        for DISK_NAME in DISK_NAME_ARR:
                            m = re.search('_(\d+)$', DISK_NAME)
                            DISK_NUMBER = m.group(1)
                            DISK_NUM_ARR.append(DISK_NUMBER)
                         
                        #DISK_NUM_ARR = DISK_NUM_ARR.split(' ')
                        DISK_NUM_MAX = int(max(DISK_NUM_ARR))
                        DISK_NUM_FOR = DISK_NUM + int(DISK_NUM_MAX) + 1
                        DISK_CURRENT_NUM = int(DISK_NUM_MAX) + 1
                        for i in range(int(DISK_NUM_MAX) + 1, DISK_NUM_FOR):
                            DISK_NAME = VM_NAME + '_' + str(DISK_CURRENT_NUM)
                            DISK_DESCRIPTION = VM_NAME+ '_' + str(DISK_CURRENT_NUM)
                            #print(DISK_NAME)+
                            AddDisk(connection, VM_NAME, DISK_NAME, DISK_SIZE, DISK_DESCRIPTION, SD_ID, DISK_TYPE)
                            DISK_CURRENT_NUM += 1
                            i += 1
                        
                    break 

        elif VM_ACTION == 'd':
            while True:
                DELETE_MODE = input(f"Введите режим выбора дисков: v - по имени ВМ, d - по имени дисков > ")
                if DELETE_MODE == 'v':
                    while True:
                        vm_match = input(f"Введите часть названия ВМ (или '*' для вывода всех ВМ) > ")
                        #print(type(vm_match))
                        VM_NAME = SelectSingleVM(connection, vm_match)
                        if not VM_NAME:
                            print(f"Не найдено ВМ, соответствующих указанным критериям. Попробуйте еще раз")
                        else:
                            #DomainArr
                            DiskArr= DiskSelectByVM(connection, VM_NAME)
                            for disk in DiskArr:
                                DeleteDisk(connection, disk, VM_NAME)
                            break
                    break

                elif DELETE_MODE == 'd':
                    while True:
                        disk_match = input(f"Введите часть названия диска (или '*' для вывода всех дисков) > ")
                        #print(type(vm_match))
                        DiskDict = DiskSelectByDisk(connection, disk_match)
                        if len(DiskDict) == 0:
                            print(f"Не найдено дисков, соответствующих указанным критериям. Попробуйте еще раз")
                        else:
                            #print(DiskDict)
                            for disk_id, vm_name in DiskDict.items():
                                DeleteDisk(connection, disk_id, vm_name)
                            break
                    break

        elif VM_ACTION == 'm':
            while True:
                MOVE_MODE = input(f"Введите режим выбора дисков: v - по имени ВМ, d - по имени дисков > ")
                if MOVE_MODE == 'v':
                    while True:
                        vm_match = input(f"Введите часть названия ВМ (или '*' для вывода всех ВМ) > ")
                        #print(type(vm_match))
                        VM_NAME = SelectSingleVM(connection, vm_match)
                        if not VM_NAME:
                            print(f"Не найдено ВМ, соответствующих указанным критериям. Попробуйте еще раз")
                        else:
                            print(f"Выберете домен хранения для миграции:")
                            DiskArr= DiskSelectByVM(connection, VM_NAME)
                            SD_ID = SelectDomain(connection)
                            for disk in DiskArr:
                                MoveDisk(connection, disk, SD_ID)
                            break
                    break

                elif MOVE_MODE == 'd':
                    while True:
                        disk_match = input(f"Введите часть названия диска (или '*' для вывода всех дисков) > ")
                        #print(type(vm_match))
                        DiskDict = DiskSelectByDisk(connection, disk_match)
                        if len(DiskDict) == 0:
                            print(f"Не найдено дисков, соответствующих указанным критериям. Попробуйте еще раз")
                        else:
                            print(f"Выберете домен хранения для миграции:")
                            SD_ID = SelectDomain(connection)
                            #print(DiskDict)
                            for disk_id, vm_name in DiskDict.items():
                                MoveDisk(connection, disk_id, SD_ID)
                            break
                    break

        else:
            break



    connection.close()

if __name__ == '__main__':
    main()