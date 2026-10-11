import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
import database as db

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء."""
    await update.message.reply_text(
        "👋 مرحبًا! أنا بوت إدارة المجموعات.\n"
        "الأوامر المتاحة:\n"
        "/warn - تحذير مستخدم (ردًا على رسالته)\n"
        "/mute [دقائق] - كتم مستخدم\n"
        "/unmute - إلغاء الكتم\n"
        "/ban - حظر مستخدم\n"
        "/warnings - عرض عدد التحذيرات\n"
        "/reset - إعادة تعيين التحذيرات"
    )


async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر التحذير: /warn (يجب أن يكون ردًا على رسالة)."""
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يجب الرد على رسالة المستخدم لتحذيره.")
        return
    
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # التحقق من أن المستخدم ليس مشرفًا
    member = await context.bot.get_chat_member(chat_id, user.id)
    if member.status in ["administrator", "creator"]:
        await update.message.reply_text("❌ لا يمكن تحذير المشرفين.")
        return
    
    count = db.add_warning(user.id, chat_id)
    await update.message.reply_text(
        f"⚠️ تم تحذير {user.mention_html()}.\n"
        f"عدد التحذيرات: {count}/{config.MAX_WARNINGS}",
        parse_mode="HTML"
    )
    
    if count >= config.MAX_WARNINGS:
        # حظر المستخدم
        await context.bot.ban_chat_member(chat_id, user.id)
        await update.message.reply_text(
            f"🚫 تم حظر {user.mention_html()} بسبب تجاوز الحد الأقصى للتحذيرات.",
            parse_mode="HTML"
        )
        db.reset_warnings(user.id, chat_id)


async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الكتم: /mute [دقائق] (ردًا على رسالة)."""
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يجب الرد على رسالة المستخدم لكتمه.")
        return
    
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # تحديد المدة
    duration = config.DEFAULT_MUTE_DURATION
    if context.args:
        try:
            duration = int(context.args[0])
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال مدة صحيحة بالدقائق.")
            return
    
    # كتم المستخدم
    permissions = ChatPermissions(can_send_messages=False)
    await context.bot.restrict_chat_member(chat_id, user.id, permissions)
    db.set_mute(user.id, chat_id, duration)
    
    await update.message.reply_text(
        f"🔇 تم كتم {user.mention_html()} لمدة {duration} دقيقة.",
        parse_mode="HTML"
    )


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر إلغاء الكتم."""
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يجب الرد على رسالة المستخدم لإلغاء كتمه.")
        return
    
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    await context.bot.restrict_chat_member(chat_id, user.id, permissions)
    db.remove_mute(user.id, chat_id)
    
    await update.message.reply_text(
        f"🔊 تم إلغاء كتم {user.mention_html()}.",
        parse_mode="HTML"
    )


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الحظر: /ban (ردًا على رسالة)."""
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يجب الرد على رسالة المستخدم لحظره.")
        return
    
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    await context.bot.ban_chat_member(chat_id, user.id)
    db.reset_warnings(user.id, chat_id)
    
    await update.message.reply_text(
        f"🚫 تم حظر {user.mention_html()}.",
        parse_mode="HTML"
    )


async def warnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض عدد التحذيرات."""
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user = update.effective_user
    
    chat_id = update.effective_chat.id
    count = db.get_warnings(user.id, chat_id)
    
    await update.message.reply_text(
        f"📊 عدد تحذيرات {user.mention_html()}: {count}/{config.MAX_WARNINGS}",
        parse_mode="HTML"
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تعيين التحذيرات (للمشرفين فقط)."""
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ يجب الرد على رسالة المستخدم.")
        return
    
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    db.reset_warnings(user.id, chat_id)
    await update.message.reply_text(
        f"✅ تم إعادة تعيين تحذيرات {user.mention_html()}.",
        parse_mode="HTML"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل: كشف الكلمات الممنوعة والسبام."""
    if not update.message or not update.message.text:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    # التحقق من الكتم
    if db.is_muted(user_id, chat_id):
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # كشف الكلمات الممنوعة
    for bad_word in config.BAD_WORDS:
        if bad_word in text:
            try:
                await update.message.delete()
            except:
                pass
            
            count = db.add_warning(user_id, chat_id)
            await context.bot.send_message(
                chat_id,
                f"⚠️ تم حذف رسالة {update.effective_user.mention_html()} لاحتواءها على كلمة ممنوعة.\n"
                f"عدد التحذيرات: {count}/{config.MAX_WARNINGS}",
                parse_mode="HTML"
            )
            
            if count >= config.MAX_WARNINGS:
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.send_message(
                    chat_id,
                    f"🚫 تم حظر {update.effective_user.mention_html()} تلقائيًا.",
                    parse_mode="HTML"
                )
                db.reset_warnings(user_id, chat_id)
            return


def main():
    """تشغيل البوت."""
    db.init_db()
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("warn", warn_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("warnings", warnings_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # معالجة الرسائل العادية
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    print("🤖 البوت يعمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
