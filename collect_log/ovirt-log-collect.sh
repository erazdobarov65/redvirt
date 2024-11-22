#!/bin/bash

# Скрипт работает в среде  Hosted-engine
# Запускается из ВМ ovirt-engine
# Собирает локальные логи с ВМ ovirt-engine и с выбранных гипервизоров
# Создает сжатый архив с логами в виде: ovirt-logs-yyyymmdd.tar.gz

SSHKeyChk="StrictHostKeyChecking=no"
SSHConTime="ConnectTimeout=3"
SSHConAtt="ConnectionAttempts=1"
SSHKey="/etc/pki/ovirt-engine/keys/engine_id_rsa"
SSHKeyOpt="-i ${SSHKey}"

SSH="ssh -q ${SSHKeyOpt} -o ${SSHKeyChk} -o ${SSHConTime} -o ${SSHConAtt}"
SCPF="scp -q ${SSHKeyOpt} -o ${SSHKeyChk} -o ${SSHConTime} -o ${SSHConAtt}"
SCPD="scp -q ${SSHKeyOpt} -o ${SSHKeyChk} -o ${SSHConTime} -o ${SSHConAtt} -r"
USER="root"


# Функция загрузки логов VDSM с гипервизоров
download_logs_vdsm() {
    local host=$1

    # Проверить доступность хоста
    if ping -c 3 "$host" &> /dev/null; then
        # Создать директорию с названием хоста и перейти в нее
        mkdir "$host"
        cd "$host"
        # Проверить наличие файла на хосте
        CHK="$( ${SSH} ${USER}@${host} [ -f /var/log/messages ] >/dev/null 2>&1; echo $? )"
        if [ ${CHK} == "0" ]; then
                # Загрузить логи с хоста
                ${SCPF} ${USER}@${host}:/var/log/messages .
        fi
        #mkdir vdsm
        # Проверить наличие директории на хосте
        CHK="$( ${SSH} ${USER}@${host} [ -d /var/log/vdsm ] >/dev/null 2>&1; echo $? )"
        if [ ${CHK} == "0" ]; then
                #mkdir vdsm
                # Загрузить логи с хоста
                ${SCPD} ${USER}@${host}:/var/log/vdsm* vdsm/
        fi
        [ -f messages ] && echo -e "Собраны логи\e[1;31m messages \e[0mс гипервизора $host"
        [ -d vdsm ] && [ -n "$(ls -A vdsm)" ] && echo -e "Собраны логи из директории\e[1;31m vdsm \e[0mгипервизора $host"
        # Перейти обратно в родительскую директорию
        cd ..
    else
        echo "Гипервизор $host не доступен"
    fi
}

# Функция загрузки полных логов с гипервизоров
download_logs() {
    local host=$1

    # Проверить доступность хоста
    if ping -c 3 "$host" &> /dev/null; then
        # Создать директорию с названием хоста и перейти в нее
        mkdir "$host"
        cd "$host"
        # Проверить наличие файла на хосте
        #CHK="$( ${SSH} ${USER}@${host} [ -f /var/log/messages ] >/dev/null 2>&1; echo $? )"
        #if [ ${CHK} == "0" ]; then
        #        # Загрузить логи с хоста
        #        ${SCPF} ${USER}@${host}:/var/log/messages .
        #fi
        #mkdir log
        # Проверить наличие директории на хосте
        CHK="$( ${SSH} ${USER}@${host} [ -d /var/log ] >/dev/null 2>&1; echo $? )"
        if [ ${CHK} == "0" ]; then
                mkdir log
                # Загрузить логи с хоста
                ${SCPD} ${USER}@${host}:/var/log/* log/
        fi
        #[ -f messages ] && echo -e "Собраны логи\e[1;31m messages \e[0mс гипервизора $host"
        [ -d log ] && [ -n "$(ls -A log)" ] && echo -e "Собраны логи из директории\e[1;31m /var/log \e[0mгипервизора $host"
        # Перейти обратно в родительскую директорию
        cd ..
    else
        echo "Гипервизор $host не доступен"
    fi
}


LOGS_DIR="ovirt-logs-$(date +%Y%m%d)"

# Если существует старая директория - удалить
[ -d "$LOGS_DIR" ] && rm -rf "$LOGS_DIR"

# Создать локальную директорью с текущей датой в названии
mkdir "$LOGS_DIR"

# Перейти в созданную директорию
cd "$LOGS_DIR"

read -p "Для полного сбора логов из каталога /var/log управляющей ВМ введите 'y' или нажмите 'Enter' для ограниченного сбора логов из каталога '/var/log/ovirt-engine': " user_input_engine_logtype
    if [ "$user_input_engine_logtype" == 'y' ]; then
        if [ -f /var/log/ovirt-engine/engine.log ]; then
            # Создать директорию 'ovirt-engine' и перейти в нее
            mkdir hosted-engine
            cd hosted-engine
            # Собрать полные логи /var/log с ВМ ovirt-engine
            [ -d /var/log ] && cp /var/log/ .
            [ -d log ] && echo "Собраны полностью локальные логи Engine из каталога /var/log"
        #   [ -d hosted-engine ] && echo "Собраны локальные логи Engine"
            # Перейти в родительскую директорию
            cd ..
        fi  
    else
        # Создать директорию 'ovirt-engine' и перейти в нее
        if [ -f /var/log/ovirt-engine/engine.log ]; then
            mkdir hosted-engine
            cd hosted-engine
            # Собрать полностью логи с ВМ ovirt-engine из каталога /var/log
            [ -d /var/log/ovirt-engine ] && cp -r /var/log/ovirt-engine .
            #[ -d /var/log/ovirt-engine/host-deploy ] &&  cp -r /var/log/ovirt-engine/host-deploy .
            #[ -d /var/log/ovirt-engine/setup ] && cp -r /var/log/ovirt-engine/setup .
            [ -f /var/log/httpd/ovirt-requests-log ] && cp /var/log/httpd/ovirt-requests-log .
            [ -f /var/log/ovirt-provider-ovn.log ] && cp /var/log/ovirt-provider-ovn.log .
            [ -d ovirt-engine ] || [ -f ovirt-requests-log ] || [ -f ovirt-provider-ovn.log ] && echo "Собраны локальные логи Engine"
        #   [ -d hosted-engine ] && echo "Собраны локальные логи Engine"
            # Перейти в родительскую директорию
            cd ..
            [ -d /var/log/vdsm ] && cp -r /var/log/vdsm .
            [ -d /var/log/libvirt ] && cp -r /var/log/libvirt .
            [ -s /var/log/messages ] && cp /var/log/messages .
            [ -d vdsm ] && [ -d libvirt ] &&  [ -f messages ] && echo "Собраны локальные логи Standalone engine или гипервизора"
        fi     
    fi


if [ -f /etc/pki/ovirt-engine/ca.pem ]; then
    CERT_OVIRT=$(openssl x509 -text -noout -in /etc/pki/ovirt-engine/ca.pem | grep -A2 Validity)
    # Добавить информацию о валидности сертификата engine
    echo -e "Срок действия сертификата (ca.pem) engine\e[1;31m $(hostname) \e[0m"  > certs_validity
    echo "$CERT_OVIRT" >> certs_validity
fi

# Добавить информацию о валидности сертификата standalone Хоста
if [ -d /etc/pki/vdsm/certs ] && [ -f /etc/pki/vdsm/certs/vdsmcert.pem ]; then
    echo -e "Срок действия сертификата (vdsmcert.pem) standalone хоста\e[1;31m ${HOSTS_ARR[$i]} \e[0m"  >> certs_validity
    echo "$(openssl x509 -text -noout -in  /etc/pki/vdsm/certs/vdsmcert.pem | grep -A2 Validity)" >> certs_validity
fi

# Проверить наличие хостов
if [ -d /etc/pki/ovirt-engine/certs ]; then
    CHK_HOSTS="$(ls /etc/pki/ovirt-engine/certs/ | grep -E "*ssh.cer$" | grep -v $(hostname) > /dev/null 2>&1; echo $?)"
    if [ ${CHK_HOSTS} == "0" ]; then
        # Создать переменную массив с названием всех гипервизоров
        HOSTS_ARR=($(ls /etc/pki/ovirt-engine/certs/ | grep -E "*ssh.cer$" | grep -v $(hostname) | sed 's/.\{8\}$//'))

        # Добавить информацию о валидности сертификатов гипервизоров
        for i in "${!HOSTS_ARR[@]}"; do
            echo -e "Срок действия сертификата (vdsmcert.pem) гипервизора\e[1;31m ${HOSTS_ARR[$i]} \e[0m"  >> certs_validity
            echo "$(openssl x509 -text -noout -in /etc/pki/ovirt-engine/certs/${HOSTS_ARR[$i]}.cer | grep -A2 Validity)" >> certs_validity
        done

        # Вывести на экран названия всех гипервизоров с численными значениями
        echo "Найденные гипервизоры:"
        for i in "${!HOSTS_ARR[@]}"; do
            echo -e "$((i+1)).\e[1;31m ${HOSTS_ARR[$i]} \e[0m"
        done

        # Запросить пользователя выбрать нужные хосты
        read -p "Выберете гипервизоры, введя их ID (1 2 5 итд 'all' - для выбора всех гипервизоров), или введите 'no' если не нужно собирать логи с гипервизороов: " user_input

        # Проверка ввода пользователя
        if [ "$user_input" != "no" ]; then
            selected_hosts=($user_input)
            read -p "Для полного сбора логов из каталога гипервизоров /var/log введите 'y' или нажмите 'Enter' для ограниченного сбора логов из каталога 'vdsm' и файла 'messages': " user_input_logtype
            if [ "$user_input_logtype" == 'y' ]; then
                # Пройтись по всем гипервизорам для сбора логов из /var/log/
                if [ "$selected_hosts" == 'all' ]; then
                    for host_id in "${HOSTS_ARR[@]}"; do
                        #index=$((host_id-1))
                        #if [ $index -ge 0 ] && [ $index -lt ${#HOSTS_ARR[@]} ]; then
                        #    HOST="${HOSTS_ARR[$index]}"
                        download_logs "$host_id"
                        #else
                        #    echo "Введен неправильный ID гипервизора: $host_id"
                        #fi
                    done
                else
                # Пройтись по всем гипервизорам из списка выбранных для сбора логов из /var/log/
                    for host_id in "${selected_hosts[@]}"; do
                        index=$((host_id-1))
                        if [ $index -ge 0 ] && [ $index -lt ${#HOSTS_ARR[@]} ]; then
                            HOST="${HOSTS_ARR[$index]}"
                                download_logs "$HOST"
                        else
                            echo "Введен неправильный ID гипервизора: $host_id"
                        fi
                    done
                fi
            else
                 # Пройтись по всем гипервизорам для сбора логов из /var/log/vdsm
                if [ "$selected_hosts" == 'all' ]; then
                    for host_id in "${HOSTS_ARR[@]}"; do
                        #index=$((host_id-1))
                        #    if [ $index -ge 0 ] && [ $index -lt ${#HOSTS_ARR[@]} ]; then
                        #        HOST="${HOSTS_ARR[$index]}"
                        download_logs_vdsm "$host_id"
                        #    else
                        #        echo "Введен неправильный ID гипервизора: $host_id"
                        #    fi
                    done
                        
                else
                    # Пройтись по всем гипервизорам из списка выбранных для сбора логов из /var/log/vdsm
                    for host_id in "${selected_hosts[@]}"; do
                        index=$((host_id-1))
                        if [ $index -ge 0 ] && [ $index -lt ${#HOSTS_ARR[@]} ]; then
                            HOST="${HOSTS_ARR[$index]}"
                                download_logs_vdsm "$HOST"
                        else
                            echo "Введен неправильный ID гипервизора: $host_id"
                        fi
                    done
                fi
            fi
                
        fi
    else
        echo "Не найдено гипервизоров" 
    fi
fi


# Перейти на уровень выше в родительскую директорию
cd ..

# Удалить архивный файл если существует
[ -f "$LOGS_DIR".tar.gz ] && rm -f "$LOGS_DIR".tar.gz

# Создать tar.gz архив из директории 'ovirt-logs-yyyymmdd'
tar -czf "$LOGS_DIR".tar.gz "$LOGS_DIR"

# Удалить деректорию 'ovirt-logs-yyyymmdd
rm -rf "$LOGS_DIR"
