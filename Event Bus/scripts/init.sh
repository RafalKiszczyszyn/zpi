#!/bin/bash

echo 'Initial Setup'

# Enable management plugin
rabbitmq-plugins enable rabbitmq_management


echo 'Clean up'
for v in $(rabbitmqctl list_vhosts --silent); do 
    rabbitmqctl delete_vhost $v 
done

for v in $(rabbitmqctl list_users --silent); do 
    rabbitmqctl delete_user $v 
done

# Create virtual hosts
rabbitmqctl add_vhost "main"
rabbitmqctl add_vhost "logging"

# Create administrator
rabbitmqctl add_user admin admin
rabbitmqctl set_user_tags admin administrator
for v in $(rabbitmqctl list_vhosts --silent) 
do 
    rabbitmqctl set_permissions -p $v "admin" ".*" ".*" ".*" 
done

# Create users
if [ -f "/var/lib/rabbitmq/scripts/mkusers.sh" ]; then
    echo 'Adding users'
    /var/lib/rabbitmq/scripts/mkusers.sh
fi
