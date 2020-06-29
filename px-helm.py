import subprocess
import re
import yaml
import os
import sys
import errno
import logging
import shutil

logger = logging.getLogger('default')
logger.setLevel(logging.DEBUG)

PX_BINARY_PATH = '/usr/local/bin/px'

def dumptoyaml(path, values):
    stream = open(path, 'w')
    yaml.dump(values, stream)
    stream.close()

def readyaml(path):
    stream = open(path, 'r')
    json_yaml = yaml.safe_load(stream)
    stream.close()
    return json_yaml


def parseargs():
    if len(sys.argv) == 1:
        return "demo"
    elif len(sys.argv) == 2:
        return sys.argv[1]
    else:
        logger.error('No more than one argument!')
        exit()


def main():
    kname = parseargs()
    logger.info("Getting deploy key!")
    proc = subprocess.Popen(
        [PX_BINARY_PATH, 'deploy-key', 'create'],
        stderr=subprocess.PIPE
    )
    key = proc.stderr.read()
    key = re.split(r'\s', key.decode('utf-8'))[-2]
    key = key.strip('"')
    subprocess.run([
         PX_BINARY_PATH,
         'deploy',
         '--extract_yaml',
         './',
         '--deploy_key',
         key
    ])
    subprocess.run(['tar', '-xvf', './yamls.tar'])

    fs = open('./pixie_yamls/01_secrets/02_secret.yaml', 'r')
    slines = fs.read()
    fs.close()
    files = slines.split('---')
    kpattern = 'name: pl-deploy-secrets'

    for f in files:
        if kpattern in f:
            kYaml = f
            kline = files.index(f)

    files.pop(kline)


    # Creating helm chart
    logger.debug("Creating Helm Chart!")
    helm_dir = "./pixie-helm-"+kname
    template_dir = helm_dir+"/templates/"
    try:
        os.mkdir(helm_dir)
        os.mkdir(template_dir)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        logger.debug("pixie-helm-", kname, " dir already exists!")
        pass

    ySecret = open(template_dir+'deploy-key.yml', 'w')
    ySecret.write(kYaml)
    ySecret.close()

    secret = readyaml(template_dir+'deploy-key.yml')
    secret['data']['deploy-key'] = "{{ .Values.deployKey.key | b64enc }}"

    dumptoyaml(template_dir+'deploy-key.yml', secret)

    for f in files:
        if 'PL_CLUSTER_NAME' in f:
            nYaml = f
            nline = files.index(f)

    files.pop(nline)
    fs_new = open(template_dir+'02_secret_new.yaml', 'w+')
    for f in files:
        fs_new.write('---\n')
        fs_new.write(f)
    fs_new.close() 

    shutil.copy("./pixie_yamls/00_namespace/00_namespace.yaml", template_dir)
    shutil.copy("./pixie_yamls/01_secrets/01_secret.yaml", template_dir)
    shutil.copy("./pixie_yamls/02_manifests/03_bootstrap.yaml", template_dir)

    config_map = open(template_dir+'pl-cloud-config.yml', 'w')
    config_map.write(nYaml)
    config_map.close()

    config = readyaml(template_dir+'pl-cloud-config.yml')

    config['data']['PL_CLUSTER_NAME'] = "{{ .Values.plCloudName.name }}"

    dumptoyaml(template_dir+'pl-cloud-config.yml', config)

    values = {
            'deployKey': {'key': key},
            'plCloudName': {'name': kname},
            'replicaCount': 1
            }

    dumptoyaml(helm_dir+'/values.yaml', values)

    proc_app = subprocess.Popen([PX_BINARY_PATH, "version"], stdout=subprocess.PIPE)
    appv = proc_app.stdout.read()

    chart = {
        'apiVersion': 'v2',
        'name': 'pixie-helm',
        'description': 'A Helm chart for deploying Pixie',
        'type': 'application',
        'version': '1.0',
        'appVersion': appv.decode('utf-8').split('+')[0]
    }
    chart['name'] = chart['name']+"-"+kname
    dumptoyaml(helm_dir+'/Chart.yaml', chart)
    logger.debug('Done!')


if __name__ == '__main__':
    main()
