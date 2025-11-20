import os

path = 'certs/homologacao.pem'
if os.path.exists(path):
    print(f"File exists: {path}")
    with open(path, 'rb') as f:
        content = f.read()
        print(f"Size: {len(content)}")
        print(f"Start: {content[:20]}")
else:
    print(f"File NOT found: {path}")
