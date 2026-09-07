import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_connection():
    return sqlite3.connect("expenses.db")

def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()

def get_expenses(user_id, search="", sort="newest", month="", limit=10, offset=0):
    connection = get_connection()
    cursor = connection.cursor()
    
    sort_options = {
        "newest": "date DESC",
        "oldest": "date ASC",
        "amount_desc": "amount DESC",
        "amount_asc": "amount ASC",
        "category_asc": "category ASC",
        "category_desc": "category DESC"
    }
    
    order_by = sort_options.get(sort, "date DESC")
    
    query = """
            SELECT id, category, amount, date
            FROM expenses
            WHERE user_id = ? 
            AND category LIKE ?
            """
    params = [user_id, f"%{search}%"]
    
    if month:
        query += """
            AND strftime('%Y-%m', date) = ?
            """
        params.append(month)
     
    query += f"""
        ORDER BY {order_by} 
        LIMIT ?
        OFFSET ?
        """
    params.append(limit)
    params.append(offset)
    
    cursor.execute(query, params)
              
    expenses = cursor.fetchall()

    connection.close()

    return expenses           

def add_expense(user_id, category, amount):
    connection = get_connection()
    cursor = connection.cursor()
           
    cursor.execute(
        """
        INSERT INTO expenses (user_id, category, amount, date)
        VALUES (?, ?, ?,DATETIME('now', 'localtime'))
        """, (user_id, category, amount)
        )
    
    connection.commit()
    connection.close()
             
def get_total(user_id, month=""):
    connection = get_connection()
    cursor = connection.cursor()
    
    query = """ 
            SELECT SUM(amount) FROM expenses
            where user_id = ?
            """
    params = [user_id]
    
    if month: 
        query += """ 
                AND strftime('%Y-%m', date) = ?
                """
        params.append(month)               
        
    cursor.execute(query, params)
    
    total = cursor.fetchone()[0]
    connection.close()
    
    if total is None:
        return 0
    
    return total

def get_expense_by_id(expense_id, user_id):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute(
        """
        SELECT id, category, amount, date
        FROM expenses
        WHERE id = ? AND user_id = ?
        """, (expense_id, user_id)
    )
    expense = cursor.fetchone()
    connection.close()
    return expense
    
def edit_expense(expense_id, user_id, category, amount, date):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute(
        """
        UPDATE expenses
        SET category = ?, amount = ?, date = ?
        WHERE id = ? AND user_id = ?
        """, (category, amount, date, expense_id, user_id)
    )
    
    connection.commit()
    connection.close()
    
def delete_expense(expense_id, user_id):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id = ? 
        AND user_id = ?
        """, (expense_id, user_id)
    )
    
    deleted = cursor.rowcount
    
    connection.commit()
    connection.close()
        
    return deleted    

def get_spending_by_category(user_id, month=""):
    connection = get_connection()
    cursor = connection.cursor()
    
    query = """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            """
                             
    params = [user_id]
    
    if month:
        query += """AND strftime('%Y-%m', date) = ?"""
        params.append(month)
        
    query += """GROUP BY category 
                ORDER BY total DESC""" 
                        
    cursor.execute(query, params)
            
    spending_by_category = cursor.fetchall()
    connection.close()
    return spending_by_category

def get_highest_spending_category(user_id, month=""):
    connection = get_connection()
    cursor = connection.cursor()
    
    query = """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            """
    params = [user_id]

    if month:
        query += """
            AND strftime('%Y-%m', date) = ?
                """
        params.append(month)

    query += """GROUP BY category 
                ORDER BY total DESC
                LIMIT 1"""
    
    cursor.execute(query, params)
    
    highest_category = cursor.fetchone()
    
    connection.close()
    
    return highest_category

def get_expense_count(user_id, month="", search=""):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
            SELECT COUNT(*)
            FROM expenses
            WHERE user_id = ?
            AND category LIKE ?
            """
    params = [user_id,f"%{search}%"]

    if month:
        query += """
        AND strftime('%Y-%m', date) = ?
        """
        params.append(month)

    cursor.execute(query, params)
    
    count = cursor.fetchone()[0]

    connection.close()

    return count

def get_largest_expense(user_id, month=""):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
            SELECT MAX(amount)
            FROM expenses
            WHERE user_id = ?
            """
    params = [user_id]

    if month:
        query += """ AND strftime('%Y-%m', date) = ? """
        params.append(month)

    cursor.execute(query, params)
    
    largest = cursor.fetchone()[0]

    connection.close()

    if largest is None:
        return 0

    return largest

def get_average_expense(user_id, month=""):
    connection = get_connection()
    cursor = connection.cursor()
    
    query = """
            SELECT AVG(amount)
            FROM expenses
            WHERE user_id = ?
            """
    params = [user_id]

    if month:
        query += """
            AND strftime('%Y-%m', date) = ?
            """
        params.append(month)

    cursor.execute(query, params)
    
    average = cursor.fetchone()[0]
    
    connection.close()
    
    if average is None:
            return 0
    
    return average

def register_user(username, password_hash):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?,?)
        """,(username, password_hash)
    )
    
    connection.commit()
    connection.close()
  
def get_user_by_username(username):   
    connection = get_connection()
    cursor = connection.cursor()
        
    cursor.execute( 
       """
       SELECT id ,username, password_hash
       FROM users
       WHERE username = ?
       """, (username,)
    )
    
    user = cursor.fetchone()
    
    connection.close()
    
    return user
    
    
    
    
    
    