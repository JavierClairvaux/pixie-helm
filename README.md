# pixie-helm

How to use:

1. Install pixie:
```
./bash -c "$(curl -fsSL https://withpixie.ai/install.sh)"
```

2. Run python script to generate helm chart:
```
python3 px-helm.py <cluster name>
```

For example:
```
python3 px-helm.py test
```

The name defaults to demo if you don't provide any name.

3. Install helm chart:
```
helm install  example ./pixie-helm-<cluster name>
```

For example:
```
helm install  example ./pixie-helm-test
```
