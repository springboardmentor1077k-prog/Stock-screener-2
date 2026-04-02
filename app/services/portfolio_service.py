# app/services/portfolio_service.py
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                       "Database", "stock_database.db")

class PortfolioService:
    
    @staticmethod
    def _get_connection():
        """Get database connection"""
        return sqlite3.connect(DB_PATH)
    
    @staticmethod
    def add_stock(user_id: int, symbol: str, quantity: int, price: float, notes: str = None) -> Dict[str, Any]:
        """Add stock to portfolio or update existing holding"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get company_id from symbol
            cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol.upper(),))
            company_row = cursor.fetchone()
            
            if not company_row:
                raise ValueError(f"Company with symbol {symbol} not found")
            
            company_id = company_row[0]
            
            # Check if stock already exists in portfolio
            cursor.execute(
                "SELECT id, quantity, average_price FROM portfolio WHERE user_id = ? AND company_id = ?",
                (user_id, company_id)
            )
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing holding
                portfolio_id = existing[0]
                old_quantity = existing[1]
                old_avg_price = existing[2]
                
                # Calculate new average price
                total_cost = (old_quantity * old_avg_price) + (quantity * price)
                new_quantity = old_quantity + quantity
                new_avg_price = total_cost / new_quantity
                
                cursor.execute("""
                    UPDATE portfolio 
                    SET quantity = ?, average_price = ?, last_updated = CURRENT_TIMESTAMP, notes = ?
                    WHERE id = ?
                """, (new_quantity, new_avg_price, notes, portfolio_id))
                
                # Record transaction
                cursor.execute("""
                    INSERT INTO portfolio_transactions 
                    (portfolio_id, transaction_type, quantity, price, total_value, notes)
                    VALUES (?, 'BUY', ?, ?, ?, ?)
                """, (portfolio_id, quantity, price, quantity * price, notes))
                
                message = f"Added {quantity} shares to existing {symbol} position"
                
            else:
                # Insert new stock
                cursor.execute("""
                    INSERT INTO portfolio 
                    (user_id, company_id, symbol, quantity, average_price, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, company_id, symbol.upper(), quantity, price, notes))
                
                portfolio_id = cursor.lastrowid
                
                # Record transaction
                cursor.execute("""
                    INSERT INTO portfolio_transactions 
                    (portfolio_id, transaction_type, quantity, price, total_value, notes)
                    VALUES (?, 'BUY', ?, ?, ?, ?)
                """, (portfolio_id, quantity, price, quantity * price, notes))
                
                message = f"Added {symbol} to portfolio"
            
            conn.commit()
            
            # Get updated portfolio stats
            stats = PortfolioService.get_portfolio_summary(user_id)
            
            return {
                "status": "success",
                "message": message,
                "portfolio_stats": stats
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def remove_stock(user_id: int, symbol: str, quantity: Optional[int] = None) -> Dict[str, Any]:
        """Remove stock from portfolio (full or partial sell)"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get portfolio details
            cursor.execute("""
                SELECT p.id, p.quantity, p.average_price, s.symbol
                FROM portfolio p
                JOIN symbols s ON p.company_id = s.id
                WHERE p.user_id = ? AND s.symbol = ?
            """, (user_id, symbol.upper()))
            
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Stock {symbol} not found in portfolio")
            
            portfolio_id, current_quantity, avg_price, stock_symbol = result
            
            # Determine quantity to sell
            sell_quantity = quantity if quantity else current_quantity
            
            if sell_quantity > current_quantity:
                raise ValueError(f"Cannot sell {sell_quantity} shares. Only {current_quantity} available")
            
            # Get current market price (simulated)
            current_price = PortfolioService._get_current_price(stock_symbol)
            
            if sell_quantity == current_quantity:
                # Full sell - delete record
                cursor.execute("DELETE FROM portfolio WHERE id = ?", (portfolio_id,))
                message = f"Fully removed {stock_symbol} from portfolio"
            else:
                # Partial sell - update quantity
                new_quantity = current_quantity - sell_quantity
                cursor.execute("""
                    UPDATE portfolio 
                    SET quantity = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (new_quantity, portfolio_id))
                message = f"Sold {sell_quantity} shares of {stock_symbol}"
            
            # Record sell transaction
            cursor.execute("""
                INSERT INTO portfolio_transactions 
                (portfolio_id, transaction_type, quantity, price, total_value, notes)
                VALUES (?, 'SELL', ?, ?, ?, ?)
            """, (portfolio_id, sell_quantity, current_price, sell_quantity * current_price, 
                  f"Sold at {current_price}"))
            
            conn.commit()
            
            # Get updated portfolio stats
            stats = PortfolioService.get_portfolio_summary(user_id)
            
            return {
                "status": "success",
                "message": message,
                "sell_details": {
                    "symbol": stock_symbol,
                    "quantity": sell_quantity,
                    "price": current_price,
                    "value": round(sell_quantity * current_price, 2)
                },
                "portfolio_stats": stats
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_portfolio(user_id: int, include_transactions: bool = False) -> Dict[str, Any]:
        """Get user's portfolio with current valuations"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all holdings
            cursor.execute("""
                SELECT 
                    p.id,
                    p.symbol,
                    s.company_name,
                    s.sector,
                    p.quantity,
                    p.average_price,
                    p.purchase_date,
                    p.notes
                FROM portfolio p
                JOIN symbols s ON p.symbol = s.symbol
                WHERE p.user_id = ?
                ORDER BY p.purchase_date DESC
            """, (user_id,))
            
            holdings = cursor.fetchall()
            
            total_investment = 0
            total_current_value = 0
            portfolio_details = []
            
            for holding in holdings:
                # Get current price
                current_price = PortfolioService._get_current_price(holding[1])
                
                invested = holding[5] * holding[4]  # avg_price * quantity
                current_val = current_price * holding[4]
                profit_loss = current_val - invested
                profit_loss_pct = (profit_loss / invested * 100) if invested > 0 else 0
                
                total_investment += invested
                total_current_value += current_val
                
                portfolio_details.append({
                    "id": holding[0],
                    "symbol": holding[1],
                    "company_name": holding[2],
                    "sector": holding[3],
                    "quantity": holding[4],
                    "average_price": round(holding[5], 2),
                    "purchase_date": holding[6],
                    "notes": holding[7],
                    "current_price": round(current_price, 2),
                    "invested_value": round(invested, 2),
                    "current_value": round(current_val, 2),
                    "profit_loss": round(profit_loss, 2),
                    "profit_loss_percentage": round(profit_loss_pct, 2)
                })
            
            total_profit_loss = total_current_value - total_investment
            total_profit_loss_pct = (total_profit_loss / total_investment * 100) if total_investment > 0 else 0
            
            result = {
                "status": "success",
                "user_id": user_id,
                "summary": {
                    "total_investment": round(total_investment, 2),
                    "total_current_value": round(total_current_value, 2),
                    "total_profit_loss": round(total_profit_loss, 2),
                    "total_profit_loss_percentage": round(total_profit_loss_pct, 2),
                    "number_of_stocks": len(portfolio_details)
                },
                "holdings": portfolio_details
            }
            
            # Include transaction history if requested
            if include_transactions:
                result["transactions"] = PortfolioService.get_transaction_history(user_id)
            
            return result
            
        finally:
            conn.close()
    
    @staticmethod
    def get_portfolio_summary(user_id: int) -> Dict[str, Any]:
        """Get portfolio summary statistics only"""
        portfolio = PortfolioService.get_portfolio(user_id)
        return portfolio["summary"]
    
    @staticmethod
    def get_transaction_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's transaction history"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    pt.transaction_type,
                    p.symbol,
                    pt.quantity,
                    pt.price,
                    pt.total_value,
                    pt.transaction_date,
                    pt.notes
                FROM portfolio_transactions pt
                JOIN portfolio p ON pt.portfolio_id = p.id
                WHERE p.user_id = ?
                ORDER BY pt.transaction_date DESC
                LIMIT ?
            """, (user_id, limit))
            
            transactions = cursor.fetchall()
            
            return [
                {
                    "type": t[0],
                    "symbol": t[1],
                    "quantity": t[2],
                    "price": round(t[3], 2),
                    "total_value": round(t[4], 2),
                    "date": t[5],
                    "notes": t[6]
                }
                for t in transactions
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def add_to_watchlist(user_id: int, symbol: str, alert_price: float = None, notes: str = None) -> Dict[str, Any]:
        """Add stock to watchlist"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get company_id
            cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol.upper(),))
            company_row = cursor.fetchone()
            
            if not company_row:
                raise ValueError(f"Company with symbol {symbol} not found")
            
            company_id = company_row[0]
            
            # Add to watchlist
            cursor.execute("""
                INSERT OR REPLACE INTO watchlist 
                (user_id, company_id, symbol, alert_price, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, company_id, symbol.upper(), alert_price, notes))
            
            conn.commit()
            
            return {
                "status": "success",
                "message": f"Added {symbol} to watchlist"
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_watchlist(user_id: int) -> Dict[str, Any]:
        """Get user's watchlist"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    w.symbol,
                    s.company_name,
                    s.sector,
                    w.alert_price,
                    w.added_at,
                    w.notes
                FROM watchlist w
                JOIN symbols s ON w.symbol = s.symbol
                WHERE w.user_id = ?
                ORDER BY w.added_at DESC
            """, (user_id,))
            
            watchlist_items = cursor.fetchall()
            
            return {
                "status": "success",
                "watchlist": [
                    {
                        "symbol": item[0],
                        "company_name": item[1],
                        "sector": item[2],
                        "alert_price": item[3],
                        "added_at": item[4],
                        "notes": item[5]
                    }
                    for item in watchlist_items
                ]
            }
            
        finally:
            conn.close()
    
    @staticmethod
    def remove_from_watchlist(user_id: int, symbol: str) -> Dict[str, Any]:
        """Remove stock from watchlist"""
        conn = PortfolioService._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM watchlist 
                WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol.upper()))
            
            conn.commit()
            
            return {
                "status": "success",
                "message": f"Removed {symbol} from watchlist"
            }
            
        finally:
            conn.close()
    
    @staticmethod
    def _get_current_price(symbol: str) -> float:
        """Get current price for a symbol (simulated for demo)"""
        # In production, fetch from real API like Alpha Vantage, Yahoo Finance, etc.
        simulated_prices = {
            "AAPL": 175.50,
            "MSFT": 330.25,
            "GOOGL": 140.75,
            "AMZN": 145.80,
            "TSLA": 250.30,
            "META": 310.20,
            "NVDA": 890.50,
            "JPM": 195.40,
            "NFLX": 620.30,
            "IBM": 185.60
        }
        
        return simulated_prices.get(symbol.upper(), 100.00)

# Add this to your app/services/portfolio_service.py

@staticmethod
def create_snapshot(user_id: int) -> Dict[str, Any]:
    """Create a performance snapshot of current portfolio"""
    conn = PortfolioService._get_connection()
    cursor = conn.cursor()
    
    try:
        # Get current portfolio summary
        summary = PortfolioService.get_portfolio_summary(user_id)
        
        # Insert snapshot
        cursor.execute("""
            INSERT INTO portfolio_snapshots 
            (user_id, total_investment, total_current_value, total_profit_loss, profit_loss_percentage)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            summary['total_investment'],
            summary['total_current_value'],
            summary['total_profit_loss'],
            summary['total_profit_loss_percentage']
        ))
        
        conn.commit()
        
        return {
            "status": "success",
            "message": "Snapshot created successfully",
            "snapshot": {
                "date": datetime.now().isoformat(),
                "total_investment": summary['total_investment'],
                "total_current_value": summary['total_current_value'],
                "profit_loss": summary['total_profit_loss'],
                "profit_loss_percentage": summary['total_profit_loss_percentage']
            }
        }
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@staticmethod
def get_snapshots(user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    """Get historical snapshots"""
    conn = PortfolioService._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                snapshot_date,
                total_investment,
                total_current_value,
                total_profit_loss,
                profit_loss_percentage
            FROM portfolio_snapshots
            WHERE user_id = ?
            ORDER BY snapshot_date DESC
            LIMIT ?
        """, (user_id, limit))
        
        snapshots = cursor.fetchall()
        
        return [
            {
                "date": s[0],
                "total_investment": round(s[1], 2),
                "total_current_value": round(s[2], 2),
                "profit_loss": round(s[3], 2),
                "profit_loss_percentage": round(s[4], 2)
            }
            for s in snapshots
        ]
        
    finally:
        conn.close()