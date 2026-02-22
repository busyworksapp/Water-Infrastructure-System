"""S3-compatible object storage service for backups and archival."""
import logging
import os
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3-compatible object storage operations (AWS S3, Linode, etc.)"""
    
    def __init__(self):
        """Initialize S3 client with Railway/Linode credentials"""
        self.enabled = bool(settings.S3_BUCKET and settings.S3_ACCESS_KEY)
        
        if not self.enabled:
            logger.warning("S3 storage not configured (S3_BUCKET or credentials missing)")
            return
        
        # S3-compatible configuration (supports AWS S3, Linode, Railway, etc.)
        client_config = {
            "region_name": settings.S3_REGION,
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
        }
        
        # Add custom endpoint URL for non-AWS S3-compatible services
        s3_resource_config = {}
        if settings.S3_ENDPOINT:
            s3_resource_config["endpoint_url"] = settings.S3_ENDPOINT
            logger.info(f"S3 endpoint configured: {settings.S3_ENDPOINT}")
        
        try:
            self.client = boto3.client("s3", **client_config)
            self.resource = boto3.resource("s3", **client_config, **s3_resource_config)
            self.bucket = self.resource.Bucket(settings.S3_BUCKET)
            
            # Test connection
            self._test_connection()
            logger.info(f"S3 service initialized for bucket: {settings.S3_BUCKET}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            self.enabled = False
    
    def _test_connection(self) -> bool:
        """Test S3 connectivity"""
        try:
            self.client.head_bucket(Bucket=settings.S3_BUCKET)
            logger.info("S3 connection test successful")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"S3 bucket not found: {settings.S3_BUCKET}")
            elif e.response['Error']['Code'] == '403':
                logger.error(f"Access denied to S3 bucket: {settings.S3_BUCKET}")
            else:
                logger.error(f"S3 connection test failed: {e}")
            return False
        except NoCredentialsError:
            logger.error("S3 credentials not found")
            return False
    
    def upload_backup(
        self,
        file_path: str,
        remote_path: Optional[str] = None,
        metadata: Optional[dict] = None,
        storage_class: str = "STANDARD_IA"
    ) -> bool:
        """
        Upload a backup file to S3
        
        Args:
            file_path: Local file path to upload
            remote_path: S3 object key (if None, uses filename)
            metadata: Custom metadata to attach
            storage_class: S3 storage class (STANDARD, STANDARD_IA, GLACIER, etc.)
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("S3 storage not enabled")
            return False
        
        if not os.path.exists(file_path):
            logger.error(f"Backup file not found: {file_path}")
            return False
        
        try:
            # Use filename if remote path not specified
            if not remote_path:
                remote_path = f"backups/{os.path.basename(file_path)}"
            
            # Prepare metadata
            extra_args = {
                "StorageClass": storage_class,
                "ServerSideEncryption": "AES256",
                "Metadata": metadata or {},
            }
            
            # Add backup timestamp to metadata
            extra_args["Metadata"]["backup-timestamp"] = datetime.utcnow().isoformat()
            
            # Upload file
            file_size = os.path.getsize(file_path)
            logger.info(f"Uploading backup to S3: {remote_path} ({file_size / 1024 / 1024:.2f} MB)")
            
            self.client.upload_file(
                file_path,
                settings.S3_BUCKET,
                remote_path,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded backup: {remote_path}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            return False
    
    def download_backup(
        self,
        remote_path: str,
        local_path: str
    ) -> bool:
        """
        Download a backup file from S3
        
        Args:
            remote_path: S3 object key
            local_path: Local destination path
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("S3 storage not enabled")
            return False
        
        try:
            logger.info(f"Downloading backup from S3: {remote_path}")
            
            self.client.download_file(
                settings.S3_BUCKET,
                remote_path,
                local_path
            )
            
            file_size = os.path.getsize(local_path)
            logger.info(f"Successfully downloaded backup: {local_path} ({file_size / 1024 / 1024:.2f} MB)")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to download backup from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
            return False
    
    def list_backups(self, prefix: str = "backups/") -> list[dict]:
        """
        List all backup files in S3
        
        Args:
            prefix: S3 key prefix to filter backups
        
        Returns:
            List of backup metadata dicts
        """
        if not self.enabled:
            return []
        
        try:
            backups = []
            response = self.client.list_objects_v2(
                Bucket=settings.S3_BUCKET,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            for obj in response['Contents']:
                backups.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "storage_class": obj.get('StorageClass', 'STANDARD'),
                })
            
            logger.info(f"Found {len(backups)} backups in S3")
            return backups
        
        except ClientError as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, remote_path: str) -> bool:
        """
        Delete a backup file from S3
        
        Args:
            remote_path: S3 object key
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            logger.info(f"Deleting backup from S3: {remote_path}")
            self.client.delete_object(Bucket=settings.S3_BUCKET, Key=remote_path)
            logger.info(f"Successfully deleted backup: {remote_path}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """
        Delete backups older than specified days
        
        Args:
            retention_days: Keep backups newer than this many days
        
        Returns:
            Number of backups deleted
        """
        if not self.enabled:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = 0
            
            backups = self.list_backups()
            
            for backup in backups:
                last_modified = datetime.fromisoformat(backup['last_modified'].replace('Z', '+00:00'))
                
                if last_modified < cutoff_date:
                    if self.delete_backup(backup['key']):
                        deleted_count += 1
            
            logger.info(f"Cleanup complete: deleted {deleted_count} old backups")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            return 0
    
    def upload_file_stream(
        self,
        file_bytes: BytesIO,
        remote_path: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file from a BytesIO stream to S3
        
        Args:
            file_bytes: BytesIO object containing file data
            remote_path: S3 object key
            metadata: Custom metadata to attach
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            logger.info(f"Uploading stream to S3: {remote_path}")
            
            extra_args = {
                "ServerSideEncryption": "AES256",
                "Metadata": metadata or {},
                "StorageClass": "STANDARD_IA",
            }
            extra_args["Metadata"]["upload-timestamp"] = datetime.utcnow().isoformat()
            
            self.client.upload_fileobj(
                file_bytes,
                settings.S3_BUCKET,
                remote_path,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded stream: {remote_path}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to upload stream: {e}")
            return False
    
    def get_backup_stats(self) -> dict:
        """
        Get statistics about backups in S3
        
        Returns:
            Dictionary with backup statistics
        """
        if not self.enabled:
            return {}
        
        try:
            backups = self.list_backups()
            total_size = sum(b['size'] for b in backups)
            
            return {
                "total_backups": len(backups),
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "oldest_backup": min((b['last_modified'] for b in backups), default=None),
                "newest_backup": max((b['last_modified'] for b in backups), default=None),
                "storage_class_distribution": self._count_storage_classes(backups),
            }
        except Exception as e:
            logger.error(f"Error getting backup stats: {e}")
            return {}
    
    def _count_storage_classes(self, backups: list[dict]) -> dict:
        """Count backups by storage class"""
        distribution = {}
        for backup in backups:
            storage_class = backup.get('storage_class', 'STANDARD')
            distribution[storage_class] = distribution.get(storage_class, 0) + 1
        return distribution


# Global S3 service instance
s3_service = S3Service()
