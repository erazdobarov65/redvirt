import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import time, requests
#import openpyxl
import re
import random

OVIRT_USER = "admin@internal"  # admin
OVIRT_PASS = ""
OVIRT_URL = "https://engine.redvirt.tst/ovirt-engine/api"

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def getStatuscode(url, user, passw):
    try:
        r = requests.head(url, verify=False, timeout=5, auth=(user, passw))
        return r.status_code
    except:
        return -1

def ovirt_connect(OVIRT_URL):
    connection = sdk.Connection(
        url=OVIRT_URL,
        username=OVIRT_USER,
        password=OVIRT_PASS,
        insecure=True,
    )
    return connection

# Функция выбора нескольких ВМ по префиксу
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
                try:
                    vmhost = connection.follow_link(vm.host)
                    print(f"{vm_num}: {vm.name}, status: {vm.status}, хост: {vmhost.name}")
                except AttributeError:
                    print(f"{vm_num}: {vm.name}, status: {vm.status}")
                #print(vm_num + ' :' +  Fore.RED + vm.name + Style.RESET_ALL + ' , status:' + vm.status)
            elif re.search(vm_match.lower(), vm.name.lower()):
                vm_num += 1
                vm_arr.append(vm.id)
                vm_arr_name.append(vm.name)
                try:
                    vmhost = connection.follow_link(vm.host)
                    print(f"{vm_num}: {vm.name}, status: {vm.status}, хост: {vmhost.name}")
                except AttributeError:
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

# Функция запуска ВМ. принимает в качестве параметра список ид ВМ
def ActionStart(connection, VM_ID_ARR):
    
    system_service = connection.system_service()
    vms_service = system_service.vms_service()

    vms = vms_service.list()

    
    for vm_id in VM_ID_ARR:
        # Find the virtual machine:
        for vm in vms:
            if vm.id == vm_id:
                vm_service = vms_service.vm_service(vm.id)
                if vm.status == types.VmStatus.UP:
                    print(f"ВМ {vm.name} уже запущена")
                else:
                    vm_service.start()
    
    
    for vm_id in VM_ID_ARR:
        for vm in vms:
            if vm.id == vm_id:
                vm_service = vms_service.vm_service(vm.id)
                vm = vm_service.get()
                if vm.status == types.VmStatus.UP:
                    #print(f"ВМ {vm.name} запущена")
                    break
                else:
                    while True:
                        #time.sleep(5)
                        #vm = vms_service.list(search='id={vm_id}')[0]
                        vm = vm_service.get()
                        #print(f"ВМ {vm.name} запускается...")
                        #print(vm.status)
                        time.sleep(1)
                        if vm.status == types.VmStatus.UP or vm.status == types.VmStatus.WAIT_FOR_LAUNCH or vm.status == types.VmStatus.POWERING_UP:
                            print(f"ВМ {vm.name} запускается")
                            break

# Функция остановки ВМ. принимает в качестве параметра список ид ВМ
def ActionStop(connection, VM_ID_ARR):
    
    system_service = connection.system_service()
    vms_service = system_service.vms_service()

    vms = vms_service.list()

    
    for vm_id in VM_ID_ARR:
        # Find the virtual machine:
        for vm in vms:
            if vm.id == vm_id:
                vm_service = vms_service.vm_service(vm.id)
                if vm.status == types.VmStatus.DOWN:
                    print(f"ВМ {vm.name} уже выключена")
                else:
                    vm_service.stop()
    
    
    for vm_id in VM_ID_ARR:
        for vm in vms:
            if vm.id == vm_id:
                vm_service = vms_service.vm_service(vm.id)
                vm = vm_service.get()
                if vm.status == types.VmStatus.DOWN:
                    print(f"ВМ {vm.name} выключена")
                    break
                else:
                    while True:
                        #time.sleep(5)
                        #vm = vms_service.list(search='id={vm_id}')[0]
                        vm = vm_service.get()
                        #print(f"ВМ {vm.name} выключается...")
                        time.sleep(1)
                        if vm.status == types.VmStatus.DOWN or vm.status == types.VmStatus.POWERING_DOWN:
                            print(f"ВМ {vm.name} выключается")
                            break

# Функция отображения списка ВМ на экране
def ShowSelectedVM(connection, VM_ID_ARR):
    
    system_service = connection.system_service()
    vms_service = system_service.vms_service()

    vms = vms_service.list()

    print(f"Выбраны ВМ:")
    for vm_id in VM_ID_ARR:
        for vm in vms:
            if vm.id == vm_id:
                print(f"{vm.name}, status: {vm.status}")

# Функция выбора хоста
def SelectHost(connection):
    
    hosts_service = connection.system_service().hosts_service()
    hosts = hosts_service.list()
    
    host_dict = {}
    host_num = 0
    host_num_selected =0
    HOST_DICT = {}
    while True:
        for host in hosts:
            if host.status.UP:
                host_num += 1
                host_dict[host.id] = host.name
                print(f"{host_num}: {host.name}, Состояние: {host.status}, Запущенных ВМ: {host.summary.active}")
                #print(vm_num + ' :' +  Fore.RED + vm.name + Style.RESET_ALL + ' , status:' + vm.status)
        host_indexes = input(f"Введите номера хостов (через пробел) или '*' для выбора всех хостов > ")
        if host_indexes == '*':
            print(f"Для миграции выбраны хосты:")
            for host_name in host_dict.values():
                host_num_selected += 1
                print(f"{host_num_selected}: {host_name}")
            return host_dict
        elif host_indexes == '0':
            print(f"Введен неправильный номер хоста, повторите снова")
            host_num = 0
            pass
        else:
            host_index_list = host_indexes.split(' ')
            #print(vm_index_list)
            try:
                for host_index in host_index_list:
                    index = int(host_index) - 1
                    k, v = list(host_dict.items())[index]
                    #print(k, v)
                    HOST_DICT[k] = v
                print(f"Для миграции выбраны хосты:")
                for host_name in HOST_DICT.values():
                    host_num_selected += 1
                    print(f"{host_num_selected}: {host_name}")
                #print(DISK_NAME_DICT)
                return HOST_DICT
                break
            except ValueError:
                print(f"Введен неправильный номер хоста, повторите снова")
                host_num = 0
            except IndexError:
                print(f"Введен неправильный номер хоста, повторите снова")
                host_num = 0
            except TypeError:
                print(f"Введен неправильный номер хоста, повторите снова")
                host_num = 0

# Функция фильтрации списка ВМ, которые могут мигрировать (т.е. находятся во включенном состоянии)
def SelectVMtoMigrate(connection, VM_ID_ARR, HOST_DICT):

    hosts_service = connection.system_service().hosts_service()
    hosts = hosts_service.list()
    
    host_arr = []
    vm_arr = []
    for host in hosts:
        if host.status.UP:
            host_arr.append(host.id)


    system_service = connection.system_service()
    vms_service = system_service.vms_service()

    vms = vms_service.list()

    print(f"Выбранные ВМ запущены на хостах:")

    for vm in vms:
        if vm.id in VM_ID_ARR:
            if vm.status == types.VmStatus.UP:
                vmhost = connection.follow_link(vm.host)
                if vmhost.id in HOST_DICT.keys():
                    host_count = 0
                    for k in HOST_DICT.keys():
                        host_count += 1
                    if host_count == 1:
                        print(f"ВМ: {vm.name} уже запущена на хосте: {vmhost.name}, ИСКЛЮЧЕНА из миграции")
                    else:
                        vm_arr.append(vm.id)
                        print(f"ВМ: {vm.name} запущена на хосте: {vmhost.name}, ДОБАВЛЕНА в миграцию")      
                else:
                    vm_arr.append(vm.id)
                    print(f"ВМ: {vm.name} запущена на хосте: {vmhost.name}, ДОБАВЛЕНА в миграцию")
            elif vm.status == types.VmStatus.DOWN:
                print(f"ВМ: {vm.name} выключена. Миграция НЕВОЗМОЖНА.")
    #print(vm_arr)
    return vm_arr

# Функция миграции ВМ. В качестве параметров принимает список отфильтрованных id ВМ и словарь с id и именами хостов   
def MigrateVM(connection, VM_ID_SELECT, HOST_DICT):

    system_service = connection.system_service()
    vms_service = system_service.vms_service()

    vms = vms_service.list()
    
    for VM_ID in VM_ID_SELECT:
        for vm in vms:
            if vm.id == VM_ID:
                vmhost = connection.follow_link(vm.host)
                vm_service = vms_service.vm_service(vm.id)
                #vm = vm_service.get()
                while True:
                    host_migrate = random.choice(list(HOST_DICT.items()))
                    if host_migrate[0] != vmhost.id:
                        vm_service.migrate(host=types.Host(id=host_migrate[0]))
                        print(f"ВМ {vm.name} мигрирует на хост {host_migrate[1]}")
                        break
                        
            
          
           

def main():
    connection = ovirt_connect(OVIRT_URL)
    while True:
        vm_match = input(f"Введите часть названия ВМ, '*' для вывода всех ВМ или любую кнопку для выхода: > ")
        if vm_match:
            VM_ID_ARR = SelectVM(connection, vm_match)
            #print(VM_ID_ARR)
            if len(VM_ID_ARR) == 0:
                print(f"Не найдено ВМ, соответствующих критериям поиска")
            elif VM_ID_ARR:
                ShowSelectedVM(connection, VM_ID_ARR)
                while True:
                    action = input(f"Выберите действие для выбранных ВМ ('on' - включить, 'off' - выключить, 'm' - мигрировать или любую кнопку для выхода): ")
                    if action == 'on':
                        ActionStart(connection, VM_ID_ARR)
                    elif action == 'off':
                        ActionStop(connection, VM_ID_ARR)
                    elif action == 'm':
                        HOST_DICT = SelectHost(connection)
                        VM_ID_SELECT = SelectVMtoMigrate(connection, VM_ID_ARR, HOST_DICT)
                        if len(VM_ID_SELECT) != 0: 
                            migrate_start = input(f"Начать миграцию (y/n)? > ")
                            if migrate_start == 'y':         
                                MigrateVM(connection, VM_ID_SELECT, HOST_DICT)
                            elif migrate_start == 'n': 
                                break
                    else:
                        break
        else:
            break
       

        
    
    connection.close()

if __name__ == '__main__':
    main()