import sqlite3
import pandas as pd
from datetime import datetime, timedelta

class RDSDatabase:
    def __init__(self, db_path='rds_monitoring.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create instances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rds_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT,
                engine TEXT,
                instance_class TEXT,
                status TEXT,
                allocated_storage INTEGER,
                endpoint TEXT,
                multi_az INTEGER,
                publicly_accessible INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rds_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT,
                metric_name TEXT,
                value REAL,
                timestamp DATETIME,
                FOREIGN KEY (instance_id) REFERENCES rds_instances(instance_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_instances(self, instances_df):
        """Store RDS instances information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for _, row in instances_df.iterrows():
            cursor.execute('''
                INSERT INTO rds_instances (
                    instance_id, engine, instance_class, status,
                    allocated_storage, endpoint, multi_az, publicly_accessible
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['DBInstanceIdentifier'],
                row['Engine'],
                row['DBInstanceClass'],
                row['Status'],
                row['AllocatedStorage'],
                row['Endpoint'],
                int(row['MultiAZ']),
                int(row['PubliclyAccessible'])
            ))
        
        conn.commit()
        conn.close()
    
    def store_metrics(self, instance_id, metric_name, metrics_df):
        """Store metrics data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for _, row in metrics_df.iterrows():
            cursor.execute('''
                INSERT INTO rds_metrics (
                    instance_id, metric_name, value, timestamp
                ) VALUES (?, ?, ?, ?)
            ''', (
                instance_id,
                metric_name,
                row['Value'],
                row['Timestamp']
            ))
        
        conn.commit()
        conn.close()
    
    def get_historical_instances(self, start_date, end_date):
        """Get historical instances data between dates"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM rds_instances 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        conn.close()
        return df
    
    def get_historical_metrics(self, instance_id, metric_name, start_date, end_date):
        """Get historical metrics data between dates"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM rds_metrics 
            WHERE instance_id = ? AND metric_name = ? 
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn, params=[instance_id, metric_name, start_date, end_date])
        conn.close()
        return df
    
    def get_available_instances(self):
        """Get list of unique instances in the database"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT DISTINCT instance_id FROM rds_instances
            ORDER BY instance_id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df['instance_id'].tolist()
    
    def get_available_metrics(self, instance_id):
        """Get list of available metrics for an instance"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT DISTINCT metric_name FROM rds_metrics
            WHERE instance_id = ?
            ORDER BY metric_name
        '''
        df = pd.read_sql_query(query, conn, params=[instance_id])
        conn.close()
        return df['metric_name'].tolist() 