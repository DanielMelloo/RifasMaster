import os
import zipfile
from datetime import datetime

def create_mvp_zip():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'RifaMaster_MVP_{timestamp}.zip'
    
    # Files and directories to exclude
    excludes = {
        'dirs': {'venv', '__pycache__', '.git', '.gemini', 'instance'},
        'files': {'.env', 'rifamaster.db', zip_filename}
    }
    
    print(f"Creating MVP package: {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in excludes['dirs']]
            
            for file in files:
                if file in excludes['files'] or file.endswith('.pyc'):
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                
                print(f"Adding: {arcname}")
                zipf.write(file_path, arcname)
                
    print(f"\nMVP Package created successfully: {zip_filename}")

if __name__ == '__main__':
    create_mvp_zip()
