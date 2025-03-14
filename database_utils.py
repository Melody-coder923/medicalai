#sqlite3 is package to create and manage sqllite database
import sqlite3
import os

DATABASE_FILE = 'user_database.db' # 数据库文件名

def create_database():
    """创建数据库和表格"""
    conn = sqlite3.connect(DATABASE_FILE) # 连接到数据库，如果文件不存在会自动创建
    cursor = conn.cursor() # 创建游标，用于执行 SQL 命令

    # 创建 users 表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            age INTEGER,
            gender TEXT,
            height TEXT,
            weight TEXT,
            profile_photo_path TEXT
        )
    ''')

    # 创建 lab_reports 表格 ,外键，关联到 users 表的 id  (这是 Python 注释，解释下面的 SQL 代码)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            report_file_name TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit() # 提交更改，保存表格创建
    conn.close() # 关闭数据库连接

# 检查数据库文件是否存在，如果不存在就创建
if not os.path.exists(DATABASE_FILE):
    create_database()
    print("Database 'user_database.db' and tables created.")
else:
    print("Database 'user_database.db' already exists.")
    
def add_user(first_name, age, gender, height, weight, profile_photo_path):
#添加新用户到 users 表格
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (first_name, age, gender, height, weight, profile_photo_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (first_name, age, gender, height, weight, profile_photo_path)) # 使用参数化查询，防止 SQL 注入
    conn.commit()
    conn.close()

def get_user(user_id):
#根据 user_id 从 users 表格获取用户信息
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users WHERE id = ?
    ''', (user_id,))
    user = cursor.fetchone() # 获取一条记录
    conn.close()
    return user # 返回一个 tuple，包含用户信息，如果没有找到用户返回 None

def update_user(user_id, first_name, age, gender, height, weight, profile_photo_path):
#更新 users 表格中的用户信息
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET first_name = ?, age = ?, gender = ?, height = ?, weight = ?, profile_photo_path = ?
        WHERE id = ?
    ''', (first_name, age, gender, height, weight, profile_photo_path, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
#从 users 表格删除用户 (注意要先删除相关的 lab_reports)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # 先删除相关的 lab_reports (级联删除，cascade delete 也可以在数据库层面设置，这里为了简单手动删除)
    cursor.execute('''DELETE FROM lab_reports WHERE user_id = ?''', (user_id,))
    cursor.execute('''DELETE FROM users WHERE id = ?''', (user_id,))
    conn.commit()
    conn.close()

def add_lab_report(user_id, report_file_name):
#为用户添加实验报告到 lab_reports 表格
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lab_reports (user_id, report_file_name)
        VALUES (?, ?)
    ''', (user_id, report_file_name))
    conn.commit()
    conn.close()

def get_lab_reports_for_user(user_id):
#获取指定用户的所有实验报告
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM lab_reports WHERE user_id = ?
    ''', (user_id,))
    reports = cursor.fetchall() # 获取所有记录
    conn.close()
    return reports # 返回一个 list of tuples，每个 tuple 是一条 lab_report 记录

def delete_lab_report(report_id):
#根据 report_id 从 lab_reports 表格删除实验报告
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM lab_reports WHERE id = ?
    ''', (report_id,))
    conn.commit()
    conn.close()

# (仍然在文件末尾)
if __name__ == "__main__":
# 测试代码 (仅在直接运行 database_utils.py 时执行)
    create_database() # 确保数据库和表格存在

    # 添加一个用户
    add_user("Alice", 30, "Female", "165cm", "55kg", "alice.jpg")
    add_user("Bob", 35, "Male", "175cm", "70kg", "bob.png")

    # 获取用户 Alice 的信息
    alice_user = get_user(1) # Alice 的 id 是 1
    print("Alice's info:", alice_user)

    # 为 Alice 添加一个实验报告
    add_lab_report(1, "alice_lab_report_1.pdf")
    add_lab_report(1, "alice_lab_report_2.docx")

    # 获取 Alice 的所有实验报告
    alice_reports = get_lab_reports_for_user(1)
    print("Alice's reports:", alice_reports)

    # 更新 Bob 的年龄
    update_user(2, "Bob", 36, "Male", "175cm", "70kg", "bob.png")
    bob_user = get_user(2)
    print("Updated Bob's info:", bob_user)

    # 删除 Alice 的一个实验报告 (假设第一个报告的 id 是 1, 需要根据实际情况调整)
    delete_lab_report(1)
    alice_reports_after_delete = get_lab_reports_for_user(1)
    print("Alice's reports after deleting one:", alice_reports_after_delete)

    # 删除 Bob 用户
    delete_user(2)
    bob_user_after_delete = get_user(2)
    print("Bob's info after delete:", bob_user_after_delete) # 应该返回 None
    bob_reports_after_delete_user = get_lab_reports_for_user(2) # Bob 的报告也应该被删除
    print("Bob's reports after user delete:", bob_reports_after_delete_user) # 应该返回 []