# app/services/alert_service.py
import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                       "Database", "stock_database.db")

class AlertService:
    
    @staticmethod
    def _get_connection():
        return sqlite3.connect(DB_PATH)
    
    @staticmethod
    def create_alert(user_id: int, alert_data: Dict) -> Dict[str, Any]:
        """Create a new alert"""
        conn = AlertService._get_connection()
        cursor = conn.cursor()
        
        try:
            # Validate alert type
            alert_type = alert_data.get('alert_type')
            
            if alert_type == 'price':
                # Price alert (e.g., "Alert me when AAPL > $200")
                cursor.execute("""
                    INSERT INTO alert 
                    (user_id, alert_name, alert_type, symbol, condition_field, 
                     condition_operator, condition_value, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    alert_data.get('alert_name', f"Price alert for {alert_data['symbol']}"),
                    'price',
                    alert_data['symbol'].upper(),
                    'current_price',
                    alert_data['operator'],
                    alert_data['value'],
                    alert_data.get('notes')
                ))
                
            elif alert_type == 'growth':
                # Growth alert (e.g., "Alert when revenue growth > 15%")
                cursor.execute("""
                    INSERT INTO alert 
                    (user_id, alert_name, alert_type, symbol, condition_field, 
                     condition_operator, condition_value, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    alert_data.get('alert_name', f"Growth alert for {alert_data['symbol']}"),
                    'growth',
                    alert_data['symbol'].upper(),
                    alert_data.get('metric', 'revenue_growth'),
                    alert_data['operator'],
                    alert_data['value'],
                    alert_data.get('notes')
                ))
                
            elif alert_type == 'screener':
                # Screener alert (e.g., "Alert when new stocks match this criteria")
                cursor.execute("""
                    INSERT INTO alert 
                    (user_id, alert_name, alert_type, screener_dsl, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    alert_data.get('alert_name', 'Screener alert'),
                    'screener',
                    json.dumps(alert_data['dsl']),
                    alert_data.get('notes')
                ))
            
            else:
                raise ValueError(f"Unknown alert type: {alert_type}")
            
            alert_id = cursor.lastrowid
            conn.commit()
            
            return {
                "status": "success",
                "message": f"Alert created successfully",
                "alert_id": alert_id
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_alerts(user_id: int, alert_type: str = None, is_active: bool = None) -> List[Dict]:
        """Get user's alerts"""
        conn = AlertService._get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM alert WHERE user_id = ?"
            params = [user_id]
            
            if alert_type:
                query += " AND alert_type = ?"
                params.append(alert_type)
            
            if is_active is not None:
                query += " AND is_active = ?"
                params.append(1 if is_active else 0)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            alerts = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            result = []
            for alert in alerts:
                alert_dict = dict(zip(columns, alert))
                # Parse JSON fields
                if alert_dict.get('screener_dsl'):
                    alert_dict['screener_dsl'] = json.loads(alert_dict['screener_dsl'])
                result.append(alert_dict)
            
            return result
            
        finally:
            conn.close()
    
    @staticmethod
    def delete_alert(alert_id: int, user_id: int) -> Dict[str, Any]:
        """Delete an alert"""
        conn = AlertService._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM alert WHERE id = ? AND user_id = ?",
                (alert_id, user_id)
            )
            
            if cursor.rowcount == 0:
                raise ValueError(f"Alert {alert_id} not found")
            
            conn.commit()
            
            return {
                "status": "success",
                "message": f"Alert {alert_id} deleted successfully"
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def toggle_alert(alert_id: int, user_id: int, is_active: bool) -> Dict[str, Any]:
        """Enable or disable an alert"""
        conn = AlertService._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE alert 
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (1 if is_active else 0, alert_id, user_id))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Alert {alert_id} not found")
            
            conn.commit()
            
            return {
                "status": "success",
                "message": f"Alert {'enabled' if is_active else 'disabled'} successfully"
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def check_alerts(user_id: int = None) -> List[Dict]:
        """Check all active alerts and trigger if conditions met"""
        conn = AlertService._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get active alerts
            query = """
                SELECT * FROM alert 
                WHERE is_active = 1 
                AND (last_triggered IS NULL OR frequency != 'once')
            """
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            cursor.execute(query, params)
            alerts = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            triggered_alerts = []
            
            for alert in alerts:
                alert_dict = dict(zip(columns, alert))
                
                # Check if alert condition is met
                is_triggered = AlertService._evaluate_alert(alert_dict)
                
                if is_triggered:
                    # Update alert trigger count
                    cursor.execute("""
                        UPDATE alert 
                        SET last_triggered = CURRENT_TIMESTAMP,
                            trigger_count = trigger_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (alert_dict['id'],))
                    
                    triggered_alerts.append({
                        "alert_id": alert_dict['id'],
                        "alert_name": alert_dict['alert_name'],
                        "alert_type": alert_dict['alert_type'],
                        "symbol": alert_dict.get('symbol'),
                        "message": AlertService._get_alert_message(alert_dict)
                    })
            
            conn.commit()
            
            return triggered_alerts
            
        finally:
            conn.close()
    
    @staticmethod
    def _evaluate_alert(alert: Dict) -> bool:
        """Evaluate if alert condition is met"""
        
        alert_type = alert['alert_type']
        
        if alert_type == 'price':
            # Get current price
            current_price = AlertService._get_current_price(alert['symbol'])
            condition_value = alert['condition_value']
            operator = alert['condition_operator']
            
            # Evaluate condition
            if operator == '>':
                return current_price > condition_value
            elif operator == '<':
                return current_price < condition_value
            elif operator == '>=':
                return current_price >= condition_value
            elif operator == '<=':
                return current_price <= condition_value
            elif operator == '==':
                return current_price == condition_value
            else:
                return False
                
        elif alert_type == 'growth':
            # Get growth metrics (simplified)
            growth = AlertService._get_growth_metric(alert['symbol'], alert['condition_field'])
            condition_value = alert['condition_value']
            operator = alert['condition_operator']
            
            if operator == '>':
                return growth > condition_value
            elif operator == '<':
                return growth < condition_value
            else:
                return False
                
        elif alert_type == 'screener':
            # Execute saved screener query
            dsl = alert['screener_dsl']
            # This would call your screener service
            # results = run_screener(dsl)
            # return len(results) > 0
            return False  # Placeholder
            
        return False
    
    @staticmethod
    def _get_current_price(symbol: str) -> float:
        """Get current price (simulated)"""
        prices = {
            "AAPL": 175.50, "MSFT": 330.25, "GOOGL": 140.75,
            "AMZN": 145.80, "TSLA": 250.30, "NVDA": 890.50
        }
        return prices.get(symbol, 100.00)
    
    @staticmethod
    def _get_growth_metric(symbol: str, metric: str) -> float:
        """Get growth metric (simulated)"""
        growth_rates = {
            "AAPL": 12.5, "MSFT": 18.3, "GOOGL": 15.2,
            "AMZN": 22.1, "TSLA": 35.4, "NVDA": 85.6
        }
        return growth_rates.get(symbol, 10.0)
    
    @staticmethod
    def _get_alert_message(alert: Dict) -> str:
        """Generate alert message"""
        if alert['alert_type'] == 'price':
            current_price = AlertService._get_current_price(alert['symbol'])
            return f"🔔 {alert['symbol']} is now ${current_price} ({alert['condition_operator']} ${alert['condition_value']})"
        elif alert['alert_type'] == 'growth':
            growth = AlertService._get_growth_metric(alert['symbol'], alert['condition_field'])
            return f"📈 {alert['symbol']} growth is {growth}% ({alert['condition_operator']} {alert['condition_value']}%)"
        else:
            return f"🔔 Alert triggered: {alert['alert_name']}"