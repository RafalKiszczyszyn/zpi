import os
import shutil
import subprocess
import json
import pathlib
from abc import ABC, abstractmethod


BASE = pathlib.Path(__file__).resolve().parent
ROOT_KEY = 'root'
CA = 'ca'


def get_details(name):
    return f'/C=PL/ST=Dolny slask/L=Wroclaw/O=ZPI/OU=/CN=ZPI@{name}/emailAddress=246655@student.pwr.edu.pl'


class IOperation(ABC):

    @abstractmethod
    def perform(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class Transaction:

    def __init__(self) -> None:
        self.operations = []

    def perform(self, operation: IOperation):
        self.operations.append(operation)
        operation.perform()

    def rollback(self):
        for operation in reversed(self.operations):
            try:
                operation.undo()
            except Exception:
                pass


class ChDir(IOperation):

    def __init__(self, path) -> None:
        self.cwd = os.getcwd()
        self.path = path

    def perform(self):
        os.chdir(self.path)

    def undo(self):
        os.chdir(self.cwd)


class MkDir(IOperation):

    def __init__(self, name) -> None:
        self.name = name

    def perform(self):
        os.mkdir(self.name)

    def undo(self):
        os.rmdir(self.name)


class CopyFile(IOperation):

    def __init__(self, source, destination) -> None:
        self.source = source
        self.destination = destination

    def perform(self):
        shutil.copy(self.source, self.destination)

    def undo(self):
        os.remove(self.destination)


class MkFile(IOperation):

    def __init__(self, name) -> None:
        self.name = name

    def perform(self):
        open(self.name, 'w').close()

    def undo(self):
        os.remove(self.name)


class GenerateKey(IOperation):

    def __init__(self, name) -> None:
        self.name = name

    def perform(self):
        result = subprocess.run(f'openssl genrsa -out {self.name}.key 2048')
        if result.returncode != 0:
            raise Exception('Generating key with openssl failed')

    def undo(self):
        os.remove(f"{self.name}.key")

class GenerateCa(IOperation):

    def __init__(self, key, name) -> None:
        self.key = key
        self.name = name

    def perform(self):
        details = get_details('root')
        cmd = f'openssl req -nodes -x509 -key {self.key}.key -out {self.name}.pem -subj "{details}"'
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise Exception('Generating certificate authority with openssl failed')

    def undo(self):
        os.remove(f"{self.name}.pem")


class GenerateCsr(IOperation):

    def __init__(self, key, name) -> None:
        self.key = key
        self.name = name

    def perform(self):
        details = get_details(self.name)
        result = subprocess.run(f'openssl req -new -key {self.key}.key -out {self.name}.csr -subj "{details}"')
        if result.returncode != 0:
            raise Exception('Generating certificate signing request with openssl failed')

    def undo(self):
        os.remove(f"{self.name}.csr")


class GenerateCrt(IOperation):

    def __init__(self, ca, rootKey, name) -> None:
        self.ca = ca
        self.rootKey = rootKey
        self.name = name

    def perform(self):
        cmd = f"openssl x509 -req -in {self.name}.csr -CA {self.ca}.pem -CAkey {self.rootKey}.key -CAcreateserial -out {self.name}.crt -days 3600 -sha256"
        print(cmd)
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise Exception('Generating certificate with openssl failed')

    def undo(self):
        os.remove(f"{self.name}.crt")
        os.remove(f"{self.ca}.srl")


def loadProfiles():
    profiles_ = os.path.join(BASE, 'profiles.json')
    
    print(f"[INFO] Loading profiles from path='{profiles_}'")
    with open(profiles_, 'r') as file:
        profiles = json.load(file)
    meta = profiles['meta']
    meta['root'] = pathlib.Path(meta['root']).resolve()
    services = profiles['services']
    print(f"[INFO] Loaded {len(services)} profiles")

    return services, meta


def initSslContext(transaction: Transaction):
    print(f"[INFO] Generating {ROOT_KEY}")
    transaction.perform(GenerateKey(ROOT_KEY))
    print(f"[INFO] Generated {ROOT_KEY}")

    print(f"[INFO] Gerating {CA}")
    transaction.perform(GenerateCa(ROOT_KEY, CA))
    print(f"[INFO] Generated {CA}")


def buildSslContext(serviceName: str, buildPath: str, transaction: Transaction):
    print(f"[INFO] Building service='{serviceName}' ssl context")
    
    sslContext = os.path.join(buildPath, 'ssl')
    if not os.path.exists(sslContext):
        transaction.perform(MkDir(sslContext))

    transaction.perform(GenerateKey(name=serviceName))
    transaction.perform(GenerateCsr(key=serviceName, name=serviceName))
    transaction.perform(GenerateCrt(ca=CA, rootKey=ROOT_KEY, name=serviceName))

    transaction.perform(CopyFile(CA + '.pem', os.path.join(sslContext, CA + '.pem')))
    transaction.perform(CopyFile(serviceName + '.key', os.path.join(sslContext, serviceName + '.key')))
    transaction.perform(CopyFile(serviceName + '.csr', os.path.join(sslContext, serviceName + '.csr')))
    transaction.perform(CopyFile(serviceName + '.crt', os.path.join(sslContext, serviceName + '.crt')))


def buildUserProfile(service: dict) -> str:
    serviceName = service['name']
    print(f"[INFO] Building service='{serviceName}' user profile")
    
    credentials = service['credentials'].split(':')
    userProfile = f'\nrabbitmqctl add_user "{credentials[0]}" "{credentials[1]}"'

    privateResources = [r'amq\.gen.*', rf'{serviceName}\..*']
    for permissions in service['permissions']:
        configure = privateResources + permissions['publish']
        write = privateResources + permissions['publish']
        read = privateResources + permissions['consume']

        configure = f'^({"|".join(configure)})$'
        write = f'^({"|".join(write)})$'
        read = f'^({"|".join(read)})$'

        userProfile += f'\nrabbitmqctl set_permissions -p "{permissions["vhost"]}" "{credentials[0]}" "{configure}" "{write}" "{read}"'
    
    return userProfile

def build(transaction: Transaction):
    transaction.perform(ChDir(BASE))
    services, meta = loadProfiles()    

    if not os.path.exists('temp'):
        transaction.perform(MkDir('temp'))
    transaction.perform(ChDir('temp'))

    initSslContext(transaction)

    # Build broker
    buildPath = os.path.join(meta['root'], pathlib.Path(meta['buildPath']).resolve())
    buildSslContext('rabbitmq', buildPath, transaction)
    
    userProfiles = '#!/bin/bash\n'
    # Build each service
    for service in services:    
        path = os.path.join(meta['root'], pathlib.Path(service['buildPath']).resolve())
        buildSslContext(service['name'], path, transaction)

        userProfiles += buildUserProfile(service)
    
    scripts = os.path.join(buildPath, 'scripts')
    if not os.path.exists(scripts):
        transaction.perform(MkDir(scripts))

    transaction.perform(MkFile('mkusers.sh'))
    with open('mkusers.sh', 'w', newline='\n') as f:
        f.write(userProfiles)
    transaction.perform(CopyFile('mkusers.sh', os.path.join(scripts, 'mkusers.sh')))


def main():
    print('[INFO] With transaction')
    transaction = Transaction()
    try:
        build(transaction)
        answer = input('Commit? [Y|n]')
        if answer.lower() == 'n':
            transaction.rollback()
    except Exception as e:
        print(f'[ERROR] {e}')
        print('[INFO] Rolling back')
        transaction.rollback()

if __name__ == '__main__':
    main()
