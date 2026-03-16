import os
import shutil
import json
import sqlite3
from datetime import datetime
import zipfile

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')

def create_backup():
    """Create a backup of the database and configuration"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'backup_{timestamp}.zip')

    with zipfile.ZipFile(backup_file, 'w') as zipf:
        # Backup database
        db_path = os.path.join(os.path.dirname(__file__), 'toolboxgalaxy.db')
        if os.path.exists(db_path):
            zipf.write(db_path, 'toolboxgalaxy.db')

        # Backup configuration files
        config_files = ['config.ini', 'requirements.txt']
        for config in config_files:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config)
            if os.path.exists(config_path):
                zipf.write(config_path, config)

    return backup_file

def restore_backup(backup_file):
    """Restore from a backup file"""
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    # Stop the Flask application (if running)
    # You might need to implement this based on your deployment

    with zipfile.ZipFile(backup_file, 'r') as zipf:
        # Restore database
        db_path = os.path.join(os.path.dirname(__file__), 'toolboxgalaxy.db')
        if 'toolboxgalaxy.db' in zipf.namelist():
            with open(db_path, 'wb') as f:
                f.write(zipf.read('toolboxgalaxy.db'))

        # Restore configuration files
        for config in zipf.namelist():
            if config != 'toolboxgalaxy.db':
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config)
                with open(config_path, 'wb') as f:
                    f.write(zipf.read(config))

def list_backups():
    """List all available backups"""
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backups = []
    for file in os.listdir(BACKUP_DIR):
        if file.startswith('backup_') and file.endswith('.zip'):
            path = os.path.join(BACKUP_DIR, file)
            timestamp = datetime.strptime(file[7:-4], '%Y%m%d_%H%M%S')
            size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
            backups.append({
                'filename': file,
                'path': path,
                'timestamp': timestamp,
                'size': round(size, 2)
            })
    
    return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
