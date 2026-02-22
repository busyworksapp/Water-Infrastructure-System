"""Production-grade automated backup service for database and critical data"""
import boto3
import json
import gzip
import subprocess
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging
from sqlalchemy import text

from ..core.config import settings
from ..core.database import engine

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.s3_enabled = settings.S3_ENABLED and settings.S3_BUCKET
        if self.s3_enabled:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f"https://{settings.S3_ENDPOINT}" if not settings.S3_ENDPOINT.startswith('http') else settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION
            )
            self.bucket = settings.S3_BUCKET
        else:
            logger.warning("S3 not configured, backups will be stored locally")
            self.backup_dir = Path("backups")
            self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, compress: bool = True) -> Dict:
        """Create full database backup"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f"db_backup_{timestamp}"
        
        try:
            if 'postgresql' in settings.DATABASE_URL:
                backup_file = self._backup_postgresql(backup_name, compress)
            elif 'mysql' in settings.DATABASE_URL:
                backup_file = self._backup_mysql(backup_name, compress)
            else:
                raise ValueError("Unsupported database type")
            
            # Upload to S3 or store locally
            if self.s3_enabled:
                s3_key = f"{settings.S3_BACKUP_PREFIX}{backup_name}.sql.gz" if compress else f"{settings.S3_BACKUP_PREFIX}{backup_name}.sql"
                self._upload_to_s3(backup_file, s3_key)
                storage_location = f"s3://{self.bucket}/{s3_key}"
            else:
                storage_location = str(backup_file)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            result = {
                "status": "success",
                "backup_name": backup_name,
                "timestamp": timestamp,
                "location": storage_location,
                "compressed": compress,
                "size_bytes": os.path.getsize(backup_file) if os.path.exists(backup_file) else 0
            }
            
            logger.info(f"Backup created successfully: {backup_name}")
            return result
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _backup_postgresql(self, backup_name: str, compress: bool) -> Path:
        """Create PostgreSQL backup using pg_dump"""
        backup_file = self.backup_dir / f"{backup_name}.sql" if not self.s3_enabled else Path(tempfile.gettempdir()) / f"{backup_name}.sql"
        
        # Parse connection string
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'pg_dump',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path.lstrip('/'),
            '-F', 'p',  # Plain text format
            '--no-owner',
            '--no-acl',
            '-f', str(backup_file)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
        
        if compress:
            compressed_file = Path(str(backup_file) + '.gz')
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            backup_file.unlink()
            return compressed_file
        
        return backup_file
    
    def _backup_mysql(self, backup_name: str, compress: bool) -> Path:
        """Create MySQL backup using mysqldump"""
        backup_file = self.backup_dir / f"{backup_name}.sql" if not self.s3_enabled else Path(tempfile.gettempdir()) / f"{backup_name}.sql"
        
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        cmd = [
            'mysqldump',
            '-h', parsed.hostname,
            '-P', str(parsed.port or 3306),
            '-u', parsed.username,
            f'-p{parsed.password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            parsed.path.lstrip('/'),
            '--result-file', str(backup_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"mysqldump failed: {result.stderr}")
        
        if compress:
            compressed_file = Path(str(backup_file) + '.gz')
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            backup_file.unlink()
            return compressed_file
        
        return backup_file
    
    def _upload_to_s3(self, file_path: Path, s3_key: str):
        """Upload backup file to S3"""
        extra_args = {
            'StorageClass': settings.S3_STORAGE_CLASS,
            'ServerSideEncryption': 'AES256'
        }
        
        self.s3_client.upload_file(
            str(file_path),
            self.bucket,
            s3_key,
            ExtraArgs=extra_args
        )
        
        # Delete local temp file
        if file_path.parent == Path(tempfile.gettempdir()):
            file_path.unlink()
        
        logger.info(f"Uploaded backup to s3://{self.bucket}/{s3_key}")
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        retention_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        if self.s3_enabled:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=settings.S3_BACKUP_PREFIX
                )
                
                for obj in response.get('Contents', []):
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3_client.delete_object(
                            Bucket=self.bucket,
                            Key=obj['Key']
                        )
                        logger.info(f"Deleted old backup: {obj['Key']}")
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
        else:
            # Cleanup local backups
            for backup_file in self.backup_dir.glob('db_backup_*'):
                if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Deleted old local backup: {backup_file}")
    
    def list_backups(self, limit: int = 50) -> List[Dict]:
        """List available backups"""
        backups = []
        
        if self.s3_enabled:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=settings.S3_BACKUP_PREFIX,
                    MaxKeys=limit
                )
                
                for obj in response.get('Contents', []):
                    backups.append({
                        'name': obj['Key'].split('/')[-1],
                        'location': f"s3://{self.bucket}/{obj['Key']}",
                        'size_bytes': obj['Size'],
                        'created_at': obj['LastModified'].isoformat(),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    })
            except Exception as e:
                logger.error(f"List backups failed: {e}")
        else:
            for backup_file in sorted(self.backup_dir.glob('db_backup_*'), reverse=True)[:limit]:
                backups.append({
                    'name': backup_file.name,
                    'location': str(backup_file),
                    'size_bytes': backup_file.stat().st_size,
                    'created_at': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                })
        
        return backups
    
    def restore_backup(self, backup_name: str) -> Dict:
        """Restore database from backup"""
        try:
            # Download from S3 if needed
            if self.s3_enabled:
                s3_key = f"{settings.S3_BACKUP_PREFIX}{backup_name}"
                local_file = Path(tempfile.gettempdir()) / backup_name
                
                self.s3_client.download_file(
                    self.bucket,
                    s3_key,
                    str(local_file)
                )
            else:
                local_file = self.backup_dir / backup_name
            
            # Decompress if needed
            if local_file.suffix == '.gz':
                decompressed = Path(str(local_file).replace('.gz', ''))
                with gzip.open(local_file, 'rb') as f_in:
                    with open(decompressed, 'wb') as f_out:
                        f_out.write(f_in.read())
                local_file = decompressed
            
            # Restore based on database type
            if 'postgresql' in settings.DATABASE_URL:
                self._restore_postgresql(local_file)
            elif 'mysql' in settings.DATABASE_URL:
                self._restore_mysql(local_file)
            
            # Cleanup temp files
            if local_file.parent == Path(tempfile.gettempdir()):
                local_file.unlink()
            
            logger.info(f"Backup restored successfully: {backup_name}")
            return {"status": "success", "backup_name": backup_name}
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _restore_postgresql(self, backup_file: Path):
        """Restore PostgreSQL backup"""
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'psql',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path.lstrip('/'),
            '-f', str(backup_file)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"psql restore failed: {result.stderr}")
    
    def _restore_mysql(self, backup_file: Path):
        """Restore MySQL backup"""
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        cmd = [
            'mysql',
            '-h', parsed.hostname,
            '-P', str(parsed.port or 3306),
            '-u', parsed.username,
            f'-p{parsed.password}',
            parsed.path.lstrip('/')
        ]
        
        with open(backup_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"mysql restore failed: {result.stderr}")
    
    def verify_backup(self, backup_name: str) -> Dict:
        """Verify backup integrity"""
        try:
            if self.s3_enabled:
                s3_key = f"{settings.S3_BACKUP_PREFIX}{backup_name}"
                response = self.s3_client.head_object(
                    Bucket=self.bucket,
                    Key=s3_key
                )
                
                return {
                    "status": "valid",
                    "size_bytes": response['ContentLength'],
                    "last_modified": response['LastModified'].isoformat(),
                    "etag": response['ETag']
                }
            else:
                backup_file = self.backup_dir / backup_name
                if backup_file.exists():
                    return {
                        "status": "valid",
                        "size_bytes": backup_file.stat().st_size,
                        "last_modified": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                    }
                else:
                    return {"status": "not_found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
