import os
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization

def convert_p12_to_pem(p12_path, pem_path):
    try:
        with open(p12_path, 'rb') as f:
            p12_data = f.read()

        # Efí certs usually have no password or empty password
        password = None 
        
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            p12_data,
            password
        )

        with open(pem_path, 'wb') as f:
            # Write Private Key
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
            # Write Certificate
            f.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM
            ))
            
            # Write Additional Certificates (if any)
            if additional_certificates:
                for cert in additional_certificates:
                    f.write(cert.public_bytes(
                        encoding=serialization.Encoding.PEM
                    ))
        
        print(f"Successfully converted {p12_path} to {pem_path}")
        return True
    except Exception as e:
        print(f"Failed to convert {p12_path}: {e}")
        return False

def main():
    certs_dir = 'certs'
    if not os.path.exists(certs_dir):
        print(f"Directory {certs_dir} not found")
        return

    files = os.listdir(certs_dir)
    for file in files:
        if file.endswith('.p12'):
            p12_path = os.path.join(certs_dir, file)
            pem_filename = file.replace('.p12', '.pem')
            # Also create a generic name like 'homologacao.pem' if the file matches the pattern
            if 'homologacao' in file:
                pem_filename = 'homologacao.pem'
            elif 'producao' in file:
                pem_filename = 'producao.pem'
            
            pem_path = os.path.join(certs_dir, pem_filename)
            convert_p12_to_pem(p12_path, pem_path)

if __name__ == '__main__':
    main()
