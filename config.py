import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البوت
MAX_WARNINGS = 3  # عدد التحذيرات قبل الحظر
DEFAULT_MUTE_DURATION = 60  # مدة الكتم الافتراضية بالدقائق

# الكلمات الممنوعة (يمكنك إضافة المزيد)
BAD_WORDS = {
    "كلب", "حمار", "غبي", "تافه", "حقير", "قذر"
}
