import subprocess, re, yaml

proc = subprocess.Popen( ['/usr/local/bin/px', 'deploy-key', 'create'],  stderr=subprocess.PIPE )
key = proc.stderr.read()
key = re.split( r'\s', key.decode('utf-8') )[-2]
key = key.strip('"')
subprocess.run( ['/home/javier-c/bin/px', 'deploy', '--extract_yaml', './', '--deploy_key', key ])
subprocess.run(['tar', '-xvf', './yamls.tar'])

fs = open('./pixie_yamls/01_secrets/03_secret.yaml', 'r')
slines = fs.read()
fs.close()
files = slines.split('---')
kpattern = 'name: pl-deploy-secrets'

for f in files:
    if kpattern in f:
        kYaml = f

ySecret = open('./templates/deploy-key.yml', 'w')
ySecret.write(kYaml)
ySecret.close()

sstream = open('./templates/deploy-key.yml', 'r')
secret = yaml.safe_load(sstream)
sstream.close()
secret['data']['deploy-key'] = "{{ .Values.deployKey.key | b64enc }}"

sstream = open('./templates/deploy-key.yml', 'w')
yaml.dump(secret, sstream)
sstream.close()

for f in files:
    if 'PL_CLUSTER_NAME' in f:
        nYaml = f

config_map = open('./templates/pl-cloud-config.yml', 'w')
config_map.write(nYaml)
config_map.close()

cstream = open('./templates/pl-cloud-config.yml', 'r')
config = yaml.safe_load(cstream)
cstream.close()

config['data']['PL_CLUSTER_NAME'] = "{{ .Values.plCloudName.name }}"

config_map = open('./templates/pl-cloud-config.yml', 'w')
yaml.dump(config, config_map)
config_map.close()

kname = "demo"
vstream = open('./values.yaml', 'r')
values = yaml.safe_load(vstream)
vstream.close()
values['deployKey']['key'] = key
values['plCloudName']['name'] = kname

vstream = open('./values.yaml', 'w')
yaml.dump(values, vstream)
vstream.close()
print('Done!')
