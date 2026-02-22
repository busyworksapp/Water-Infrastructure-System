# Database Entity-Relationship Diagram

## National Water Infrastructure Monitoring System

---

## Core Entities

### 1. Municipality
**Purpose**: Multi-tenant isolation for different municipalities

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Municipality name |
| code | VARCHAR(50) | UNIQUE, NOT NULL | Municipality code |
| region | VARCHAR(100) | | Geographic region |
| contact_email | VARCHAR(255) | | Contact email |
| contact_phone | VARCHAR(50) | | Contact phone |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Relationships**:
- ONE municipality → MANY users
- ONE municipality → MANY sensors
- ONE municipality → MANY pipelines
- ONE municipality → MANY alerts
- ONE municipality → MANY incidents

---

### 2. User
**Purpose**: System users with authentication and authorization

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Login username |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(255) | | Full name |
| municipality_id | UUID | FK → Municipality | Associated municipality |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| is_super_admin | BOOLEAN | DEFAULT FALSE | Super admin flag |
| last_login | TIMESTAMP | | Last login timestamp |
| created_at | TIMESTAMP | DEFAULT NOW() | Account creation |
| updated_at | TIMESTAMP | | Last update |

**Relationships**:
- MANY users → ONE municipality
- MANY users → MANY roles (via user_roles)
- ONE user → MANY audit_logs
- ONE user → ONE user_preference

---

### 3. Role
**Purpose**: Role definitions for RBAC

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Role name |
| description | TEXT | | Role description |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Relationships**:
- MANY roles → MANY users (via user_roles)
- MANY roles → MANY permissions (via role_permissions)

---

### 4. Permission
**Purpose**: Granular permissions for access control

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| resource | VARCHAR(100) | NOT NULL | Resource name |
| action | VARCHAR(50) | NOT NULL | Action (read/write/delete) |
| description | TEXT | | Permission description |

**Relationships**:
- MANY permissions → MANY roles (via role_permissions)

---

### 5. SensorType
**Purpose**: Dynamic sensor type definitions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(100) | PK | Type identifier |
| name | VARCHAR(255) | NOT NULL | Display name |
| unit | VARCHAR(50) | | Measurement unit |
| min_value | FLOAT | | Minimum valid value |
| max_value | FLOAT | | Maximum valid value |
| description | TEXT | | Type description |
| icon | VARCHAR(100) | | Icon identifier |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Relationships**:
- ONE sensor_type → MANY sensors

---

### 6. Sensor
**Purpose**: IoT sensor device registry

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(100) | PK | Device identifier |
| name | VARCHAR(255) | NOT NULL | Sensor name |
| sensor_type_id | VARCHAR(100) | FK → SensorType | Sensor type |
| municipality_id | UUID | FK → Municipality | Owner municipality |
| pipeline_id | UUID | FK → Pipeline | Associated pipeline |
| latitude | FLOAT | | GPS latitude |
| longitude | FLOAT | | GPS longitude |
| altitude | FLOAT | | Altitude (meters) |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| last_reading_at | TIMESTAMP | | Last data received |
| baseline_mean | FLOAT | | Statistical baseline mean |
| baseline_std | FLOAT | | Statistical baseline std dev |
| baseline_min | FLOAT | | Baseline minimum |
| baseline_max | FLOAT | | Baseline maximum |
| metadata | JSONB | | Additional metadata |
| created_at | TIMESTAMP | DEFAULT NOW() | Installation date |
| updated_at | TIMESTAMP | | Last update |

**Relationships**:
- MANY sensors → ONE municipality
- MANY sensors → ONE sensor_type
- MANY sensors → ONE pipeline (optional)
- ONE sensor → MANY sensor_readings
- ONE sensor → MANY alerts

---

### 7. SensorReading
**Purpose**: Time-series sensor data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PK | Unique identifier |
| sensor_id | VARCHAR(100) | FK → Sensor, INDEXED | Sensor reference |
| value | FLOAT | NOT NULL | Measured value |
| unit | VARCHAR(50) | | Measurement unit |
| timestamp | TIMESTAMP | NOT NULL, INDEXED | Reading timestamp |
| quality_score | FLOAT | DEFAULT 1.0 | Data quality (0-1) |
| is_anomaly | BOOLEAN | DEFAULT FALSE | Anomaly flag |
| anomaly_score | FLOAT | | Anomaly confidence |
| anomaly_method | VARCHAR(50) | | Detection method |
| metadata | JSONB | | Additional data |
| created_at | TIMESTAMP | DEFAULT NOW() | Ingestion time |

**Indexes**:
- (sensor_id, timestamp DESC)
- (timestamp DESC)
- (is_anomaly, timestamp DESC)

**Relationships**:
- MANY readings → ONE sensor

---

### 8. Pipeline
**Purpose**: Water pipeline infrastructure with GIS

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Pipeline name |
| municipality_id | UUID | FK → Municipality | Owner municipality |
| geometry | GEOMETRY(LineString) | PostGIS | Pipeline route |
| diameter | FLOAT | | Pipe diameter (mm) |
| material | VARCHAR(100) | | Pipe material |
| installation_date | DATE | | Installation date |
| length_km | FLOAT | | Pipeline length |
| max_pressure | FLOAT | | Max pressure rating |
| status | VARCHAR(50) | | Operational status |
| metadata | JSONB | | Additional metadata |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMP | | Last update |

**Spatial Index**: GIST(geometry)

**Relationships**:
- MANY pipelines → ONE municipality
- ONE pipeline → MANY sensors

---

### 9. Alert
**Purpose**: Real-time alert management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| municipality_id | UUID | FK → Municipality | Target municipality |
| sensor_id | VARCHAR(100) | FK → Sensor | Related sensor |
| pipeline_id | UUID | FK → Pipeline | Related pipeline |
| alert_type | VARCHAR(100) | NOT NULL | Alert type |
| severity | VARCHAR(20) | NOT NULL | critical/high/medium/low |
| title | VARCHAR(255) | NOT NULL | Alert title |
| description | TEXT | | Detailed description |
| status | VARCHAR(50) | DEFAULT 'active' | active/acknowledged/resolved |
| acknowledged_by | UUID | FK → User | User who acknowledged |
| acknowledged_at | TIMESTAMP | | Acknowledgment time |
| resolved_by | UUID | FK → User | User who resolved |
| resolved_at | TIMESTAMP | | Resolution time |
| metadata | JSONB | | Additional data |
| created_at | TIMESTAMP | DEFAULT NOW() | Alert creation |

**Indexes**:
- (municipality_id, status, created_at DESC)
- (sensor_id, created_at DESC)
- (severity, status)

**Relationships**:
- MANY alerts → ONE municipality
- MANY alerts → ONE sensor (optional)
- MANY alerts → ONE pipeline (optional)

---

### 10. Incident
**Purpose**: Incident tracking and management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| municipality_id | UUID | FK → Municipality | Municipality |
| alert_id | UUID | FK → Alert | Related alert |
| title | VARCHAR(255) | NOT NULL | Incident title |
| description | TEXT | | Detailed description |
| incident_type | VARCHAR(100) | | Incident category |
| severity | VARCHAR(20) | | Severity level |
| status | VARCHAR(50) | DEFAULT 'open' | Incident status |
| location | GEOMETRY(Point) | PostGIS | Incident location |
| reported_by | UUID | FK → User | Reporter |
| assigned_to | UUID | FK → User | Assigned user |
| resolved_at | TIMESTAMP | | Resolution time |
| resolution_notes | TEXT | | Resolution details |
| created_at | TIMESTAMP | DEFAULT NOW() | Report time |
| updated_at | TIMESTAMP | | Last update |

**Relationships**:
- MANY incidents → ONE municipality
- MANY incidents → ONE alert (optional)

---

### 11. MaintenanceLog
**Purpose**: Maintenance activity tracking

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| municipality_id | UUID | FK → Municipality | Municipality |
| sensor_id | VARCHAR(100) | FK → Sensor | Related sensor |
| pipeline_id | UUID | FK → Pipeline | Related pipeline |
| maintenance_type | VARCHAR(100) | | Type of maintenance |
| description | TEXT | | Activity description |
| performed_by | UUID | FK → User | Technician |
| scheduled_date | DATE | | Scheduled date |
| completed_date | DATE | | Completion date |
| status | VARCHAR(50) | | Status |
| cost | DECIMAL(10,2) | | Maintenance cost |
| notes | TEXT | | Additional notes |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation |

**Relationships**:
- MANY maintenance_logs → ONE municipality
- MANY maintenance_logs → ONE sensor (optional)
- MANY maintenance_logs → ONE pipeline (optional)

---

### 12. DeviceAuthentication
**Purpose**: IoT device security and authentication

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| device_id | VARCHAR(100) | UNIQUE, NOT NULL | Device identifier |
| api_key | VARCHAR(255) | UNIQUE | API key |
| certificate_fingerprint | VARCHAR(255) | | TLS cert fingerprint |
| certificate_expiry | TIMESTAMP | | Certificate expiration |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| last_used | TIMESTAMP | | Last authentication |
| created_at | TIMESTAMP | DEFAULT NOW() | Registration date |

**Relationships**:
- ONE device_auth → ONE sensor (via device_id)

---

### 13. AuditLog
**Purpose**: System audit trail

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PK | Unique identifier |
| user_id | UUID | FK → User | User who performed action |
| action | VARCHAR(100) | NOT NULL | Action type |
| resource | VARCHAR(100) | | Affected resource |
| resource_id | VARCHAR(100) | | Resource identifier |
| details | JSONB | | Action details |
| ip_address | VARCHAR(50) | | Client IP |
| user_agent | TEXT | | Client user agent |
| timestamp | TIMESTAMP | DEFAULT NOW(), INDEXED | Action timestamp |

**Indexes**:
- (user_id, timestamp DESC)
- (timestamp DESC)
- (action, timestamp DESC)

**Relationships**:
- MANY audit_logs → ONE user

---

### 14. DynamicRule
**Purpose**: Configurable alert rules

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| municipality_id | UUID | FK → Municipality | Target municipality |
| sensor_type_id | VARCHAR(100) | FK → SensorType | Applicable sensor type |
| rule_name | VARCHAR(255) | NOT NULL | Rule name |
| condition | JSONB | NOT NULL | Rule condition |
| threshold | FLOAT | | Threshold value |
| severity | VARCHAR(20) | | Alert severity |
| is_active | BOOLEAN | DEFAULT TRUE | Rule active status |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |
| updated_at | TIMESTAMP | | Last update |

**Relationships**:
- MANY rules → ONE municipality
- MANY rules → ONE sensor_type

---

### 15. NotificationChannel
**Purpose**: Multi-channel notification configuration

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| municipality_id | UUID | FK → Municipality | Municipality |
| channel_type | VARCHAR(50) | NOT NULL | email/sms/webhook/push |
| name | VARCHAR(255) | NOT NULL | Channel name |
| config | JSONB | NOT NULL | Channel configuration |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |

**Relationships**:
- MANY channels → ONE municipality

---

### 16. SystemSettings
**Purpose**: Dynamic system configuration

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| key | VARCHAR(255) | UNIQUE, NOT NULL | Setting key |
| value | JSONB | NOT NULL | Setting value |
| description | TEXT | | Setting description |
| is_public | BOOLEAN | DEFAULT FALSE | Public visibility |
| updated_at | TIMESTAMP | | Last update |

---

### 17. UserPreference
**Purpose**: User-specific preferences

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK → User, UNIQUE | User reference |
| theme | VARCHAR(50) | DEFAULT 'dark' | UI theme |
| language | VARCHAR(10) | DEFAULT 'en' | Language |
| timezone | VARCHAR(50) | | User timezone |
| notification_settings | JSONB | | Notification preferences |
| dashboard_layout | JSONB | | Custom dashboard |
| updated_at | TIMESTAMP | | Last update |

**Relationships**:
- ONE preference → ONE user

---

## Junction Tables

### user_roles
| Column | Type | Constraints |
|--------|------|-------------|
| user_id | UUID | FK → User, PK |
| role_id | UUID | FK → Role, PK |

### role_permissions
| Column | Type | Constraints |
|--------|------|-------------|
| role_id | UUID | FK → Role, PK |
| permission_id | UUID | FK → Permission, PK |

---

## Indexes Summary

### Performance Indexes
- sensor_readings(sensor_id, timestamp DESC)
- sensor_readings(timestamp DESC)
- alerts(municipality_id, status, created_at DESC)
- audit_logs(timestamp DESC)

### Spatial Indexes
- pipelines GIST(geometry)
- incidents GIST(location)

### Unique Constraints
- users(username), users(email)
- municipalities(code)
- device_authentication(device_id)
- system_settings(key)

---

## Data Retention Policies

| Table | Retention | Archive Strategy |
|-------|-----------|------------------|
| sensor_readings | 90 days | Move to cold storage |
| audit_logs | 365 days | Compress and archive |
| alerts (resolved) | 180 days | Archive to S3 |
| incidents (closed) | 730 days | Long-term storage |

---

**Generated**: 2024-01-15  
**Database**: PostgreSQL 15+ with PostGIS 3.3+  
**ORM**: SQLAlchemy 2.0+
