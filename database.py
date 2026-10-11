import sqlite3
from datetime import datetime, timedelta

DB_PATH = "bot_data.db"

def init_db():
    """إنشاء جداول قاعدة البيانات إذا لم تكن موجودة."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            user_id INTEGER,
            chat_id INTEGER,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mutes (
            user_id INTEGER,
            chat_id INTEGER,
            mute_until TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_warnings(user_id: int, chat_id: int) -> int:
    """الحصول على عدد التحذيرات لمستخدم في مجموعة."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT count FROM warnings WHERE user_id = ? AND chat_id = ?",
        (user_id, chat_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_warning(user_id: int, chat_id: int) -> int:
    """إضافة تحذير وإرجاع العدد الجديد."""
    current = get_warnings(user_id, chat_id)
    new_count = current + 1
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO warnings (user_id, chat_id, count)
        VALUES (?, ?, ?)
    """, (user_id, chat_id, new_count))
    conn.commit()
    conn.close()
    return new_count

def reset_warnings(user_id: int, chat_id: int):
    """إعادة تعيين التحذيرات لمستخدم."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM warnings WHERE user_id = ? AND chat_id = ?",
        (user_id, chat_id)
    )
    conn.commit()
    conn.close()

def set_mute(user_id: int, chat_id: int, duration_minutes: int):
    """كتم مستخدم لمدة محددة."""
    mute_until = datetime.now() + timedelta(minutes=duration_minutes)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO mutes (user_id, chat_id, mute_until)
        VALUES (?, ?, ?)
    """, (user_id, chat_id, mute_until.isoformat()))
    conn.commit()
    conn.close()

def is_muted(user_id: int, chat_id: int) -> bool:
    """التحقق مما إذا كان المستخدم مكتومًا."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mute_until FROM mutes WHERE user_id = ? AND chat_id = ?",
        (user_id, chat_id)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        mute_until = datetime.fromisoformat(result[0])
        if datetime.now() < mute_until:
            return True
        else:
            # انتهت مدة الكتم، حذف السجل
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM mutes WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id)
            )
            conn.commit()
            conn.close()
    return False

def remove_mute(user_id: int, chat_id: int):
    """إلغاء كتم مستخدم."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM mutes WHERE user_id = ? AND chat_id = ?",
        (user_id, chat_id)
    )
    conn.commit()
    conn.close()
