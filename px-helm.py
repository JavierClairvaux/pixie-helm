import subprocess
import re
import yaml
import os
import sys
import errno
import logging

logger = logging.getLogger('default')
logger.setLevel(logging.DEBUG)


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
        ['/usr/local/bin/px', 'deploy-key', 'create'],
        stderr=subprocess.PIPE
    )
    key = proc.stderr.read()
    key = re.split(r'\s', key.decode('utf-8'))[-2]
    key = key.strip('"')
    subprocess.run([
         '/usr/local/bin/px',
         'deploy',
         '--extract_yaml',
         './',
         '--deploy_key',
         key
    ])
    subprocess.run(['tar', '-xvf', './yamls.tar'])

    fs = open('./pixie_yamls/01_secrets/03_secret.yaml', 'r')
    slines = fs.read()
    fs.close()
    files = slines.split('---')
    kpattern = 'name: pl-deploy-secrets'

    for f in files:
        if kpattern in f:
            kYaml = f

    # Creating helm chart
    logger.debug("Creating Helm Chart!")
    helm_dir = "./pixie-helm-"+kname
    try:
        os.mkdir(helm_dir)
        os.mkdir(helm_dir+"/templates")
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        logger.debug("pixie-helm-", kname, " dir already exists!")
        pass

    ySecret = open(helm_dir+'/templates/deploy-key.yml', 'w')
    ySecret.write(kYaml)
    ySecret.close()

    sstream = open(helm_dir+'/templates/deploy-key.yml', 'r')
    secret = yaml.safe_load(sstream)
    sstream.close()
    secret['data']['deploy-key'] = "{{ .Values.deployKey.key | b64enc }}"

    sstream = open(helm_dir+'/templates/deploy-key.yml', 'w')
    yaml.dump(secret, sstream)
    sstream.close()

    for f in files:
        if 'PL_CLUSTER_NAME' in f:
            nYaml = f

    config_map = open(helm_dir+'/templates/pl-cloud-config.yml', 'w')
    config_map.write(nYaml)
    config_map.close()

    cstream = open(helm_dir+'/templates/pl-cloud-config.yml', 'r')
    config = yaml.safe_load(cstream)
    cstream.close()

    config['data']['PL_CLUSTER_NAME'] = "{{ .Values.plCloudName.name }}"

    config_map = open(helm_dir+'/templates/pl-cloud-config.yml', 'w')
    yaml.dump(config, config_map)
    config_map.close()

    values = {
            'deployKey': {'key': key},
            'plCloudName': {'name': kname},
            'replicaCount': 1
            }
    # values['deployKey']['key'] = key
    # values['plCloudName']['name'] = kname

    vstream = open(helm_dir+'/values.yaml', 'w')
    yaml.dump(values, vstream)
    vstream.close()

    chart = {
        'apiVersion': 'v2',
        'name': 'pixie-helm',
        'description': 'A Helm chart for deploying Pixie',
        'type': 'application',
        'version': '0.1.0',
        'appVersion': '1.16.0'
    }
    chart['name'] = chart['name']+"-"+kname
    cstream = open(helm_dir+'/Chart.yaml', 'w')
    yaml.dump(chart, cstream)
    cstream.close()
    logger.debug('Done!')


if __name__ == '__main__':
    main()
