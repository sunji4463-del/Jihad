"""
Trusted Sell Zone — Telegram Shop Bot
=====================================
একটি সাধারণ (generic) Telegram শপ-বট টেমপ্লেট।
ফিচার: Admin Panel, Buy Product, Deposit Money, Refer, My Product,
My Profile, Check Data, Support, My ID, About

লাইব্রেরি: python-telegram-bot v22.7+
ইনস্টল: pip install -U "python-telegram-bot>=22.7,<23"

🎨 নোট: Telegram Bot API-এর নতুন button style + Premium custom emoji icon ব্যবহার করা হয়েছে।
primary = নীল, success = সবুজ, danger = লাল। এই style Bot API 9.x /
python-telegram-bot 22.7+ এবং নতুন Telegram client-এ কাজ করে।

⚠️ ডিপোজিট/পেমেন্ট অংশটি শুধু একটি ব্যালেন্স-সিস্টেমের কাঠামো
(placeholder) হিসেবে দেওয়া হয়েছে। বাস্তব পেমেন্ট গেটওয়ে (bKash,
Nagad, ক্রিপ্টো ইত্যাদি) যুক্ত করতে চাইলে সেই গেটওয়ের অফিসিয়াল
API/SDK ব্যবহার করে নিজে ইন্টিগ্রেট করতে হবে।
"""

import sqlite3
import logging
import json
import os
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db
except ImportError:
    firebase_admin = None
    credentials = None
    firebase_db = None

# 🎨 Real Telegram button styling.
# Bot API supports: primary (blue), success (green), danger (red).
# python-telegram-bot 22.7+ is required.

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    MenuButtonCommands,
)
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ✨ Premium/custom emoji icons for Telegram buttons.
USER_REQUESTED_PREMIUM_EMOJI_IDS = {
    "ℹ️": "6053028307971085979",
    "👑": "6314576556278685829",
    "💎": "6314396206306958399",
    "💻": "6312139458690948101",
    "🚀": "6053216517732964810",
    "⚡": "6311939527963319025",
    "🛡️": "6314576556278685829",
    # Language selector custom emoji IDs supplied by the user.
    "🌐": "6339280615459789282",
    "🇧🇩": "5291824687096027834",
    "🇬🇧": "5294354358408859664",
}

CUSTOM_BUTTON_EMOJI_IDS = {
    "ADMIN PANEL": "6314576556278685829", "BUY PRODUCT": "6314203594203602602",
    "DEPOSIT MONEY": "6312104703815590263", "REFER & EARN": "6312301920123887895",
    "MY PRODUCT": "6314203594203602602", "MY PROFILE": "6314425974725288033",
    "CHECK DATA": "6314269247073687881", "SUPPORT": "6312004025487204067",
    "MY ID": "6314425974725288033", "ABOUT": "6314396206306958399",
    "বাংলা": "5291824687096027834", "English": "5294354358408859664",
    "সাপোর্ট ও লাইভ চ্যাট": "6314425974725288033", "বট কোর ও ব্র্যান্ডিং": "6314425974725288033",
    "ডিপোজিট ও গেটওয়ে": "6312104703815590263", "উইথড্র ও রেফারেল": "6312301920123887895",
    "স্ক্রিপ্ট ও শপ প্রোডাক্ট": "6314203594203602602", "ইউজার ও ব্যালেন্স": "6314441239039056345",
    "ব্রডকাস্ট ও নোটিশ বোর্ড (৪)": "6311947409228307310", "এডমিন টিম ও পারমিশন": "6311947409228307310",
    "এনালিটিক্স ও Firebase": "6314269247073687881", "মেইন মেনুতে ফিরুন": "6312314362644143742",
    "লাইভ চ্যাট চালু/বন্ধ": "6312004025487204067", "সাপোর্ট টিকেট লিস্ট": "6312004025487204067",
    "লাইভ চ্যাট চালু/Live Chat ON": "6312004025487204067", "লাইভ চ্যাট বন্ধ/Live Chat OFF": "6312004025487204067",
    "সাপোর্ট মেসেজ এডিট": "6312004025487204067", "Admin Panel এ ফিরুন": "6314089206339607649",
    "বট প্রোফাইল ছবি": "6314362233115647636", "বট নাম/বায়ো": "6314362233115647636",
    "ওয়েলকাম মেসেজ এডিট": "6314362233115647636", "গেটওয়ে যোগ করুন": "6312260233171312151",
    "গেটওয়ে রিমুভ": "6312207774440759897", "গেটওয়ে লিস্ট": "6314128625549450770",
    "উইথড্র রিকোয়েস্ট লিস্ট": "6314269247073687881", "রেফারেল বোনাস সেট": "6312301920123887895",
    "রেফারেল রিপোর্ট": "6312301920123887895", "Add Product": "6314203594203602602",
    "Remove Product": "6312207774440759897", "All Products": "6314203594203602602",
    "ক্যাটাগরি ও প্রোডাক্ট": "6314203594203602602", "নতুন ক্যাটাগরি যোগ": "6312260233171312151",
    "সরাসরি প্রোডাক্ট যোগ": "6312260233171312151", "মেইন অ্যাডমিন প্যানেল": "6314576556278685829",
    "All Users": "6314441239039056345", "Add Balance": "6312104703815590263",
    "ইউজার সার্চ (ID দিয়ে)": "6311848921333245664", "Broadcast পাঠান": "6311947409228307310",
    "নোটিশ বোর্ড এডিট": "6314293152861657827", "Admin যোগ করুন": "6312260233171312151",
    "Admin রিমুভ": "6312207774440759897", "Admin লিস্ট ও পারমিশন": "6314576556278685829",
    "সেলস রিপোর্ট": "6314269247073687881", "ইউজার গ্রোথ": "6314269247073687881",
    "Firebase কানেকশন স্ট্যাটাস": "6314269247073687881", "Back to Home": "6314089206339607649",
    "Approve": "6311983130471308119", "Reject": "6312235051778056164",
    "Close Ticket": "6312235051778056164",
    "১-ক্লিকে উত্তর (Reply)": "6314425974725288033",
    "CANCEL": "6312235051778056164",
    "CHANGE LANGUAGE": "6339280615459789282",
    "Add Category": "6312260233171312151",
    "Del Category": "6312207774440759897",
    "Admin Panel এ ফিরুন": "6314089206339607649",
    "Back to Categories": "6314203594203602602",
    "Home": "6314089206339607649",
    "🏆": "6235422679835350879",
    "📢": "6053275839821257175",
    "🔥": "6052973985224728368",
    "🔴": "6312207774440759897",
    "🔁": "6053225373955530616",
    "📅": "6311977787531997060",
    "👨‍💻": "6312139458690948101",
    "💸": "6312104703815590263",
    "🧑‍🤝‍🧑": "6314471909400519173",
    "✅": "6336784805669114360",
    "🏷️": "6314269247073687881",
    "❌": "6052869226677410910",
    "🦊": "6336639073133794426",
    "📜": "6314269247073687881",
    "😔": "6312207774440759897",
    "📋": "6311977787531997060",
    "🗂️": "6314203594203602602",
    "📦": "6314203594203602602",
    "⚠️": "6314510813214284503",
    "🧩": "6311888503751843904",
}

# Payment-method custom emoji IDs supplied by the user.
CUSTOM_BUTTON_EMOJI_IDS.update({
    "Bkash": "5348469219761626211",
    "Nagad": "6235336389647407554",
    "Roket": "5346042941196507141",
    "Binance": "6312205150215740546",
    "Binance USDT": "6312205150215740546",
})


WELCOME_MESSAGE = '🔥 **Hello Hey!** 🌟 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 **TRUSTED SELL 𝗭𝗢NE**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚡ 𝙄𝙣𝙨𝙩𝙖𝙣𝙩 𝘿𝙚𝙡𝙞𝙫𝙚𝙧𝙮\n🛡️ 𝙎𝙚𝙘𝙪𝙧𝙚 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚\n💎 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙌𝙪𝙖𝙡𝙞𝙩𝙮\n✅ 𝙏𝙧𝙪𝙨𝙩𝙚𝙙 𝙎𝙚𝙧𝙫𝙞𝙘𝙚\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n👋 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 𝙩𝙝𝙚 𝙎𝙝𝙤𝙥 𝙈𝙚𝙣𝙪!\nSelect an option below:\n@Ifgsupport'

# ----------------------------------------------------------------------
# Premium custom emoji for MESSAGE TEXT
# ----------------------------------------------------------------------
# The IDs below are Telegram custom-emoji IDs supplied for this bot.
# Buttons use icon_custom_emoji_id directly; messages use Telegram HTML
# <tg-emoji emoji-id="...">...</tg-emoji> tags so the emoji itself renders
# as Premium/Custom Emoji instead of the normal Unicode emoji.
PREMIUM_MESSAGE_EMOJI_IDS = {
    "👑": USER_REQUESTED_PREMIUM_EMOJI_IDS["👑"],
    "📚": "6314203594203602602",
    "💳": "6312104703815590263",
    "🎁": "6312301920123887895",
    "🛍️": "6314203594203602602",
    "👤": "6314425974725288033",
    "🪪": "6314425974725288033",
    "💎": USER_REQUESTED_PREMIUM_EMOJI_IDS["💎"],
    "🏠": "6312314362644143742",
    "🎧": "6312004025487204067",
    "💬": "6312004025487204067",
    "🎫": "6312004025487204067",
    "📝": "6312004025487204067",
    "✨": "6314362233115647636",
    "🖼️": "6314362233115647636",
    "💌": "6314362233115647636",
    "🗑️": "6312207774440759897",
    "💰": "6312301920123887895",
    "📈": "6312301920123887895",
    "👥": "6314441239039056345",
    "🔎": "6311848921333245664",
    "📣": "6311947409228307310",
    "📌": "6314293152861657827",
    "🛡️": USER_REQUESTED_PREMIUM_EMOJI_IDS["🛡️"],
    "📊": "6314269247073687881",
    "💹": "6314269247073687881",
    "🔙": "6314089206339607649",
    "🟢": "6311983130471308119",
    "🔒": "6312235051778056164",
    "🏆": "6235422679835350879",
    "📢": "6053275839821257175",
    "🔥": "6052973985224728368",
    "🔴": "6312207774440759897",
    "🔁": "6053225373955530616",
    "📅": "6311977787531997060",
    "👨‍💻": "6312139458690948101",
    "💸": "6312104703815590263",
    "🧑‍🤝‍🧑": "6314471909400519173",
    "✅": "6336784805669114360",
    "🏷️": "6314269247073687881",
    "❌": "6052869226677410910",
    "🦊": "6336639073133794426",
    "📜": "6314269247073687881",
    "😔": "6312207774440759897",
    "📋": "6311977787531997060",
    "🗂️": "6314203594203602602",
    "📦": "6314203594203602602",
    "⚠️": "6314510813214284503",
    "🧩": "6311888503751843904",
    "📁": "6314564624859536473",
    "🤖": "6053117209499146201",
}

# Additional Premium IDs supplied in the latest update are included above.
# Also cover the plus icon used by some admin actions.
PREMIUM_MESSAGE_EMOJI_IDS["➕"] = "6312260233171312151"

# Latest Premium/Custom Emoji IDs supplied by the user.
LATEST_PREMIUM_EMOJI_IDS = {
    "🎨": "6052973985224728368",
    "🪙": "6311842100925176802",
    "🎖": "6314510323588013280",
    "👋": "6311842100925176802",
    "➖": "6312235051778056164",
    "ℹ️": "6053028307971085979",
    "✍️": "6053077996447734125",
    "🆔": "6052909083973918987",
    "🧾": "6338935574967098253",
    "🦋": "6312104703815590263",
    "♾️": "6053323501073341449",
}
LATEST_PREMIUM_EMOJI_IDS.update({
    "📂": "6314269247073687881",
    "👇": "6053078043692374997",
    "🎯": "6314298001879735512",
    "⚡": "6311939527963319025",
    "➡": "6314565157435480578",
})
CUSTOM_BUTTON_EMOJI_IDS.update(LATEST_PREMIUM_EMOJI_IDS)
PREMIUM_MESSAGE_EMOJI_IDS.update(LATEST_PREMIUM_EMOJI_IDS)
PREMIUM_MESSAGE_EMOJI_IDS.update({
    "🌐": "6339280615459789282",
    "🇧🇩": "5291824687096027834",
    "🇬🇧": "5294354358408859664",
})



def _markdown_to_html(text: str) -> str:
    """Convert the small Markdown subset used by this bot to safe HTML."""
    import html
    import re
    text = html.escape(str(text), quote=False)

    # Protect inline code first.
    code_parts = []
    def _code(m):
        code_parts.append(m.group(1))
        return f"\x00CODE{len(code_parts)-1}\x00"
    text = re.sub(r"`([^`]+)`", _code, text)

    # Convert bold/italic markers used by the bot. Most bot messages use *bold*.
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", text)

    for i, value in enumerate(code_parts):
        text = text.replace(f"\x00CODE{i}\x00", f"<code>{value}</code>")
    return text


def premiumize_message_text(text: str, parse_mode=None):
    """Replace mapped Unicode emoji with Telegram Premium custom emoji tags."""
    import re
    if text is None:
        return text, parse_mode

    # When Markdown is requested, convert the bot's simple Markdown to HTML so
    # custom-emoji tags can be used without losing the existing bold/code text.
    if parse_mode and str(parse_mode).upper() == "MARKDOWN":
        text = _markdown_to_html(text)
        parse_mode = "HTML"
    elif not parse_mode:
        # No parse_mode was requested, but a Premium emoji below can still
        # force HTML mode on this text. Any literal '<' or '>' already in
        # the plain text (e.g. "/reply <user_id>") would then be parsed by
        # Telegram as a broken HTML tag and the send silently fails with
        # "Can't parse entities". Escape those now so plain text is always
        # safe to send, exactly like the Markdown path already does above.
        import html
        text = html.escape(str(text), quote=False)

    # Long/multi-codepoint emoji must be replaced before shorter forms.
    for emoji in sorted(PREMIUM_MESSAGE_EMOJI_IDS, key=len, reverse=True):
        emoji_id = PREMIUM_MESSAGE_EMOJI_IDS[emoji]
        text = text.replace(
            emoji,
            f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'
        )

    # If custom emoji tags were inserted, HTML mode is required.
    if "<tg-emoji " in text:
        parse_mode = "HTML"
    return text, parse_mode


# ----------------------------------------------------------------------
# User language support (Bangla / English)
# ----------------------------------------------------------------------
LANGUAGE_BUTTON = "🌐 CHANGE LANGUAGE"
LANGUAGE_SELECT_BN = "🇧🇩 বাংলা"
LANGUAGE_SELECT_EN = "🇬🇧 English"

BUTTON_TRANSLATIONS = {
    "BUY PRODUCT": "প্রোডাক্ট কিনুন", "প্রোডাক্ট কিনুন": "BUY PRODUCT",
    "DEPOSIT MONEY": "টাকা ডিপোজিট", "টাকা ডিপোজিট": "DEPOSIT MONEY",
    "REFER & EARN": "রেফার ও আয় করুন", "রেফার ও আয় করুন": "REFER & EARN",
    "MY PRODUCT": "আমার প্রোডাক্ট", "আমার প্রোডাক্ট": "MY PRODUCT",
    "MY PROFILE": "আমার প্রোফাইল", "আমার প্রোফাইল": "MY PROFILE",
    "SUPPORT": "সাপোর্ট", "সাপোর্ট": "SUPPORT",
    "MY ID": "আমার আইডি", "আমার আইডি": "MY ID",
    "ABOUT": "সম্পর্কে", "সম্পর্কে": "ABOUT",
    "ADMIN PANEL": "এডমিন প্যানেল", "এডমিন প্যানেল": "ADMIN PANEL",
    "CHANGE LANGUAGE": "ভাষা পরিবর্তন করুন", "ভাষা পরিবর্তন করুন": "CHANGE LANGUAGE",
    "Home": "হোম", "হোম": "Home", "Back to Home": "হোমে ফিরুন", "হোমে ফিরুন": "Back to Home",
    "CANCEL": "বাতিল", "বাতিল": "CANCEL",
    "Approve": "অনুমোদন", "অনুমোদন": "Approve", "Reject": "প্রত্যাখ্যান", "প্রত্যাখ্যান": "Reject",
    "Add Category": "নতুন ক্যাটাগরি যোগ", "নতুন ক্যাটাগরি যোগ": "Add Category",
    "Add Product": "প্রোডাক্ট যোগ", "প্রোডাক্ট যোগ": "Add Product",
    "সাপোর্ট ও লাইভ চ্যাট": "Support & Live Chat", "Support & Live Chat": "সাপোর্ট ও লাইভ চ্যাট",
    "বট কোর ও ব্র্যান্ডিং": "Bot Core & Branding", "Bot Core & Branding": "বট কোর ও ব্র্যান্ডিং",
    "ডিপোজিট ও গেটওয়ে": "Deposit & Gateway", "Deposit & Gateway": "ডিপোজিট ও গেটওয়ে",
    "উইথড্র ও রেফারেল": "Withdraw & Referral", "Withdraw & Referral": "উইথড্র ও রেফারেল",
    "স্ক্রিপ্ট ও শপ প্রোডাক্ট": "Script & Shop Products", "Script & Shop Products": "স্ক্রিপ্ট ও শপ প্রোডাক্ট",
    "ইউজার ও ব্যালেন্স": "Users & Balance", "Users & Balance": "ইউজার ও ব্যালেন্স",
    "ব্রডকাস্ট ও নোটিশ বোর্ড (৪)": "Broadcast & Notice Board (4)", "Broadcast & Notice Board (4)": "ব্রডকাস্ট ও নোটিশ বোর্ড (৪)",
    "এডমিন টিম ও পারমিশন": "Admin Team & Permissions", "Admin Team & Permissions": "এডমিন টিম ও পারমিশন",
    "এনালিটিক্স ও Firebase": "Analytics & Firebase", "Analytics & Firebase": "এনালিটিক্স ও Firebase",
    "মেইন মেনুতে ফিরুন": "Back to Main Menu", "Back to Main Menu": "মেইন মেনুতে ফিরুন",
    "Admin Panel এ ফিরুন": "Back to Admin Panel", "Back to Admin Panel": "Admin Panel এ ফিরুন",
    "লাইভ চ্যাট চালু/বন্ধ": "Enable/Disable Live Chat", "Enable/Disable Live Chat": "লাইভ চ্যাট চালু/বন্ধ",
    "সাপোর্ট টিকেট লিস্ট": "Support Ticket List", "Support Ticket List": "সাপোর্ট টিকেট লিস্ট",
    "সাপোর্ট মেসেজ এডিট": "Edit Support Message", "Edit Support Message": "সাপোর্ট মেসেজ এডিট",
    "বট প্রোফাইল ছবি": "Bot Profile Picture", "Bot Profile Picture": "বট প্রোফাইল ছবি",
    "বট নাম/বায়ো": "Bot Name/Bio", "Bot Name/Bio": "বট নাম/বায়ো",
    "ওয়েলকাম মেসেজ এডিট": "Edit Welcome Message", "Edit Welcome Message": "ওয়েলকাম মেসেজ এডিট",
    "ওয়েলকাম বেনার": "Welcome Banner", "Welcome Banner": "ওয়েলকাম বেনার",
    "রুলস ও টার্মস ইডিট": "Edit Rules & Terms", "Edit Rules & Terms": "রুলস ও টার্মস ইডিট",
    "ডেভেলপার ইনফর্মেশন": "Developer Information", "Developer Information": "ডেভেলপার ইনফর্মেশন",
    "ডেভেলপার কন্ট্যাক্ট লিংক": "Developer Contact Link", "Developer Contact Link": "ডেভেলপার কন্ট্যাক্ট লিংক",
    "গেটওয়ে যোগ করুন": "Add Gateway", "Add Gateway": "গেটওয়ে যোগ করুন",
    "গেটওয়ে রিমুভ": "Remove Gateway", "Remove Gateway": "গেটওয়ে রিমুভ",
    "গেটওয়ে লিস্ট": "Gateway List", "Gateway List": "গেটওয়ে লিস্ট",
    "Pending Deposit": "পেন্ডিং ডিপোজিট", "পেন্ডিং ডিপোজিট": "Pending Deposit",
    "উইথড্র রিকোয়েস্ট লিস্ট": "Withdrawal Request List", "Withdrawal Request List": "উইথড্র রিকোয়েস্ট লিস্ট",
    "রেফারেল বোনাস সেট": "Set Referral Bonus", "Set Referral Bonus": "রেফারেল বোনাস সেট",
    "রেফারেল রিপোর্ট": "Referral Report", "Referral Report": "রেফারেল রিপোর্ট",
    "ক্যাটাগরি ও প্রোডাক্ট": "Categories & Products", "Categories & Products": "ক্যাটাগরি ও প্রোডাক্ট",
    "নতুন ক্যাটাগরি যোগ": "Add New Category", "Add New Category": "নতুন ক্যাটাগরি যোগ",
    "সরাসরি প্রোডাক্ট যোগ": "Add Product Directly", "Add Product Directly": "সরাসরি প্রোডাক্ট যোগ",
    "মেইন অ্যাডমিন প্যানেল": "Main Admin Panel", "Main Admin Panel": "মেইন অ্যাডমিন প্যানেল",
    "ইউজার সার্চ (ID দিয়ে)": "Search User (by ID)", "Search User (by ID)": "ইউজার সার্চ (ID দিয়ে)",
    "Broadcast পাঠান": "Send Broadcast", "Send Broadcast": "Broadcast পাঠান",
    "নোটিশ বোর্ড এডিট": "Edit Notice Board", "Edit Notice Board": "নোটিশ বোর্ড এডিট",
    "Admin যোগ করুন": "Add Admin", "Add Admin": "Admin যোগ করুন",
    "Admin রিমুভ": "Remove Admin", "Remove Admin": "Admin রিমুভ",
    "Admin লিস্ট ও পারমিশন": "Admin List & Permissions", "Admin List & Permissions": "Admin লিস্ট ও পারমিশন",
    "সেলস রিপোর্ট": "Sales Report", "Sales Report": "সেলস রিপোর্ট",
    "ইউজার গ্রোথ": "User Growth", "User Growth": "ইউজার গ্রোথ",
    "Firebase কানেকশন স্ট্যাটাস": "Firebase Connection Status", "Firebase Connection Status": "Firebase কানেকশন স্ট্যাটাস",
    "➕ Firebase কানেক্ট করুন": "Connect Firebase", "Connect Firebase": "➕ Firebase কানেক্ট করুন",
    "📤 Firebase ডাটা যোগ করুন": "Add Firebase Data", "Add Firebase Data": "📤 Firebase ডাটা যোগ করুন",
    "📥 Firebase ডাটা দেখুন": "View Firebase Data", "View Firebase Data": "📥 Firebase ডাটা দেখুন",
}

MESSAGE_TRANSLATIONS = {
    "মেনু থেকে একটি অপশন সিলেক্ট করুন 👇": "Please select an option from the menu 👇",
    "মেইন মেনু:": "Main Menu:",
    "আপনি Admin না। ⛔": "You are not an Admin. ⛔",
    "⛔ আপনি Admin নন।": "⛔ You are not an Admin.",
    "📋 কোনো ওপেন সাপোর্ট টিকেট নেই।": "📋 There are no open support tickets.",
    "😔 এখন কোনো প্রোডাক্ট স্টকে নেই।": "😔 No products are currently in stock.",
    "🧾 আপনার কোনো প্রোডাক্ট নেই।": "🧾 You don't have any products.",
    "❌ প্রসেস বাতিল করা হয়েছে।": "❌ The process has been cancelled.",
    "❌ Ticket reply বাতিল করা হয়েছে।": "❌ Ticket reply has been cancelled.",
    "🔴 সঠিক পূর্ণ সংখ্যা দিন।": "🔴 Please enter a valid whole number.",
    "🔴 সঠিক দাম দিন।": "🔴 Please enter a valid price.",
    "🔴 সঠিক সংখ্যা দিন।": "🔴 Please enter a valid number.",
    "🔴 সঠিক User ID দিন।": "🔴 Please enter a valid User ID.",
    "😔 এই ID-এর কোনো ইউজার পাওয়া যায়নি।": "😔 No user was found with this ID.",
    "💬 আপনার মেসেজ এডমিনের কাছে পাঠানো হয়েছে।": "💬 Your message has been sent to the admin.",
    "ℹ️ Main Menu খুলতে /start চাপুন।\n👑 Admin হলে /admin ব্যবহার করতে পারবেন।": "ℹ️ Press /start to open the Main Menu.\n👑 Admins can use /admin.",
}

def get_language(user_id: int) -> str:
    try:
        row = get_user(user_id)
        return (row["language"] or "bn") if row else "bn"
    except Exception:
        return "bn"

def set_language(user_id: int, language: str):
    conn = db(); cur = conn.cursor()
    cur.execute("UPDATE users SET language=? WHERE user_id=?", (language, user_id))
    conn.commit(); conn.close()
    firebase_sync_after_db_change()

def localize_label(label: str, user_id: int) -> str:
    lang = get_language(user_id)
    clean = clean_button_text(label)
    bn_to_en = {a: b for a, b in BUTTON_TRANSLATIONS.items() if "\u0980" <= a[:1] <= "\u09ff"}
    en_to_bn = {a: b for a, b in BUTTON_TRANSLATIONS.items() if a and not ("\u0980" <= a[:1] <= "\u09ff")}
    translated = clean
    if lang == "en":
        translated = bn_to_en.get(clean, clean)
        if clean in en_to_bn:
            translated = clean
    else:
        translated = en_to_bn.get(clean, clean)
        if clean in bn_to_en:
            translated = clean
    prefix = label[:len(label)-len(clean)] if clean else label
    return (prefix + translated).strip()

def localize_message(text: str, user_id: int) -> str:
    if get_language(user_id) == "bn":
        return text
    out = text
    for bn,en in MESSAGE_TRANSLATIONS.items():
        out = out.replace(bn,en)
    return out

def localize_markup(markup, user_id: int):
    """Translate labels while preserving each button's original custom emoji ID."""
    if markup is None:
        return None
    try:
        if isinstance(markup, ReplyKeyboardMarkup):
            rows = []
            for row in markup.keyboard:
                newrow = []
                for btn in row:
                    original_text = getattr(btn, "text", "")
                    original_icon = getattr(btn, "icon_custom_emoji_id", None)
                    translated = localize_label(original_text, user_id)
                    if original_icon:
                        newrow.append(make_custom_keyboard_button(translated, str(original_icon), style=getattr(btn, "style", None) or button_style(translated)))
                    else:
                        newrow.append(make_keyboard_button(translated, style=getattr(btn, "style", None)))
                rows.append(newrow)
            return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=markup.one_time_keyboard)
        if isinstance(markup, InlineKeyboardMarkup):
            rows = []
            for row in markup.inline_keyboard:
                newrow = []
                for btn in row:
                    original_text = getattr(btn, "text", "")
                    original_icon = getattr(btn, "icon_custom_emoji_id", None)
                    translated = localize_label(original_text, user_id)
                    kwargs = {}
                    if getattr(btn, "callback_data", None) is not None:
                        kwargs["callback_data"] = btn.callback_data
                    if getattr(btn, "url", None) is not None:
                        kwargs["url"] = btn.url
                    if original_icon:
                        kwargs["icon_custom_emoji_id"] = str(original_icon)
                    else:
                        kwargs["icon_custom_emoji_id"] = button_icon_id(translated)
                    newrow.append(InlineKeyboardButton(text=translated, **kwargs))
                rows.append(newrow)
            return InlineKeyboardMarkup(rows)
    except Exception as e:
        logger.warning(f"Keyboard localization failed: {e}")
        return markup
    return markup

async def premium_reply_text(message, text, **kwargs):
    """Reply with Premium custom emojis while preserving reply markup."""
    parse_mode = kwargs.pop("parse_mode", None)
    user_id = getattr(getattr(message, "chat", None), "id", 0)
    text = localize_message(text, user_id)
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = localize_markup(kwargs["reply_markup"], user_id)
    text, parse_mode = premiumize_message_text(text, parse_mode)
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    return await message.reply_text(text, **kwargs)


async def premium_send_message(bot, chat_id, text, **kwargs):
    """Send a message with Premium custom emojis."""
    parse_mode = kwargs.pop("parse_mode", None)
    text = localize_message(text, chat_id)
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = localize_markup(kwargs["reply_markup"], chat_id)
    text, parse_mode = premiumize_message_text(text, parse_mode)
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    return await bot.send_message(chat_id, text, **kwargs)


async def premium_edit_message_text(query, text, **kwargs):
    """Edit a message with Premium custom emojis."""
    parse_mode = kwargs.pop("parse_mode", None)
    text, parse_mode = premiumize_message_text(text, parse_mode)
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    return await query.edit_message_text(text, **kwargs)


# Exact user-requested Premium Emoji IDs are also available as stable aliases.
CUSTOM_BUTTON_EMOJI_IDS.update({
    "🌐": "6339280615459789282",
    "🇧🇩": "5291824687096027834",
    "🇬🇧": "5294354358408859664",
    "__INFO__": USER_REQUESTED_PREMIUM_EMOJI_IDS["ℹ️"],
    "__CROWN__": USER_REQUESTED_PREMIUM_EMOJI_IDS["👑"],
    "__DIAMOND__": USER_REQUESTED_PREMIUM_EMOJI_IDS["💎"],
    "__LAPTOP__": USER_REQUESTED_PREMIUM_EMOJI_IDS["💻"],
    "__ROCKET__": USER_REQUESTED_PREMIUM_EMOJI_IDS["🚀"],
    "__LIGHTNING__": USER_REQUESTED_PREMIUM_EMOJI_IDS["⚡"],
    "__SHIELD__": USER_REQUESTED_PREMIUM_EMOJI_IDS["🛡️"],
})

def clean_button_text(text: str) -> str:
    """Button label only: remove normal leading emoji so Telegram uses the custom icon field."""
    import re, unicodedata
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u200d", "").replace("\ufe0f", "")
    # Strip all leading Unicode symbols/pictographs before the actual label.
    while text:
        ch = text[0]
        cat = unicodedata.category(ch)
        if ch.isalnum() or "\u0980" <= ch <= "\u09ff":
            break
        if cat.startswith(("S", "P")) or cat == "So":
            text = text[1:].lstrip()
        else:
            break
    return re.sub(r"\s+", " ", text).strip()


MAIN_MENU_ALIASES = {
    "BUY PRODUCT": "BUY_PRODUCT", "প্রোডাক্ট কিনুন": "BUY_PRODUCT",
    "DEPOSIT MONEY": "DEPOSIT_MONEY", "টাকা ডিপোজিট": "DEPOSIT_MONEY",
    "REFER & EARN": "REFER", "রেফার ও আয় করুন": "REFER",
    "MY PRODUCT": "MY_PRODUCT", "আমার প্রোডাক্ট": "MY_PRODUCT",
    "MY PROFILE": "MY_PROFILE", "আমার প্রোফাইল": "MY_PROFILE",
    "CHANGE LANGUAGE": "CHANGE_LANGUAGE", "ভাষা পরিবর্তন করুন": "CHANGE_LANGUAGE",
    "SUPPORT": "SUPPORT", "সাপোর্ট": "SUPPORT",
    "MY ID": "MY_ID", "আমার আইডি": "MY_ID",
    "ABOUT": "ABOUT", "সম্পর্কে": "ABOUT",
    "ADMIN PANEL": "ADMIN_PANEL", "এডমিন প্যানেল": "ADMIN_PANEL",
}

def button_icon_id(text: str):
    """Return the premium/custom emoji ID for a button.

    Exact button labels are checked first so labels that reuse the same
    normal emoji (for example 💳, 💰, 🏠 or 🗑️) can still use different
    premium emoji IDs. Prefix fallbacks cover any remaining buttons that
    use one of the supplied standard emoji.
    """
    clean = clean_button_text(text)
    if clean in CUSTOM_BUTTON_EMOJI_IDS:
        return CUSTOM_BUTTON_EMOJI_IDS[clean]
    for src, dst in BUTTON_TRANSLATIONS.items():
        if src == clean and dst in CUSTOM_BUTTON_EMOJI_IDS:
            return CUSTOM_BUTTON_EMOJI_IDS[dst]
        if dst == clean and src in CUSTOM_BUTTON_EMOJI_IDS:
            return CUSTOM_BUTTON_EMOJI_IDS[src]

    # Fallbacks for buttons whose exact label is not in the map.
    # Exact mappings above always win when the same standard emoji has
    # multiple meanings/IDs.
    prefix_ids = {
        "👑": USER_REQUESTED_PREMIUM_EMOJI_IDS["👑"],
        "📚": "6314203594203602602",
        "🎁": "6312301920123887895",
        "🛍️": "6314203594203602602",
        "👤": "6314425974725288033",
        "🪪": "6314425974725288033",
        "💎": USER_REQUESTED_PREMIUM_EMOJI_IDS["💎"],
        "🎧": "6312004025487204067",
        "💬": "6312004025487204067",
        "🎫": "6312004025487204067",
        "📝": "6312004025487204067",
        "✨": "6314362233115647636",
        "🖼️": "6314362233115647636",
        "💌": "6314362233115647636",
        "📋": "6311977787531997060",
        "📣": "6311947409228307310",
        "📌": "6314293152861657827",
        "🛡️": USER_REQUESTED_PREMIUM_EMOJI_IDS["🛡️"],
        "📊": "6314269247073687881",
        "💹": "6314269247073687881",
        "🔎": "6311848921333245664",
        "🔙": "6314089206339607649",
        "🔒": "6312235051778056164",
        "➕": "6312260233171312151",
        "🗑️": "6312207774440759897",
        "🟢": "6311983130471308119",
        "ℹ️": USER_REQUESTED_PREMIUM_EMOJI_IDS["ℹ️"],
        "💻": USER_REQUESTED_PREMIUM_EMOJI_IDS["💻"],
        "🚀": USER_REQUESTED_PREMIUM_EMOJI_IDS["🚀"],
        "⚡": USER_REQUESTED_PREMIUM_EMOJI_IDS["⚡"],
        "🔴": "6312207774440759897",
        "🏆": "6235422679835350879",
        "📢": "6053275839821257175",
        "🔥": "6052973985224728368",
        "🔁": "6053225373955530616",
        "📅": "6311977787531997060",
        "👨‍💻": "6312139458690948101",
        "💸": "6312104703815590263",
        "🧑‍🤝‍🧑": "6314471909400519173",
        "✅": "6336784805669114360",
        "🏷️": "6314269247073687881",
        "❌": "6052869226677410910",
        "🦊": "6336639073133794426",
        "📜": "6314269247073687881",
        "😔": "6312207774440759897",
        "🗂️": "6314203594203602602",
        "📦": "6314203594203602602",
        "⚠️": "6314510813214284503",
        "🧩": "6311888503751843904",
    }
    prefix_ids.update(LATEST_PREMIUM_EMOJI_IDS)
    # Normalize variation selector so both emoji forms match.
    raw = (text or "").replace("\ufe0f", "")
    for emoji, emoji_id in prefix_ids.items():
        if raw.startswith(emoji.replace("\ufe0f", "")):
            return emoji_id
    return None

def make_keyboard_button(text: str, style=None):
    # IMPORTANT: normal emoji are stripped from the visible label; Telegram
    # receives the custom emoji through icon_custom_emoji_id.
    clean = clean_button_text(text)
    return KeyboardButton(
        text=clean,
        style=style or button_style(text),
        icon_custom_emoji_id=button_icon_id(text),
    )


def make_custom_keyboard_button(text: str, emoji_id: str, style="primary"):
    # Explicit custom emoji ID: no normal emoji is kept in the label.
    return KeyboardButton(text=clean_button_text(text), style=style, icon_custom_emoji_id=str(emoji_id))

def make_inline_button(text: str, **kwargs):
    return InlineKeyboardButton(clean_button_text(text), icon_custom_emoji_id=button_icon_id(text), **kwargs)

DISPLAY_TO_LOGICAL = {clean_button_text(k): k for k in CUSTOM_BUTTON_EMOJI_IDS}

# Every recognized menu/admin-panel button label, in its cleaned (no leading
# emoji) form. Used to detect "the admin tapped a menu button" versus "the
# admin typed free text" inside stateful input flows (e.g. one-click ticket
# reply), so a stray leftover flag can never swallow an unrelated button tap.
_KNOWN_MENU_LABELS = {clean_button_text(k) for k in CUSTOM_BUTTON_EMOJI_IDS}


class _NotMenuButtonFilter(filters.MessageFilter):
    """True when the message text is NOT a known menu/admin-panel button
    label. Every admin input flow below (Add Category, Add Gateway, Edit
    Notice Board, Add Balance, etc.) uses a broad "any text" filter for its
    waiting-for-input states. Without this guard, if an admin leaves such a
    flow open (forgets to press CANCEL) and taps an unrelated menu button —
    e.g. the Live Chat toggle — that tap gets silently swallowed as if it
    were the expected input, and the button appears to "not work". Adding
    this filter makes every such state ignore known button taps so they
    fall through to normal menu routing instead."""
    def filter(self, message):
        return clean_button_text(message.text or "") not in _KNOWN_MENU_LABELS


NOT_MENU_BUTTON = _NotMenuButtonFilter()



# ----------------------------------------------------------------------
# কনফিগারেশন
# ----------------------------------------------------------------------
BOT_TOKEN = "8432339396:AAEK9QTgIQMwxOnDgBwdS0YqwGW-A6dIRUk"
ADMIN_IDS = [7491778880]                    # আপনার Telegram user id (একাধিক হতে পারে)
DB_PATH = "shop.db"
SUPPORT_USERNAME = "@your_support_username"

# ডিপোজিট সেটিংস
MIN_DEPOSIT_USD = 0.20
MIN_DEPOSIT_BDT = 25
MAX_DEPOSIT_TEXT = "Unlimited / আনলিমিটেড"
USD_TO_BDT_RATE = 125

PAYMENT_METHODS = {
    "binance": "Binance USDT",
    "nagad": "Nagad",
    "bkash": "Bkash",
    "roket": "Roket",
}

# 🔥 Firebase integration: configured directly from the Telegram Admin Panel.
FIREBASE_SERVICE_ACCOUNT_FILE = "firebase_service_account.json"
FIREBASE_CONFIG = {"project_id": "", "database_url": ""}

def _load_firebase_config():
    FIREBASE_CONFIG["project_id"] = get_setting("firebase_project_id", "")
    FIREBASE_CONFIG["database_url"] = get_setting("firebase_database_url", "")
    return FIREBASE_CONFIG

def _firebase_ready():
    if firebase_admin is None:
        return False, "firebase-admin ইনস্টল করা নেই। Server-এ `pip install firebase-admin` চালান।"
    if not os.path.exists(FIREBASE_SERVICE_ACCOUNT_FILE):
        return False, "Service Account JSON এখনো যোগ করা হয়নি।"
    _load_firebase_config()
    if not FIREBASE_CONFIG.get("database_url"):
        return False, "Realtime Database URL এখনো সেট করা হয়নি।"
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_FILE)
            firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_CONFIG["database_url"]})
        return True, "OK"
    except Exception as e:
        return False, f"Firebase initialize error: {e}"

def _firebase_ref(path="/"):
    ready, msg = _firebase_ready()
    if not ready:
        raise RuntimeError(msg)
    return firebase_db.reference(path)


TABLE_PRIMARY_KEYS = {
    "users": "user_id",
    "products": "id",
    "categories": "id",
    "orders": "id",
    "deposits": "id",
    "gateways": "id",
    "settings": "key",
    "admins": "user_id",
    "tickets": "id",
    "withdrawals": "id",
}


def sync_core_data_to_firebase():
    """Mirror ALL SQLite tables into Firebase when Firebase is connected.
    SQLite remains the local source of truth; Firebase keeps a live backup/copy.
    Every table (users/balance, deposits, orders, products, categories,
    gateways, settings, admins, tickets, withdrawals) is included so nothing
    is silently left out of the backup.
    """
    try:
        ready, _ = _firebase_ready()
        if not ready:
            return False
        conn = db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        snapshot = {}
        for table, pk in TABLE_PRIMARY_KEYS.items():
            rows = cur.execute(f"SELECT * FROM {table}").fetchall()
            items = {}
            for row in rows:
                item = dict(row)
                # Firebase does not accept Python NaN/Infinity values.
                for k, v in list(item.items()):
                    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
                        item[k] = 0
                row_id = item.get(pk)
                items[str(row_id)] = item
            snapshot[table] = items
        conn.close()

        root = firebase_db.reference("/")
        for table, items in snapshot.items():
            root.child(table).set(items)
        # Keep a dedicated balance map for quick Firebase-side access.
        balances = {uid: float(data.get("balance", 0) or 0) for uid, data in snapshot["users"].items()}
        root.child("balances").set(balances)
        return True
    except Exception as e:
        logger.warning("Firebase core-data sync failed: %s", e)
        return False

import threading

_firebase_sync_event = threading.Event()
_firebase_sync_worker_started = False
_firebase_sync_worker_lock = threading.Lock()

def _firebase_sync_worker():
    """Runs forever in a background thread. Wakes up whenever a DB change
    happens, does one full sync, then goes back to sleep. If several changes
    arrive while a sync is running, they collapse into a single follow-up
    sync instead of piling up."""
    while True:
        _firebase_sync_event.wait()
        _firebase_sync_event.clear()
        try:
            sync_core_data_to_firebase()
        except Exception:
            logger.warning("Firebase background sync failed", exc_info=True)


def firebase_sync_after_db_change():
    """Best-effort sync hook; never breaks the Telegram bot if Firebase is down.
    IMPORTANT: this only *signals* a background thread — it never uploads to
    Firebase itself. That keeps every Telegram handler fast, even though the
    Firebase upload (a full-table snapshot) can take a second or more.
    """
    global _firebase_sync_worker_started
    with _firebase_sync_worker_lock:
        if not _firebase_sync_worker_started:
            threading.Thread(target=_firebase_sync_worker, daemon=True).start()
            _firebase_sync_worker_started = True
    _firebase_sync_event.set()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# States for admin add-product conversation
ADD_NAME, ADD_PRICE, ADD_STOCK, ADD_DESC, ADD_DEMO, ADD_CONTENT = range(6)
# States for admin add-gateway conversation
ADD_GW_NAME, ADD_GW_DETAILS = range(4, 6)
DEPOSIT_AMOUNT = 10
# States for other admin edit-flows
EDIT_SUPPORT_MSG = 20
SET_WELCOME_MSG = 21
SET_RULES_TERMS = 24
SET_DEVELOPER_INFO = 25
SET_BOT_NAME = 22
SET_BOT_DESC = 23
SET_NOTICE_BOARD = 24
SET_REFERRAL_BONUS = 25
BROADCAST_MSG = 26
ADD_ADMIN_ID = 27
USER_SEARCH_ID = 28
ADD_BALANCE_USER_ID = 29
ADD_BALANCE_AMOUNT = 30
ADD_CATEGORY_NAME = 31
SET_DEVELOPER_CONTACT = 32

# ----------------------------------------------------------------------
# ডাটাবেজ
# ----------------------------------------------------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            referred_by INTEGER,
            joined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER,
            description TEXT,
            description_type TEXT DEFAULT 'text',
            description_file_id TEXT,
            demo_username TEXT,
            content_type TEXT,
            content TEXT
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            price REAL,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            decided_at TEXT,
            decided_by INTEGER
        );

        CREATE TABLE IF NOT EXISTS gateways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            details TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_at TEXT
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            decided_at TEXT,
            decided_by INTEGER
        );
        """
    )
    # Existing databases may have been created before category support.
    # Add the category_id column safely if it is missing.
    cur.execute("PRAGMA table_info(products)")
    product_columns = {row[1] for row in cur.fetchall()}
    if "category_id" not in product_columns:
        cur.execute("ALTER TABLE products ADD COLUMN category_id INTEGER")

    # Product metadata/content fields for the extended Add Product flow.
    cur.execute("PRAGMA table_info(products)")
    product_columns = {row[1] for row in cur.fetchall()}
    for col, definition in [
        ("description_type", "TEXT DEFAULT 'text'"),
        ("description_file_id", "TEXT"),
        ("demo_username", "TEXT"),
        ("content_type", "TEXT"),
        ("content", "TEXT"),
    ]:
        if col not in product_columns:
            cur.execute(f"ALTER TABLE products ADD COLUMN {col} {definition}")

    # User language preference.
    cur.execute("PRAGMA table_info(users)")
    user_columns = {row[1] for row in cur.fetchall()}
    if "language" not in user_columns:
        cur.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'bn'")

    # Deposit proof fields for transaction ID / screenshot verification.
    cur.execute("PRAGMA table_info(deposits)")
    deposit_columns = {row[1] for row in cur.fetchall()}
    if "transaction_id" not in deposit_columns:
        cur.execute("ALTER TABLE deposits ADD COLUMN transaction_id TEXT")
    if "proof_file_id" not in deposit_columns:
        cur.execute("ALTER TABLE deposits ADD COLUMN proof_file_id TEXT")
    conn.commit()
    conn.close()


def ensure_user(user_id: int, username: str):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, balance, joined_at) VALUES (?,?,0,?)",
            (user_id, username, datetime.utcnow().isoformat()),
        )
        conn.commit()
    conn.close()
    firebase_sync_after_db_change()


def get_user(user_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_balance(user_id: int, amount: float):
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()


def get_setting(key: str, default=None):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS or user_id in HIDDEN_ADMIN_IDS:  # আসল ওনার/হার্ডকোড করা এডমিন
        return True
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def is_owner(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id in HIDDEN_ADMIN_IDS


def get_all_admin_ids():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins")
    dynamic_ids = [r["user_id"] for r in cur.fetchall()]
    conn.close()
    return list(set(ADMIN_IDS + HIDDEN_ADMIN_IDS + dynamic_ids))


def build_dashboard_text() -> str:
    """One-glance status of every system in the Admin Panel: counts pulled
    live from SQLite/settings, plus the Firebase connection state."""
    conn = db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    total_users = cur.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    total_balance = cur.execute("SELECT COALESCE(SUM(balance),0) s FROM users").fetchone()["s"]

    pending_deposits = cur.execute("SELECT COUNT(*) c FROM deposits WHERE status='pending'").fetchone()["c"]
    approved_deposit_sum = cur.execute("SELECT COALESCE(SUM(amount),0) s FROM deposits WHERE status='approved'").fetchone()["s"]

    pending_withdrawals = cur.execute("SELECT COUNT(*) c FROM withdrawals WHERE status='pending'").fetchone()["c"]

    gateway_count = cur.execute("SELECT COUNT(*) c FROM gateways").fetchone()["c"]

    category_count = cur.execute("SELECT COUNT(*) c FROM categories").fetchone()["c"]
    product_count = cur.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    total_stock = cur.execute("SELECT COALESCE(SUM(stock),0) s FROM products").fetchone()["s"]

    open_tickets = cur.execute("SELECT COUNT(*) c FROM tickets WHERE status='open'").fetchone()["c"]
    total_tickets = cur.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"]

    admin_count = len([i for i in get_all_admin_ids() if i not in HIDDEN_ADMIN_IDS])
    conn.close()

    live_chat_on = (get_setting("live_chat", "off") or "off").lower() == "on"
    notice_set = bool((get_setting("notice_board", "") or "").strip())
    referral_bonus = float(get_setting("referral_bonus", "0") or 0)
    welcome_set = bool((get_setting("welcome_message", "") or "").strip())
    branding_ready = welcome_set or bool(get_setting("welcome_banner_file_id", ""))

    _load_firebase_config()
    fb_ready, fb_msg = _firebase_ready()
    fb_line = (
        f"✅ Connected (`{FIREBASE_CONFIG.get('project_id') or 'Unknown'}`)"
        if fb_ready else f"🔴 Not connected — {fb_msg}"
    )

    def onoff(flag):
        return "🟢 ON" if flag else "🔴 OFF"

    return (
        "📟 *Admin Panel Dashboard*\n"
        "সব সিস্টেমের লাইভ স্ট্যাটাস:\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *ইউজার ও ব্যালেন্স*\n"
        f"• মোট ইউজার: {total_users}\n"
        f"• মোট ব্যালেন্স: {total_balance:.2f}৳\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 *ডিপোজিট ও গেটওয়ে*\n"
        f"• Pending Deposit: {pending_deposits}\n"
        f"• মোট Approved Deposit: {approved_deposit_sum:.2f}৳\n"
        f"• Active Gateway: {gateway_count}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 *উইথড্র ও রেফারেল*\n"
        f"• Pending Withdrawal: {pending_withdrawals}\n"
        f"• Referral Bonus: {referral_bonus:.2f}৳\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 *স্ক্রিপ্ট ও শপ প্রোডাক্ট*\n"
        f"• Category: {category_count}\n"
        f"• Product: {product_count} (Stock: {int(total_stock)})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎧 *সাপোর্ট ও লাইভ চ্যাট*\n"
        f"• Live Chat: {onoff(live_chat_on)}\n"
        f"• Open Ticket: {open_tickets} (মোট {total_tickets})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ *বট কোর ও ব্র্যান্ডিং*\n"
        f"• Branding Setup: {'🟢 Done' if branding_ready else '🔴 Not set'}\n"
        f"• Notice Board: {'🟢 Set' if notice_set else '🔴 Empty'}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ *এডমিন টিম*\n"
        f"• মোট Admin: {admin_count}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 *Firebase*\n"
        f"• Status: {fb_line}\n"
    )


# ----------------------------------------------------------------------
# মেনু কীবোর্ড (স্ক্রিনশট অনুযায়ী)
# ----------------------------------------------------------------------
def button_style(text: str) -> str:
    """Return the Telegram button style used for this bot."""
    t = text.lower()

    # Green: positive/main actions
    if (
        "buy product" in t
        or "deposit money" in t
        or "add product" in t
        or "add balance" in t
        or "gateway যোগ" in t
        or "gateway add" in t
        or "➕" in text
        or "approve" in t
    ):
        return "success"

    # Red: destructive actions
    if (
        "remove" in t
        or "রিমুভ" in t
        or "reject" in t
        or "🔴" in text
    ):
        return "danger"

    # Blue: normal/navigation actions
    return "primary"


def styled_reply_keyboard(rows):
    """Build a ReplyKeyboardMarkup with real Telegram button colors."""
    keyboard = [
        [make_keyboard_button(label) for label in row]
        for row in rows
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


CANCEL_TEXT = "CANCEL"

CANCEL_EMOJI_ID = "6312235051778056164"

def cancel_keyboard():
    """Reply keyboard shown while waiting for input, with the requested custom emoji icon."""
    return ReplyKeyboardMarkup(
        [[make_custom_keyboard_button("CANCEL", CANCEL_EMOJI_ID, style="danger")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def main_menu_keyboard(user_id: int):
    rows = []
    if is_admin(user_id):
        rows.append(["👑 ADMIN PANEL"])
    rows.append(["📚 BUY PRODUCT", "💳 DEPOSIT MONEY"])
    rows.append(["🎁 REFER & EARN", "🛍️ MY PRODUCT"])
    rows.append(["👤 MY PROFILE", "🎧 SUPPORT"])
    # Swap the positions of ABOUT and CHANGE LANGUAGE.
    # Their labels remain unchanged so each button keeps its original action.
    rows.append(["🪪 MY ID", LANGUAGE_BUTTON])
    rows.append(["💎 ABOUT"])
    return styled_reply_keyboard(rows)


ADMIN_PANEL_KB = styled_reply_keyboard(
    [
        ["🎧 সাপোর্ট ও লাইভ চ্যাট", "✨ বট কোর ও ব্র্যান্ডিং"],
        ["💳 ডিপোজিট ও গেটওয়ে", "💰 উইথড্র ও রেফারেল"],
        ["📦 স্ক্রিপ্ট ও শপ প্রোডাক্ট", "👥 ইউজার ও ব্যালেন্স"],
        ["📣 ব্রডকাস্ট ও নোটিশ বোর্ড (৪)"],
        ["🛡️ এডমিন টিম ও পারমিশন", "📊 এনালিটিক্স ও Firebase"],
        ["🏠 মেইন মেনুতে ফিরুন"],
    ]
)


# প্রতিটা সাব-প্যানেলের নিজস্ব কীবোর্ড (ব্যাক বাটনসহ)
def sub_panel_keyboard(buttons):
    rows = buttons + [["🔙 Admin Panel এ ফিরুন"]]
    return styled_reply_keyboard(rows)


def live_chat_button_label():
    """Button label reflects the CURRENT live-chat state, not a fixed on/off toggle name."""
    is_on = (get_setting("live_chat", "off") or "off").lower() == "on"
    return "💬 লাইভ চ্যাট চালু/Live Chat ON" if is_on else "💬 লাইভ চ্যাট বন্ধ/Live Chat OFF"


def support_live_keyboard():
    """Rebuilt on every render so the Live Chat button always shows the live status."""
    return sub_panel_keyboard(
        [[live_chat_button_label(), "🎫 সাপোর্ট টিকেট লিস্ট"], ["📝 সাপোর্ট মেসেজ এডিট"]]
    )
BOT_BRANDING_KB = sub_panel_keyboard(
    [
        ["🖼️ বট প্রোফাইল ছবি", "✨ বট নাম/বায়ো"],
        ["💌 ওয়েলকাম মেসেজ এডিট"],
        ["🖼️ ওয়েলকাম বেনার", "📜 রুলস ও টার্মস ইডিট"],
        ["👨‍💻 ডেভেলপার ইনফর্মেশন", "🔗 ডেভেলপার কন্ট্যাক্ট লিংক"],
    ]
)
DEPOSIT_GATEWAY_KB = sub_panel_keyboard(
    [["💳 গেটওয়ে যোগ করুন", "🗑️ গেটওয়ে রিমুভ"], ["📋 গেটওয়ে লিস্ট"], ["⏳ Pending Deposit"]]
)
WITHDRAW_REFERRAL_KB = sub_panel_keyboard(
    [["💸 উইথড্র রিকোয়েস্ট লিস্ট", "🎁 রেফারেল বোনাস সেট"], ["📈 রেফারেল রিপোর্ট"]]
)
SCRIPT_PRODUCT_KB = sub_panel_keyboard(
    [
        ["📋 ক্যাটাগরি ও প্রোডাক্ট", "➕ নতুন ক্যাটাগরি যোগ"],
        ["🎁 সরাসরি প্রোডাক্ট যোগ"],
        ["📤 মেইন অ্যাডমিন প্যানেল"],
    ]
)
USER_BALANCE_KB = sub_panel_keyboard(
    [["👥 All Users", "💰 Add Balance"], ["🔎 ইউজার সার্চ (ID দিয়ে)"]]
)
BROADCAST_KB = sub_panel_keyboard(
    [["📣 Broadcast পাঠান", "📌 নোটিশ বোর্ড এডিট"]]
)
ADMIN_TEAM_KB = sub_panel_keyboard(
    [["👑 Admin যোগ করুন", "🗑️ Admin রিমুভ"], ["🛡️ Admin লিস্ট ও পারমিশন"]]
)
ANALYTICS_KB = sub_panel_keyboard(
    [["💹 সেলস রিপোর্ট", "📈 ইউজার গ্রোথ"],
     ["🔥 Firebase কানেকশন স্ট্যাটাস", "➕ Firebase কানেক্ট করুন"],
     ["📤 Firebase ডাটা যোগ করুন", "📥 Firebase ডাটা দেখুন"]]
)

# ----------------------------------------------------------------------
# /start
# ----------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)

    # referral: /start ref_12345
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                ref_id = int(arg.replace("ref_", ""))
                if ref_id != user.id:
                    conn = db()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE users SET referred_by=? WHERE user_id=? AND referred_by IS NULL",
                        (ref_id, user.id),
                    )
                    conn.commit()
                    conn.close()
                    firebase_sync_after_db_change()
            except ValueError:
                pass

    default_welcome = (
        "🪙 Hello Hey!\n\n"
        "🎖️ *Welcome to* TRUSTED SELL *ZONE* ✨\n\n"
        "👑 *Admin Access Enabled* — Use /admin or button below\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Instant Delivery*\n"
        "🛡️ *Secure Purchase*\n"
        "💎 *Premium Quality*\n"
        "✅ *Trusted Service*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Welcome to the Shop Menu!*\n"
        "Select an option below:"
    )
    text = get_setting("welcome_message", default_welcome)

    # Show access status dynamically: admins see Admin Access, regular users see User Access.
    access_line = (
        "👑 *Admin Access Enabled* — Use /admin or button below"
        if is_admin(user.id)
        else "👑 *User Access*"
    )
    text = text.replace(
        "👑 *Admin Access Enabled* — Use /admin or button below",
        access_line,
    )

    notice = get_setting("notice_board")
    if notice:
        text += f"\n\n📌 *Notice:*\n{notice}"

    await premium_reply_text(update.message, 
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard(user.id)
    )


# ----------------------------------------------------------------------
# সাধারণ মেনু হ্যান্ডলার
# ----------------------------------------------------------------------
async def _create_deposit_request(update: Update, context: ContextTypes.DEFAULT_TYPE, transaction_id=None, proof_file_id=None):
    """Create a pending deposit only after the user submits proof."""
    user = update.effective_user
    amount = context.user_data.get("deposit_amount")
    method = context.user_data.get("deposit_method", "N/A")
    if amount is None:
        await premium_reply_text(update.effective_message, "❌ Deposit session পাওয়া যায়নি। আবার DEPOSIT MONEY চাপুন।")
        context.user_data.clear()
        return

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO deposits (user_id, amount, method, status, created_at, transaction_id, proof_file_id) VALUES (?,?,?,?,?,?,?)",
        (user.id, amount, method, "pending", datetime.utcnow().isoformat(), transaction_id, proof_file_id),
    )
    deposit_id = cur.lastrowid
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    context.user_data.pop("awaiting_deposit_proof", None)
    context.user_data.pop("deposit_amount", None)
    context.user_data.pop("deposit_method", None)

    await premium_reply_text(update.effective_message,
        f"✅ Deposit Request #{deposit_id} পাঠানো হয়েছে।\n"
        f"💰 Amount: {amount:.2f} ৳\n"
        f"💳 Method: {method}\n"
        "🧾 Proof received. Admin verify করার পর balance-এ যোগ হবে।",
        reply_markup=main_menu_keyboard(user.id),
    )

    approve_kb = InlineKeyboardMarkup([[
        make_inline_button("🟢 Approve", style="success", callback_data=f"dep_ok_{deposit_id}"),
        make_inline_button("🔴 Reject", style="danger", callback_data=f"dep_no_{deposit_id}"),
    ]])
    proof_line = f"Transaction ID: {transaction_id}" if transaction_id else "Proof: 📸 Screenshot/Photo attached"
    admin_text = (
        f"🔔 নতুন ডিপোজিট রিকোয়েস্ট #{deposit_id}\n"
        f"User: {user.id} (@{user.username or 'N/A'})\n"
        f"Method: {method}\n"
        f"Amount: {amount:.2f} ৳\n"
        f"{proof_line}"
    )
    for admin_id in get_all_admin_ids():
        try:
            if proof_file_id:
                await context.bot.send_photo(admin_id, photo=proof_file_id, caption=admin_text, reply_markup=approve_kb)
            else:
                await premium_send_message(context.bot, admin_id, admin_text, reply_markup=approve_kb)
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "lang_cancel":
        await premium_reply_text(
            query.message,
            "❌ প্রসেস বাতিল করা হয়েছে।",
            reply_markup=main_menu_keyboard(user_id),
        )
        return

    if query.data == "lang_bn":
        set_language(user_id, "bn")
        text = "🇧🇩 বাংলা ভাষা নির্বাচন করা হয়েছে।"
    elif query.data == "lang_en":
        set_language(user_id, "en")
        text = "🇬🇧 English language selected."
    else:
        return

    # Rebuild the main keyboard after saving the choice so every button is
    # immediately rendered in the newly selected language.
    await premium_reply_text(
        query.message,
        text,
        reply_markup=main_menu_keyboard(user_id),
    )


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Custom emoji icons are not part of button text, so route using the cleaned label.
    text = clean_button_text(text)
    # Normalize translated button labels back to the bot's canonical labels.
    # This keeps every existing router branch working in both Bangla and English.
    _en_to_bn = {a: b for a, b in BUTTON_TRANSLATIONS.items()
                 if a and not ("\u0980" <= a[:1] <= "\u09ff")}
    if text in _en_to_bn:
        text = _en_to_bn[text]
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)

    # Firebase setup/data flows must be handled by the normal TEXT router.
    # Previously this logic was accidentally placed inside /start(), so a
    # Realtime Database URL sent after tapping "Firebase Connect" was ignored.
    if is_admin(user.id) and context.user_data.get("firebase_setup_waiting_url"):
        if text and text.upper() not in ("CANCEL", "বাতিল"):
            url = text.strip()
            if not (url.startswith("https://") and ("firebaseio.com" in url or "firebasedatabase.app" in url)):
                await premium_reply_text(
                    update.message,
                    "❌ সঠিক Firebase Realtime Database URL দিন।\n\n"
                    "উদাহরণ: `https://your-project-default-rtdb.firebaseio.com/`",
                    parse_mode="Markdown",
                    reply_markup=cancel_keyboard(),
                )
                return
            context.user_data["firebase_database_url_pending"] = url.rstrip("/")
            context.user_data.pop("firebase_setup_waiting_url", None)
            context.user_data["firebase_waiting_service_json"] = True
            await premium_reply_text(
                update.message,
                "✅ *Database URL নেওয়া হয়েছে!*\n\n"
                "এখন Firebase Console থেকে *Service Account JSON* ফাইলটি `Document` হিসেবে পাঠান।",
                parse_mode="Markdown",
                reply_markup=cancel_keyboard(),
            )
            return

    if is_admin(user.id) and context.user_data.get("firebase_data_mode") in ("add", "read"):
        mode = context.user_data["firebase_data_mode"]
        if text and text.upper() not in ("CANCEL", "বাতিল"):
            try:
                if mode == "read":
                    value = _firebase_ref(text.strip()).get()
                    payload = json.dumps(value, ensure_ascii=False, indent=2, default=str)
                    if len(payload) > 3500:
                        payload = payload[:3500] + "\n..."
                    await premium_reply_text(
                        update.message,
                        f"📥 *Firebase:* `{text.strip()}`\n\n`{payload}`",
                        parse_mode="Markdown",
                    )
                else:
                    parts = [p.strip() for p in text.split("|", 2)]
                    if len(parts) != 3:
                        raise ValueError("Format ভুল। `path | key | value` ব্যবহার করুন।")
                    path, key, raw = parts
                    try:
                        value = json.loads(raw)
                    except Exception:
                        value = raw
                    clean_path = path.strip("/")
                    ref = _firebase_ref(f"/{clean_path}" if clean_path else "/")
                    ref.child(key).set(value)
                    await premium_reply_text(
                        update.message,
                        f"✅ Firebase-এ `{clean_path}/{key}` সফলভাবে যোগ হয়েছে.",
                        parse_mode="Markdown",
                    )
            except Exception as e:
                await premium_reply_text(update.message, f"❌ Firebase error: {e}")
            context.user_data.pop("firebase_data_mode", None)
            return

    # One-click support ticket reply: after an admin taps Reply, the next
    # message from that admin is delivered directly to the ticket owner.
    # IMPORTANT: if the admin instead taps any other known menu/admin-panel
    # button (e.g. Live Chat toggle) without pressing CANCEL first, that tap
    # must NOT be swallowed as a ticket reply — silently clear the pending
    # reply and let normal menu routing continue below.
    reply_ticket_id = context.user_data.get("reply_ticket_id")
    if reply_ticket_id is not None and text in _KNOWN_MENU_LABELS:
        context.user_data.pop("reply_ticket_id", None)
        context.user_data.pop("reply_ticket_user_id", None)
        reply_ticket_id = None

    if reply_ticket_id is not None:
        if text == CANCEL_TEXT:
            context.user_data.pop("reply_ticket_id", None)
            context.user_data.pop("reply_ticket_user_id", None)
            await premium_reply_text(update.message, "❌ Ticket reply বাতিল করা হয়েছে।", reply_markup=main_menu_keyboard(user.id))
            return

        if is_admin(user.id):
            conn = db()
            cur = conn.cursor()
            cur.execute("SELECT id, user_id, status FROM tickets WHERE id=?", (reply_ticket_id,))
            ticket = cur.fetchone()
            conn.close()

            if not ticket:
                context.user_data.pop("reply_ticket_id", None)
                context.user_data.pop("reply_ticket_user_id", None)
                await premium_reply_text(update.message, "🔴 টিকেটটি আর পাওয়া যাচ্ছে না।")
                return

            if ticket["status"] != "open":
                context.user_data.pop("reply_ticket_id", None)
                context.user_data.pop("reply_ticket_user_id", None)
                await premium_reply_text(update.message, "🔒 এই টিকেটটি Closed, তাই উত্তর পাঠানো যায়নি।")
                return

            try:
                await premium_send_message(
                    context.bot,
                    int(ticket["user_id"]),
                    f"💬 *Support Reply — Ticket #{ticket['id']}*\n\n{text}",
                    parse_mode="Markdown",
                )
                await premium_reply_text(
                    update.message,
                    f"✅ Ticket #{ticket['id']} এর উত্তর ইউজারের কাছে পাঠানো হয়েছে।",
                    reply_markup=main_menu_keyboard(user.id),
                )
            except Exception as e:
                logger.warning(f"Ticket reply failed for #{ticket['id']}: {e}")
                await premium_reply_text(update.message, f"🔴 উত্তর পাঠানো যায়নি: {e}")

            context.user_data.pop("reply_ticket_id", None)
            context.user_data.pop("reply_ticket_user_id", None)
            return

    # Language choices are ReplyKeyboard buttons, so handle their text here.
    # This is intentionally before the main-menu router so the choices work
    # immediately after opening the language selector.
    if text in ("বাংলা", "English"):
        selected_lang = "bn" if text == "বাংলা" else "en"
        set_language(user.id, selected_lang)
        if selected_lang == "bn":
            await premium_reply_text(
                update.message,
                "🇧🇩 বাংলা ভাষা নির্বাচন করা হয়েছে।",
                reply_markup=main_menu_keyboard(user.id),
            )
        else:
            await premium_reply_text(
                update.message,
                "🇬🇧 English language selected.",
                reply_markup=main_menu_keyboard(user.id),
            )
        return

    # Universal cancel: stop any pending input flow and return to the main menu.
    if text in (CANCEL_TEXT, "বাতিল"):
        context.user_data.clear()
        await premium_reply_text(update.message, 
            "❌ প্রসেস বাতিল করা হয়েছে।",
            reply_markup=main_menu_keyboard(user.id),
        )
        return

    # Universal "Back to Admin Panel" routing. This must run before any
    # sub-panel/conversation flow so the button works everywhere, in both
    # Bangla and English (including the older "Main Admin Panel" label).
    admin_back_labels = {
        clean_button_text("🔙 Admin Panel এ ফিরুন"),
        clean_button_text("Back to Admin Panel"),
        clean_button_text("📤 মেইন অ্যাডমিন প্যানেল"),
        clean_button_text("Main Admin Panel"),
    }
    if is_admin(user.id) and text in admin_back_labels:
        context.user_data.clear()
        await premium_reply_text(
            update.message,
            build_dashboard_text(),
            parse_mode="Markdown",
            reply_markup=ADMIN_PANEL_KB,
        )
        return

    # Robust main-menu routing. This is checked before the other flows so a
    # custom emoji icon, variation selector, or old label cannot break clicks.
    main_action = MAIN_MENU_ALIASES.get(text)
    if main_action == "ADMIN_PANEL":
        if not is_admin(user.id):
            await premium_reply_text(update.message, "আপনি Admin না। ⛔")
        else:
            await premium_reply_text(update.message,
                build_dashboard_text(), parse_mode="Markdown", reply_markup=ADMIN_PANEL_KB
            )
        return
    if main_action == "BUY_PRODUCT":
        await show_products(update, context)
        return
    if main_action == "DEPOSIT_MONEY":
        deposit_text = (
            "🦋 *DEPOSIT MONEY*\n"
            "――――――――――――\n\n"
            f"💰 *Min Deposit*: ${MIN_DEPOSIT_USD:.2f} ({MIN_DEPOSIT_BDT} BDT)\n"
            f"♾️ *Max Deposit*: {MAX_DEPOSIT_TEXT}\n"
            f"📈 *Rate*: 1 USD = {USD_TO_BDT_RATE} BDT\n"
            "――――――――――――\n\n"
            "📌 *Select Payment Method:*"
        )
        # Only gateways added from Admin Panel are shown to users.
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, details FROM gateways ORDER BY id")
        gateways = cur.fetchall()
        conn.close()
        # Use ReplyKeyboard here because Telegram reliably renders the
        # primary/success colours on ReplyKeyboard buttons. Inline buttons
        # can remain grey on some Telegram clients even when style is sent.
        gateway_keyboard = []
        for g in gateways:
            name = g["name"]
            emoji_id = button_icon_id(name) or button_icon_id(str(name))
            if name.lower() == "bkash":
                emoji_id = "5348469219761626211"
            elif name.lower() == "nagad":
                emoji_id = "6235336389647407554"
            elif name.lower() == "roket":
                emoji_id = "5346042941196507141"
            elif name.lower() in ("binance", "binance usdt"):
                emoji_id = "6312205150215740546"
            gateway_keyboard.append([make_custom_keyboard_button(name, emoji_id, "primary")])

        home_label = "হোমে ফিরুন"
        gateway_keyboard.append([make_custom_keyboard_button(home_label, CUSTOM_BUTTON_EMOJI_IDS.get("Back to Home", "6314089206339607649"), "success")])

        if not gateways:
            context.user_data["awaiting_payment_method_selection"] = True
            await premium_reply_text(update.message,
                deposit_text + "\n\n❌ বর্তমানে কোনো payment method যোগ করা হয়নি। Admin Panel থেকে gateway যোগ করুন.",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(
                    [[make_custom_keyboard_button(home_label, CUSTOM_BUTTON_EMOJI_IDS.get("Back to Home", "6314089206339607649"), "success")]],
                    resize_keyboard=True
                )
            )
            return

        context.user_data["awaiting_payment_method_selection"] = True
        await premium_reply_text(update.message,
            deposit_text, parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(gateway_keyboard, resize_keyboard=True)
        )
        return
    if main_action == "REFER":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{user.id}"
        await premium_reply_text(update.message, 
            f"🎁 আপনার রেফার লিংক:\n{link}\n\nবন্ধুরা এই লিংক দিয়ে জয়েন করলে আপনি বোনাস পাবেন।"
        )
        return
    if main_action == "MY_PRODUCT":
        await show_my_orders(update, context)
        return
    if main_action == "CHANGE_LANGUAGE":
        # The main-menu language button is a ReplyKeyboard button, so it must
        # be handled by menu_router (not by CallbackQueryHandler). Show the
        # actual language choices as inline buttons; their callbacks are
        # handled by language_callback below.
        current_lang = get_language(user.id)
        # Use a ReplyKeyboard here, not InlineKeyboardButton. Telegram
        # supports the button `style` colours reliably on ReplyKeyboard
        # buttons; the inline version was rendering both choices grey.
        language_kb = ReplyKeyboardMarkup([
            [
                make_custom_keyboard_button("বাংলা", "5291824687096027834", "success"),
                make_custom_keyboard_button("English", "5294354358408859664", "primary"),
            ],
            [make_custom_keyboard_button("CANCEL", CANCEL_EMOJI_ID, "danger")],
        ], resize_keyboard=True, one_time_keyboard=False)
        await premium_reply_text(
            update.message,
            "🌐 *ভাষা নির্বাচন করুন / Select Language*\n\n🇧🇩 বাংলা অথবা 🇬🇧 English নির্বাচন করুন।",
            parse_mode="Markdown",
            reply_markup=language_kb,
        )
        return
    if main_action == "MY_PROFILE":
        u = get_user(user.id)
        await premium_reply_text(update.message, 
            f"👤 *My Profile*\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 Username: @{user.username or 'N/A'}\n"
            f"💰 Balance: {u['balance']:.2f} ৳\n"
            f"📅 Joined: {u['joined_at'][:10]}",
            parse_mode="Markdown",
        )
        return
    if main_action == "SUPPORT":
        support_msg = get_setting("support_message", f"🏷️ Support: {SUPPORT_USERNAME}")
        await premium_reply_text(update.message, 
            f"{support_msg}\n\n✍️ নিচে আপনার সমস্যা লিখে পাঠান, আমরা একটা টিকেট খুলে দিচ্ছি:",
            reply_markup=cancel_keyboard(),
        )
        context.user_data["awaiting_ticket"] = True
        return
    if main_action == "MY_ID":
        await premium_reply_text(update.message, f"🆔 আপনার Telegram ID: `{user.id}`", parse_mode="Markdown")
        return
    if main_action == "ABOUT":
        developer_info = get_setting("developer_info", "এখানে এডমিন প্যানেল থেকে Developer Information সেট করুন")
        about_text = (
            "ℹ️ **𝘿𝙀𝙑𝙀𝙇𝙊𝙋𝙀𝙍 & 𝙋𝙇𝘼𝙏𝙁𝙊𝙍𝙈 𝙄𝙉𝙁𝙊**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 𝘽𝙤𝙩 𝙋𝙡𝙖𝙩𝙛𝙤𝙧𝙢: **TRUSTED SELL 𝗭𝗢𝗡𝗘 💎**\n"
            f"💻 𝘿𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧 / 𝙊𝙬𝙣𝙚𝙧: {developer_info}\n"
            "🚀 𝙎𝙮𝙨𝙩𝙚𝙢 𝙑𝙚𝙧𝙨𝙞𝙤𝙣: **v3.5 Pro Cloud Realtime**\n"
            "⚡ 𝙁𝙚𝙖𝙩𝙪𝙧𝙚: Instant Delivery & Auto Verification\n"
            "🛡️ 𝙎𝙚𝙘𝙪𝙧𝙞𝙩𝙮: RBAC Multi-Admin & Encrypted Storage\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 𝙁𝙤𝙧 𝙗𝙤𝙩 𝙘𝙪𝙨𝙩𝙤𝙢𝙞𝙯𝙖𝙩𝙞𝙤𝙣 𝙤𝙧 𝙞𝙣𝙦𝙪𝙞𝙧𝙞𝙚𝙨, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 𝙙𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧 𝙗𝙚𝙡𝙤𝙬:\n"
            "💡 𝙁𝙤𝙧 𝙗𝙤𝙩 𝙘𝙪𝙨𝙩𝙤𝙢𝙞𝙯𝙖𝙩𝙞𝙤𝙣 𝙤𝙧 𝙞𝙣𝙦𝙪𝙞𝙧𝙞𝙚𝙨, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 𝙙𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧 𝙗𝙚𝙡𝙤𝙬:\n\n"

        )
        contact = get_setting("developer_contact", SUPPORT_USERNAME).strip()
        if contact.startswith("https://t.me/") or contact.startswith("tg://user?id="):
            contact_url = contact
        elif contact.startswith("@"):
            contact_url = "https://t.me/" + contact[1:]
        elif contact.isdigit():
            contact_url = "tg://user?id=" + contact
        else:
            contact_url = "https://t.me/" + contact.lstrip("@")
        about_kb = InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Contact Developer", url=contact_url)]])
        await update.message.reply_text(about_text, parse_mode="Markdown", reply_markup=about_kb)
        return

    # PAYMENT METHOD selection: these are ReplyKeyboard buttons, so their text
    # must be handled by menu_router (not payment_method_callback, which is for
    # legacy inline buttons). Match gateway names case-insensitively and return
    # to Home reliably.
    if context.user_data.get("awaiting_payment_method_selection"):
        raw_payment_text = (update.message.text or "").strip()
        payment_clean = clean_button_text(raw_payment_text)
        if payment_clean.casefold() in {"হোমে ফিরুন".casefold(), "back to home".casefold(), "home".casefold()}:
            context.user_data.pop("awaiting_payment_method_selection", None)
            context.user_data.pop("deposit_method", None)
            context.user_data.pop("deposit_gateway_id", None)
            context.user_data.pop("deposit_gateway_details", None)
            await premium_reply_text(update.message, "মেইন মেনু:", reply_markup=main_menu_keyboard(user.id))
            return

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, details FROM gateways ORDER BY id")
        gateways = cur.fetchall()
        conn.close()
        selected_gateway = next(
            (g for g in gateways if clean_button_text(g["name"]).casefold() == payment_clean.casefold()),
            None,
        )
        if selected_gateway:
            gateway_id = int(selected_gateway["id"])
            method_label = selected_gateway["name"]
            method_details = selected_gateway["details"] or "Payment address/details সেট করা হয়নি।"
            context.user_data.pop("awaiting_payment_method_selection", None)
            context.user_data["deposit_method"] = method_label
            context.user_data["deposit_gateway_id"] = gateway_id
            context.user_data["deposit_gateway_details"] = method_details
            context.user_data["awaiting_deposit"] = True
            await premium_reply_text(
                update.message,
                f"🦋 *{method_label}*\n\n"
                f"💳 *Payment Address / Details:*\n`{method_details}`\n\n"
                f"💰 কত টাকা ডিপোজিট করতে চান লিখুন (শুধু সংখ্যা):\n"
                f"উদাহরণ: 100\n\n"
                f"⚠️ Min Deposit: ${MIN_DEPOSIT_USD:.2f} ({MIN_DEPOSIT_BDT} BDT)",
                parse_mode="Markdown",
            )
            await premium_reply_text(
                update.message,
                "❌ প্রয়োজন হলে নিচের CANCEL বাটনে চাপ দিয়ে এই প্রসেস বন্ধ করতে পারবেন.",
                reply_markup=cancel_keyboard(),
            )
            return

    # BUY PRODUCT flow: category -> products -> purchase.
    buy_category_mode = context.user_data.get("buy_category_mode", False)
    buy_product_mode = context.user_data.get("buy_product_mode")

    if buy_category_mode:
        raw_text = update.message.text.strip()
        if raw_text in ("Home", "হোম"):
            context.user_data.pop("buy_category_mode", None)
            await premium_reply_text(update.message, "মেইন মেনু:", reply_markup=main_menu_keyboard(user.id))
            return
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories WHERE name=?", (raw_text.rsplit(" (", 1)[0],))
        category = cur.fetchone()
        conn.close()
        if category:
            await show_category_products_for_buy(update, context, category)
            return

    if buy_product_mode:
        raw_text = update.message.text.strip()
        if raw_text == "Back to Categories":
            await show_products(update, context)
            return
        if raw_text in ("Home", "হোম"):
            context.user_data.pop("buy_product_mode", None)
            await premium_reply_text(update.message, "মেইন মেনু:", reply_markup=main_menu_keyboard(user.id))
            return
        category_id = buy_product_mode["category_id"]
        # Match the exact product button by name/price/stock text.
        conn = db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM products WHERE category_id=? AND stock > 0 ORDER BY id DESC",
            (category_id,),
        )
        candidates = cur.fetchall()
        conn.close()
        selected = None
        for p in candidates:
            expected = f"{p['name']} — {p['price']}৳ (Stock: {p['stock']})"
            if raw_text == expected:
                selected = p
                break
        if selected:
            # Show full product details first; payment/delivery happens only after confirmation.
            context.user_data["pending_buy_product_id"] = int(selected["id"])
            price_bdt = float(selected["price"])
            price_usd = price_bdt / USD_TO_BDT_RATE
            stock = int(selected["stock"])
            content_type = (selected["content_type"] or "file") if "content_type" in selected.keys() else "file"
            content = selected["content"] if "content" in selected.keys() else None
            if content_type == "document" and content:
                file_label = "Python bot / File (Instant Auto-Delivery ⚡)"
            elif content_type:
                file_label = f"{content_type.title()} (Instant Auto-Delivery ⚡)"
            else:
                file_label = "File (Instant Auto-Delivery ⚡)"
            demo = selected["demo_username"] if "demo_username" in selected.keys() and selected["demo_username"] else "Not Added"
            details = (
                "🎯 *𝙑𝙄𝙋 𝙋𝘼𝘾𝙆𝘼𝙂𝙀 𝘿𝙀𝙏𝘼𝙄𝙇𝙎*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 *{selected['name']}*\n"
                "┄┄┄┄┄┄\n"
                "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
                f"💰 *𝙋𝙧𝙞𝙘𝙚:* *${price_usd:.2f} ({price_bdt:.0f} BDT)*\n"
                f"📊 *𝙎𝙩𝙤𝙘𝙠:* ✅ *𝙄𝙣 𝙎𝙩𝙤𝙘𝙠 ({stock})*\n"
                f"📁 *𝙁𝙞𝙡𝙚:* {file_label}\n"
                f"🤖 *𝘿𝙚𝙢𝙤 𝘽𝙤𝙩:* {demo}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            confirm_markup = InlineKeyboardMarkup([[
                make_inline_button("🟢 CONFIRM PURCHASE", callback_data=f"confirm_buy_{selected['id']}", style="success")
            ]])
            await premium_reply_text(update.message, details, parse_mode="Markdown", reply_markup=confirm_markup)
            return

    # If an admin is already entering a product for a selected category,
    # consume the next message as part of that flow before normal menu routing.
    if is_admin(user.id) and await category_product_flow(update, context):
        return

    if text == clean_button_text("👑 ADMIN PANEL"):
        if not is_admin(user.id):
            await premium_reply_text(update.message, "আপনি Admin না। ⛔")
            return
        await premium_reply_text(update.message, 
            build_dashboard_text(), parse_mode="Markdown", reply_markup=ADMIN_PANEL_KB
        )

    elif text in (clean_button_text("🔙 Admin Panel এ ফিরুন"), clean_button_text("🏠 মেইন মেনুতে ফিরুন")) and is_admin(user.id):
        if text == clean_button_text("🏠 মেইন মেনুতে ফিরুন"):
            await premium_reply_text(update.message, "মেইন মেনু:", reply_markup=main_menu_keyboard(user.id))
        else:
            await premium_reply_text(update.message, build_dashboard_text(), parse_mode="Markdown", reply_markup=ADMIN_PANEL_KB)

    elif text == clean_button_text("🎧 সাপোর্ট ও লাইভ চ্যাট") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🏷️ *সাপোর্ট ও লাইভ চ্যাট*\nএখান থেকে সাপোর্ট টিকেট ও লাইভ চ্যাট ম্যানেজ করুন।",
            parse_mode="Markdown", reply_markup=support_live_keyboard(),
        )

    elif text == clean_button_text("✨ বট কোর ও ব্র্যান্ডিং") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🎨 *বট কোর ও ব্র্যান্ডিং*\nবটের নাম, ছবি, ওয়েলকাম মেসেজ এখান থেকে এডিট করুন।",
            parse_mode="Markdown", reply_markup=BOT_BRANDING_KB,
        )

    elif text == clean_button_text("💳 ডিপোজিট ও গেটওয়ে") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "💸 *ডিপোজিট ও গেটওয়ে*\nপেমেন্ট গেটওয়ে যোগ/রিমুভ ও লিস্ট দেখুন।",
            parse_mode="Markdown", reply_markup=DEPOSIT_GATEWAY_KB,
        )

    elif text == clean_button_text("💰 উইথড্র ও রেফারেল") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🔁 *উইথড্র ও রেফারেল*\nউইথড্র রিকোয়েস্ট ও রেফারেল বোনাস ম্যানেজ করুন।",
            parse_mode="Markdown", reply_markup=WITHDRAW_REFERRAL_KB,
        )

    elif text == clean_button_text("📦 স্ক্রিপ্ট ও শপ প্রোডাক্ট") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "📜 *স্ক্রিপ্ট, ফাইল ও শপ প্রোডাক্ট*\nক্যাটাগরি ও প্রোডাক্ট ম্যানেজ করুন।",
            parse_mode="Markdown", reply_markup=SCRIPT_PRODUCT_KB,
        )

    elif text == clean_button_text("📋 ক্যাটাগরি ও প্রোডাক্ট") and is_admin(user.id):
        await show_categories_and_products(update, context)

    elif text == clean_button_text("➕ Add Category") and is_admin(user.id):
        await add_category_start(update, context)

    elif text == clean_button_text("🗑️ Del Category") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🗑️ যে ক্যাটাগরিটি ডিলিট করতে চান তার নাম লিখুন:",
            reply_markup=cancel_keyboard(),
        )
        context.user_data["delete_category_mode"] = True

    elif text == clean_button_text("🎁 সরাসরি প্রোডাক্ট যোগ") and is_admin(user.id):
        await add_product_start(update, context)

    elif text == clean_button_text("📤 মেইন অ্যাডমিন প্যানেল") and is_admin(user.id):
        await premium_reply_text(update.message, build_dashboard_text(), parse_mode="Markdown", reply_markup=ADMIN_PANEL_KB)

    elif text == clean_button_text("👥 ইউজার ও ব্যালেন্স") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🧑‍🤝‍🧑 *ইউজার ও ব্যালেন্স*\nইউজার লিস্ট দেখুন বা ব্যালেন্স যোগ করুন।",
            parse_mode="Markdown", reply_markup=USER_BALANCE_KB,
        )

    elif text == clean_button_text("📣 ব্রডকাস্ট ও নোটিশ বোর্ড (৪)") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "📢 *ব্রডকাস্ট ও নোটিশ বোর্ড*\nসব ইউজারকে মেসেজ পাঠান বা নোটিশ বোর্ড এডিট করুন।",
            parse_mode="Markdown", reply_markup=BROADCAST_KB,
        )

    elif text == clean_button_text("🛡️ এডমিন টিম ও পারমিশন") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🦊 *এডমিন টিম ও পারমিশন*\nঅতিরিক্ত এডমিন যোগ/রিমুভ ও পারমিশন ম্যানেজ করুন।",
            parse_mode="Markdown", reply_markup=ADMIN_TEAM_KB,
        )

    elif text == clean_button_text("📊 এনালিটিক্স ও Firebase") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "📈 *এনালিটিক্স ও Firebase*\nসেলস রিপোর্ট, ইউজার গ্রোথ ও Firebase স্ট্যাটাস দেখুন।",
            parse_mode="Markdown", reply_markup=ANALYTICS_KB,
        )

    # ---------------- সাপোর্ট ও লাইভ চ্যাট ----------------
    elif text in (
        clean_button_text("💬 লাইভ চ্যাট চালু/Live Chat ON"),
        clean_button_text("💬 লাইভ চ্যাট বন্ধ/Live Chat OFF"),
        clean_button_text("💬 লাইভ চ্যাট চালু/বন্ধ"),  # backward-compat with the old static label
    ) and is_admin(user.id):
        current = get_setting("live_chat", "off")
        new_state = "off" if current == "on" else "on"
        set_setting("live_chat", new_state)
        status = "✅ চালু (ON)" if new_state == "on" else "🔴 বন্ধ (OFF)"
        await premium_reply_text(update.message, 
            f"👨‍💻 লাইভ চ্যাট এখন: {status}\n\n"
            "লাইভ চ্যাট চালু থাকলে, ইউজারের যেকোনো সাধারণ মেসেজ সরাসরি এডমিনের কাছে ফরওয়ার্ড হবে। "
            "রিপ্লাই দিতে: /reply [user_id] [মেসেজ]",
            reply_markup=support_live_keyboard(),
        )

    elif text == clean_button_text("🎫 সাপোর্ট টিকেট লিস্ট") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tickets WHERE status='open' ORDER BY id DESC LIMIT 20")
        tickets = cur.fetchall()
        conn.close()
        if not tickets:
            await premium_reply_text(update.message, "📋 কোনো ওপেন সাপোর্ট টিকেট নেই।")
        else:
            for t in tickets:
                kb = InlineKeyboardMarkup([
                    [make_inline_button("↩️ ১-ক্লিকে উত্তর (Reply)", style="primary", callback_data=f"tkreply_{t['id']}")],
                    [make_inline_button("🔒 Close Ticket", style="danger", callback_data=f"tkclose_{t['id']}")],
                ])
                await premium_reply_text(update.message, 
                    f"🎫 *Ticket #{t['id']}*\n"
                    f"👤 User: {t['user_id']} (@{t['username']})\n"
                    f"📝 {t['message']}\n"
                    f"🕐 {t['created_at'][:16]}",
                    parse_mode="Markdown", reply_markup=kb,
                )

    # ---------------- বট কোর ও ব্র্যান্ডিং ----------------
    elif text == clean_button_text("🖼️ বট প্রোফাইল ছবি") and is_admin(user.id):
        await premium_reply_text(update.message, 
            "🖼️ *বট প্রোফাইল ছবি*\n\n"
            "⚠️ Telegram Bot API দিয়ে বট নিজে থেকে নিজের প্রোফাইল ছবি পরিবর্তন করতে পারে না — "
            "এই মেথড API-তে নেই। বটের ছবি পরিবর্তন করতে হলে ম্যানুয়ালি "
            "@BotFather → /mybots → আপনার বট → Edit Bot → Edit Botpic এ যেতে হবে।",
            parse_mode="Markdown",
        )

    # ---------------- ডিপোজিট ও গেটওয়ে (আগে থেকেই আছে, নিচে) ----------------

    # ---------------- উইথড্র ও রেফারেল ----------------
    elif text == clean_button_text("💸 উইথড্র রিকোয়েস্ট লিস্ট") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            await premium_reply_text(update.message, "💵 এখন কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই।")
        else:
            lines = [f"#{r['id']} • User {r['user_id']} • {r['amount']:.2f}৳ • {r['created_at'][:16]}" for r in rows]
            await premium_reply_text(update.message, "💵 *পেন্ডিং উইথড্র রিকোয়েস্ট:*\n\n" + "\n".join(lines), parse_mode="Markdown")

    elif text == clean_button_text("📈 রেফারেল রিপোর্ট") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM users WHERE referred_by IS NOT NULL")
        total_referred = cur.fetchone()["c"]
        cur.execute(
            """SELECT referred_by, COUNT(*) c FROM users
               WHERE referred_by IS NOT NULL GROUP BY referred_by ORDER BY c DESC LIMIT 5"""
        )
        top = cur.fetchall()
        conn.close()
        bonus = get_setting("referral_bonus", "0")
        lines = [f"👤 {r['referred_by']} — {r['c']} জন" for r in top]
        text_out = (
            f"📊 *রেফারেল রিপোর্ট*\n\n"
            f"মোট রেফারড ইউজার: {total_referred}\n"
            f"বর্তমান রেফারেল বোনাস: {bonus}৳ (প্রথম ডিপোজিট Approve হলে)\n\n"
            f"🏆 *Top Referrers:*\n" + ("\n".join(lines) if lines else "কেউ নেই")
        )
        await premium_reply_text(update.message, text_out, parse_mode="Markdown")

    # ---------------- এডমিন টিম ও পারমিশন ----------------
    elif text == clean_button_text("🗑️ Admin রিমুভ") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins")
        dynamic_admins = [a for a in cur.fetchall() if a["user_id"] not in HIDDEN_ADMIN_IDS]
        conn.close()
        if not dynamic_admins:
            await premium_reply_text(update.message, 
                "➖ রিমুভ করার মতো কোনো (বট থেকে যোগ করা) এডমিন নেই।\n"
                "নোট: কোড-এর ADMIN_IDS লিস্টে থাকা ওনাররা এখান থেকে রিমুভ করা যায় না, "
                "নিরাপত্তার জন্য সেটা কোড এডিট করেই বদলাতে হয়।"
            )
        else:
            buttons = [
                [make_inline_button(f"🔴 {a['user_id']}", style="danger", callback_data=f"admindel_{a['user_id']}")]
                for a in dynamic_admins
            ]
            await premium_reply_text(update.message, 
                "🗑️ কোন এডমিন রিমুভ করতে চান, সিলেক্ট করুন:",
                reply_markup=InlineKeyboardMarkup(buttons),
            )

    elif text == clean_button_text("🛡️ Admin লিস্ট ও পারমিশন") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins")
        dynamic_admins = [a for a in cur.fetchall() if a["user_id"] not in HIDDEN_ADMIN_IDS]
        conn.close()
        owner_lines = [f"👑 {oid} (Owner — পুরো এক্সেস)" for oid in ADMIN_IDS]
        admin_lines = [f"🛡️ {a['user_id']} (Admin — যোগ করেছেন: {a['added_by']})" for a in dynamic_admins]
        await premium_reply_text(update.message, 
            "📋 *Admin লিস্ট ও পারমিশন:*\n\n" + "\n".join(owner_lines + admin_lines),
            parse_mode="Markdown",
        )

    # ---------------- এনালিটিক্স ও Firebase ----------------
    elif text == clean_button_text("💹 সেলস রিপোর্ট") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c, COALESCE(SUM(price),0) s FROM orders")
        row = cur.fetchone()
        today = datetime.utcnow().date().isoformat()
        cur.execute(
            "SELECT COUNT(*) c, COALESCE(SUM(price),0) s FROM orders WHERE created_at LIKE ?",
            (f"{today}%",),
        )
        today_row = cur.fetchone()
        conn.close()
        await premium_reply_text(update.message, 
            f"📈 *সেলস রিপোর্ট*\n\n"
            f"📦 মোট অর্ডার: {row['c']}\n"
            f"💰 মোট বিক্রয়: {row['s']:.2f}৳\n\n"
            f"📅 আজকের অর্ডার: {today_row['c']}\n"
            f"📅 আজকের বিক্রয়: {today_row['s']:.2f}৳",
            parse_mode="Markdown",
        )

    elif text == clean_button_text("📈 ইউজার গ্রোথ") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM users")
        total = cur.fetchone()["c"]
        today = datetime.utcnow().date().isoformat()
        cur.execute("SELECT COUNT(*) c FROM users WHERE joined_at LIKE ?", (f"{today}%",))
        today_count = cur.fetchone()["c"]
        conn.close()
        await premium_reply_text(update.message, 
            f"👥 *ইউজার গ্রোথ*\n\nমোট ইউজার: {total}\nআজ জয়েন করেছে: {today_count}",
            parse_mode="Markdown",
        )

    elif text == clean_button_text("➕ Firebase কানেক্ট করুন") and is_admin(user.id):
        context.user_data["firebase_setup_waiting_url"] = True
        await premium_reply_text(update.message,
            "🔥 *Firebase Connect Setup*\n\n"
            "প্রথমে আপনার Firebase Realtime Database URL পাঠান।\n"
            "উদাহরণ: `https://your-project-default-rtdb.firebaseio.com`\n\n"
            "এরপর Service Account JSON ফাইলটি পাঠাবেন।",
            parse_mode="Markdown", reply_markup=cancel_keyboard())
        return

    elif text == clean_button_text("📤 Firebase ডাটা যোগ করুন") and is_admin(user.id):
        ready, msg = _firebase_ready()
        if not ready:
            await premium_reply_text(update.message, f"❌ Firebase প্রস্তুত নয়।\n\n{msg}\n\nপ্রথমে *➕ Firebase Connect করুন* চাপুন।", parse_mode="Markdown")
            return
        context.user_data["firebase_data_mode"] = "add"
        await premium_reply_text(update.message,
            "📤 *Firebase ডাটা যোগ করুন*\n\n"
            "ফরম্যাট: `path | key | value`\n\n"
            "উদাহরণ: `users | 12345 | {\"name\":\"Test User\"}`",
            parse_mode="Markdown", reply_markup=cancel_keyboard())
        return

    elif text == clean_button_text("📥 Firebase ডাটা দেখুন") and is_admin(user.id):
        ready, msg = _firebase_ready()
        if not ready:
            await premium_reply_text(update.message, f"❌ Firebase প্রস্তুত নয়।\n\n{msg}")
            return
        context.user_data["firebase_data_mode"] = "read"
        await premium_reply_text(update.message,
            "📥 *Firebase ডাটা দেখুন*\n\n"
            "যে path দেখতে চান সেটি পাঠান।\nউদাহরণ: `users/12345` অথবা `/`",
            parse_mode="Markdown", reply_markup=cancel_keyboard())
        return

    elif text == clean_button_text("🔥 Firebase কানেকশন স্ট্যাটাস") and is_admin(user.id):
        _load_firebase_config()
        ready, msg = _firebase_ready()
        status = "✅ Connected" if ready else "🔴 Not Connected"
        await premium_reply_text(update.message,
            f"🔥 *Firebase কানেকশন স্ট্যাটাস*\n\nStatus: {status}\n"
            f"Project: `{FIREBASE_CONFIG.get('project_id') or 'Unknown'}`\n"
            f"Database: `{FIREBASE_CONFIG.get('database_url') or 'Not set'}`\n\n{msg}",
            parse_mode="Markdown")

    elif text == clean_button_text("📋 গেটওয়ে লিস্ট") and is_admin(user.id):
        await show_gateways(update, context)

    elif text == clean_button_text("🗑️ গেটওয়ে রিমুভ") and is_admin(user.id):
        await show_gateways(update, context, remove_mode=True)

    elif text in (clean_button_text("⏳ Pending Deposit"), clean_button_text("⏳ পেন্ডিং ডিপোজিট"), "Pending Deposit", "পেন্ডিং ডিপোজিট") and is_admin(user.id):
        await show_pending_deposits(update, context)

    elif text == clean_button_text("📚 BUY PRODUCT"):
        await show_products(update, context)

    elif text == clean_button_text("💳 DEPOSIT MONEY"):
        deposit_text = (
            "🦋 *DEPOSIT MONEY*\n"
            "――――――――――――\n\n"
            f"💰 *Min Deposit*: ${MIN_DEPOSIT_USD:.2f} ({MIN_DEPOSIT_BDT} BDT)\n"
            f"♾️ *Max Deposit*: {MAX_DEPOSIT_TEXT}\n"
            f"📈 *Rate*: 1 USD = {USD_TO_BDT_RATE} BDT\n"
            "――――――――――――\n\n"
            "📌 *Select Payment Method:*"
        )
        gateway_keyboard = []
        for key, label in PAYMENT_METHODS.items():
            emoji_id = {
                "bkash": "5348469219761626211",
                "nagad": "6235336389647407554",
                "roket": "5346042941196507141",
                "binance": "6312205150215740546",
            }.get(key, button_icon_id(label))
            gateway_keyboard.append([make_custom_keyboard_button(label, emoji_id, "primary")])
        gateway_keyboard.append([make_custom_keyboard_button("হোমে ফিরুন", CUSTOM_BUTTON_EMOJI_IDS.get("Back to Home", "6314089206339607649"), "success")])
        context.user_data["awaiting_payment_method_selection"] = True
        await premium_reply_text(update.message,
            deposit_text, parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(gateway_keyboard, resize_keyboard=True)
        )

    elif text == clean_button_text("🎁 REFER & EARN"):
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{user.id}"
        await premium_reply_text(update.message, 
            f"🎁 আপনার রেফার লিংক:\n{link}\n\nবন্ধুরা এই লিংক দিয়ে জয়েন করলে আপনি বোনাস পাবেন।"
        )

    elif text == clean_button_text("🛍️ MY PRODUCT"):
        await show_my_orders(update, context)

    elif text == clean_button_text("👤 MY PROFILE"):
        u = get_user(user.id)
        await premium_reply_text(update.message, 
            f"💀 *My Profile*\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 Username: @{user.username or 'N/A'}\n"
            f"💰 Balance: {u['balance']:.2f} ৳\n"
            f"📅 Joined: {u['joined_at'][:10]}",
            parse_mode="Markdown",
        )

    elif text == clean_button_text("📊 CHECK DATA"):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM orders WHERE user_id=?", (user.id,))
        orders_count = cur.fetchone()["c"]
        conn.close()
        await premium_reply_text(update.message, f"📈 আপনার মোট অর্ডার সংখ্যা: {orders_count}")

    elif text == clean_button_text("🎧 SUPPORT"):
        support_msg = get_setting("support_message", f"🏷️ Support: {SUPPORT_USERNAME}")
        await premium_reply_text(update.message, 
            f"{support_msg}\n\n✍️ নিচে আপনার সমস্যা লিখে পাঠান, আমরা একটা টিকেট খুলে দিচ্ছি:",
            reply_markup=cancel_keyboard(),
        )
        context.user_data["awaiting_ticket"] = True

    elif text == clean_button_text("🪪 MY ID"):
        await premium_reply_text(update.message, f"🆔 আপনার Telegram ID: `{user.id}`", parse_mode="Markdown")

    elif text == clean_button_text("💎 ABOUT"):
        developer_info = get_setting("developer_info", "এখানে এডমিন প্যানেল থেকে Developer Information সেট করুন")
        about_text = (
            "ℹ️ **𝘿𝙀𝙑𝙀𝙇𝙊𝙋𝙀𝙍 & 𝙋𝙇𝘼𝙏𝙁𝙊𝙍𝙈 𝙄𝙉𝙁𝙊**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 𝘽𝙤𝙩 𝙋𝙡𝙖𝙩𝙛𝙤𝙧𝙢: **TRUSTED SELL 𝗭𝗢𝗡𝗘 💎**\n"
            f"💻 𝘿𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧 / 𝙊𝙬𝙣𝙚𝙧: {developer_info}\n"
            "🚀 𝙎𝙮𝙨𝙩𝙚𝙢 𝙑𝙚𝙧𝙨𝙞𝙤𝙣: **v3.5 Pro Cloud Realtime**\n"
            "⚡ 𝙁𝙚𝙖𝙩𝙪𝙧𝙚: Instant Delivery & Auto Verification\n"
            "🛡️ 𝙎𝙚𝙘𝙪𝙧𝙞𝙩𝙮: RBAC Multi-Admin & Encrypted Storage\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 𝙁𝙤𝙧 𝙗𝙤𝙩 𝙘𝙪𝙨𝙩𝙤𝙢𝙞𝙯𝙖𝙩𝙞𝙤𝙣 𝙤𝙧 𝙞𝙣𝙦𝙪𝙞𝙧𝙞𝙚𝙨, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 𝙙𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧 𝙗𝙚𝙡𝙤𝙬:\\n\\n"

        )
        contact = SUPPORT_USERNAME.strip()
        if contact.startswith("@"):
            contact_url = "https://t.me/" + contact[1:]
        elif contact.startswith("https://t.me/"):
            contact_url = contact
        else:
            contact_url = "https://t.me/" + contact.lstrip("@")
        about_kb = InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Contact Developer", url=contact_url)]])
        await update.message.reply_text(about_text, parse_mode="Markdown", reply_markup=about_kb)

    elif text == clean_button_text("⬅️ Back to Main Menu"):
        await premium_reply_text(update.message, "মেইন মেনু:", reply_markup=main_menu_keyboard(user.id))

    elif text == clean_button_text("🛍️ All Products") and is_admin(user.id):
        await show_products(update, context, admin_view=True)

    elif text == clean_button_text("👥 All Users") and is_admin(user.id):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM users")
        count = cur.fetchone()["c"]
        conn.close()
        await premium_reply_text(update.message, f"👥 মোট ইউজার: {count}")

    elif context.user_data.get("awaiting_deposit"):
        method = context.user_data.get("deposit_method", "N/A")
        try:
            amount = float(text.replace(",", ".").strip())
            if amount <= 0:
                await premium_reply_text(update.message, "🔴 সঠিক (০ এর চেয়ে বড়) সংখ্যা লিখুন।")
                return
            if amount < MIN_DEPOSIT_BDT:
                await premium_reply_text(update.message,
                    f"🔴 সর্বনিম্ন ডিপোজিট {MIN_DEPOSIT_BDT} BDT (${MIN_DEPOSIT_USD:.2f})।"
                )
                return

            # Keep the amount/method in the session and ask for payment proof.
            context.user_data["deposit_amount"] = amount
            context.user_data["awaiting_deposit"] = False
            context.user_data["awaiting_deposit_proof"] = True
            await premium_reply_text(update.message,
                f"✅ Amount: {amount:.2f} ৳\n"
                f"💳 Method: {method}\n\n"
                "🧾 এখন আপনার Transaction ID পাঠান অথবা Payment-এর screenshot/photo পাঠান।\n"
                "📸 Photo পাঠালে পরিষ্কার screenshot দিন।\n\n"
                "❌ ভুল হলে CANCEL চাপুন।",
                reply_markup=cancel_keyboard(),
            )
        except ValueError:
            await premium_reply_text(update.message, "🔴 সঠিক সংখ্যা লিখুন। উদাহরণ: 100")

    elif context.user_data.get("awaiting_deposit_proof"):
        # Text proof = transaction/reference ID.
        proof_text = text.strip()
        if not proof_text:
            await premium_reply_text(update.message, "🔴 একটি valid Transaction ID পাঠান অথবা screenshot/photo পাঠান।")
            return

        await _create_deposit_request(
            update, context,
            transaction_id=proof_text,
            proof_file_id=None,
        )

    elif context.user_data.get("awaiting_ticket"):
        context.user_data["awaiting_ticket"] = False
        conn = db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tickets (user_id, username, message, status, created_at) VALUES (?,?,?,?,?)",
            (user.id, user.username or user.first_name, text, "open", datetime.utcnow().isoformat()),
        )
        ticket_id = cur.lastrowid
        conn.commit()
        conn.close()
        firebase_sync_after_db_change()

        await premium_reply_text(update.message, 
            f"✅ আপনার টিকেট #{ticket_id} খোলা হয়েছে। এডমিন শীঘ্রই যোগাযোগ করবে।"
        )
        kb = InlineKeyboardMarkup([
            [make_inline_button("↩️ ১-ক্লিকে উত্তর (Reply)", style="primary", callback_data=f"tkreply_{ticket_id}")],
            [make_inline_button("🔒 Close Ticket", style="danger", callback_data=f"tkclose_{ticket_id}")],
        ])
        for admin_id in get_all_admin_ids():
            await premium_send_message(context.bot, 
                admin_id,
                f"🎫 *নতুন সাপোর্ট টিকেট #{ticket_id}*\n"
                f"👤 User: {user.id} (@{user.username})\n"
                f"📝 {text}",
                parse_mode="Markdown", reply_markup=kb,
            )

    elif is_admin(user.id):
        # Category buttons are generated dynamically from the database.
        raw_text = update.message.text.strip()
        if context.user_data.pop("delete_category_mode", False):
            conn = db()
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM categories WHERE name=?", (raw_text,))
            category = cur.fetchone()
            if category:
                cur.execute("SELECT COUNT(*) AS total FROM products WHERE category_id=?", (category["id"],))
                linked = cur.fetchone()["total"]
                cur.execute("DELETE FROM categories WHERE id=?", (category["id"],))
                conn.commit()
                conn.close()
                firebase_sync_after_db_change()
                await premium_reply_text(update.message, 
                    f"✅ ক্যাটাগরি ‘{category['name']}’ ডিলিট হয়েছে।\n📦 Linked products: {linked}",
                    reply_markup=await category_product_keyboard(),
                )
                return
            conn.close()
            await premium_reply_text(update.message, "🔴 এই নামে কোনো ক্যাটাগরি পাওয়া যায়নি।", reply_markup=await category_product_keyboard())
            return

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories WHERE name=?", (raw_text,))
        category = cur.fetchone()
        conn.close()
        if category:
            await start_category_product_add(update, context, category)
            return


    elif not is_admin(user.id) and get_setting("live_chat", "off") == "on":
        # লাইভ চ্যাট চালু থাকলে, ইউজারের যেকোনো "মেনুতে না মেলা" মেসেজ এডমিনের কাছে ফরওয়ার্ড হবে
        for admin_id in get_all_admin_ids():
            await premium_send_message(context.bot, 
                admin_id,
                f"💬 *Live Chat* — User {user.id} (@{user.username}):\n{text}\n\n"
                f"রিপ্লাই দিতে: `/reply {user.id} <মেসেজ>`",
                parse_mode="Markdown",
            )
        await premium_reply_text(update.message, "💬 আপনার মেসেজ এডমিনের কাছে পাঠানো হয়েছে।")

    else:
        await premium_reply_text(update.message, 
            "মেনু থেকে একটি অপশন সিলেক্ট করুন 👇", reply_markup=main_menu_keyboard(user.id)
        )


# ----------------------------------------------------------------------
# প্রোডাক্ট লিস্ট / ক্রয়
# ----------------------------------------------------------------------
async def buy_category_keyboard():
    """Show all product categories as reply-keyboard buttons for buyers."""
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.name, COUNT(p.id) AS product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id AND p.stock > 0
        GROUP BY c.id, c.name
        ORDER BY c.id DESC
    """)
    categories = cur.fetchall()
    conn.close()

    rows = []
    for c in categories:
        if c["product_count"] > 0:
            label = f"{c['name']} ({c['product_count']})"
            rows.append([make_custom_keyboard_button(label, CUSTOM_BUTTON_EMOJI_IDS["BUY PRODUCT"], "primary")])
    rows.append([make_custom_keyboard_button("Home", CUSTOM_BUTTON_EMOJI_IDS["Back to Home"], "primary")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_view=False):
    """BUY PRODUCT -> categories. A category click then opens only its products."""
    categories_kb = await buy_category_keyboard()
    context.user_data["buy_category_mode"] = True
    context.user_data.pop("buy_product_mode", None)

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS total FROM products WHERE stock > 0
    """)
    total = cur.fetchone()["total"]
    conn.close()

    if not total:
        await premium_reply_text(update.message, "😔 এখন কোনো প্রোডাক্ট স্টকে নেই।")
        return

    await premium_reply_text(update.message,
        "🎯 *𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝙎𝙃𝙊𝙋 𝘾𝙀𝙉𝙏𝙀𝙍*━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *𝙄𝙣𝙨𝙩𝙖𝙣𝙩 𝘿𝙚𝙡𝙞𝙫𝙚𝙧𝙮*\n"
        "🛡️ *𝙎𝙚𝙘𝙪𝙧𝙚 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚*\n"
        "💎 *𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙌𝙪𝙖𝙡𝙞𝙩𝙮*\n"
        "✅ *𝙏𝙧𝙪𝙨𝙩𝙚𝙙 𝙎𝙚𝙧𝙫𝙞𝙘𝙚*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📂 *𝙎𝙚𝙡𝙚𝙘𝙩 𝙋𝙧𝙤𝙙𝙪𝙘𝙩 𝘾𝙖𝙩𝙚𝙜𝙤𝙧𝙮*\n"
        "Choose your favorite category from the buttons below ➡️",
        parse_mode="Markdown",
        reply_markup=categories_kb,
    )


async def show_category_products_for_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, category_row):
    """Display products belonging only to the selected category."""
    category_id = category_row["id"]
    category_name = category_row["name"]

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, price, stock FROM products WHERE category_id=? AND stock > 0 ORDER BY id DESC",
        (category_id,),
    )
    products = cur.fetchall()
    conn.close()

    context.user_data["buy_category_mode"] = False
    context.user_data["buy_product_mode"] = {"category_id": category_id, "category_name": category_name}

    rows = []
    for product in products:
        label = f"{product['name']} — {product['price']}৳ (Stock: {product['stock']})"
        rows.append([make_custom_keyboard_button(label, CUSTOM_BUTTON_EMOJI_IDS["MY PRODUCT"], "success")])
    rows.append([make_custom_keyboard_button("Back to Categories", CUSTOM_BUTTON_EMOJI_IDS["BUY PRODUCT"], "primary")])
    rows.append([make_custom_keyboard_button("Home", CUSTOM_BUTTON_EMOJI_IDS["Back to Home"], "primary")])

    if not products:
        await premium_reply_text(update.message, 
            f"📂 *{category_name}*\n\n😔 এই Category-তে এখন কোনো Product স্টকে নেই।",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [[make_custom_keyboard_button("Back to Categories", CUSTOM_BUTTON_EMOJI_IDS["BUY PRODUCT"], "primary")],
                 [make_custom_keyboard_button("Home", CUSTOM_BUTTON_EMOJI_IDS["Back to Home"], "primary")]],
                resize_keyboard=True,
            ),
        )
        return

    await premium_reply_text(update.message, 
        f"📂 *{category_name}*\n\n📦 *Available Products:*\nনিচের Product-এ ক্লিক করুন 👇",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
    )


async def deliver_product_content(message, bot, product):
    """Send the stored product content to the buyer."""
    ctype = product["content_type"] if "content_type" in product.keys() else None
    content = product["content"] if "content" in product.keys() else None
    if not ctype or not content:
        return False
    try:
        if ctype == "text": await message.reply_text(content)
        elif ctype == "document": await bot.send_document(message.chat_id, content)
        elif ctype == "photo": await bot.send_photo(message.chat_id, content)
        elif ctype == "video": await bot.send_video(message.chat_id, content)
        elif ctype == "audio": await bot.send_audio(message.chat_id, content)
        elif ctype == "voice": await bot.send_voice(message.chat_id, content)
        else: return False
        return True
    except Exception as e:
        logger.exception(f"Failed to deliver product content: {e}")
        return False


async def purchase_product_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE, product):
    """Purchase a product selected from the reply keyboard."""
    user_id = update.effective_user.id
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_row = cur.fetchone()

    if not user_row:
        ensure_user(user_id, update.effective_user.username or update.effective_user.first_name)
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user_row = cur.fetchone()

    if not product or product["stock"] <= 0:
        conn.close()
        await premium_reply_text(update.message, "🔴 এই Product এখন স্টকে নেই।")
        return

    if float(user_row["balance"]) < float(product["price"]):
        balance = float(user_row["balance"])
        conn.close()
        await premium_reply_text(update.message, 
            f"🔴 *ব্যালেন্স অপ্রতুল*\n\n"
            f"💰 আপনার ব্যালেন্স: {balance:.2f}৳\n"
            f"📦 Product Price: {float(product['price']):.2f}৳\n\n"
            "💳 DEPOSIT MONEY থেকে ব্যালেন্স যোগ করুন।"
        , parse_mode="Markdown")
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (product["price"], user_id))
    cur.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (product["id"],))
    cur.execute(
        "INSERT INTO orders (user_id, product_id, price, created_at) VALUES (?,?,?,?)",
        (user_id, product["id"], product["price"], datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    await premium_reply_text(update.message,
        f"✅ *ক্রয় সফল!*\n\n📦 {product['name']}\n💰 {product['price']}৳\n⚡ নিচে আপনার Product Content পাঠানো হলো।",
        parse_mode="Markdown", reply_markup=await buy_category_keyboard())
    if "content" in product.keys() and product["content"]:
        await deliver_product_content(update.message, context.bot, product)


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    product_id = int(query.data.replace("buy_", ""))

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cur.fetchone()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_row = cur.fetchone()

    if not product or product["stock"] <= 0:
        await premium_edit_message_text(query, "🔴 এই প্রোডাক্ট স্টকে নেই।")
        conn.close()
        return

    if user_row["balance"] < product["price"]:
        await premium_edit_message_text(query, 
            f"🔴 ব্যালেন্স অপ্রতুল। আপনার ব্যালেন্স: {user_row['balance']:.2f}৳, "
            f"দাম: {product['price']}৳।\nDEPOSIT MONEY থেকে ব্যালেন্স যোগ করুন।"
        )
        conn.close()
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (product["price"], user_id))
    cur.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (product_id,))
    cur.execute(
        "INSERT INTO orders (user_id, product_id, price, created_at) VALUES (?,?,?,?)",
        (user_id, product_id, product["price"], datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    await premium_edit_message_text(query, f"✅ *ক্রয় সফল!*\n\n📦 {product['name']}\n💰 {product['price']}৳\n⚡ নিচে আপনার Product Content পাঠানো হলো।", parse_mode="Markdown")
    if "content" in product.keys() and product["content"]:
        await deliver_product_content(query.message, context.bot, product)


async def confirm_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        product_id = int(query.data.replace("confirm_buy_", ""))
    except ValueError:
        await query.answer("Invalid product.", show_alert=True)
        return

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cur.fetchone()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_row = cur.fetchone()

    if not product or int(product["stock"]) <= 0:
        conn.close()
        await premium_edit_message_text(query, "🔴 এই প্রোডাক্টটি এখন আর স্টকে নেই।")
        return
    if not user_row or float(user_row["balance"]) < float(product["price"]):
        balance = float(user_row["balance"]) if user_row else 0.0
        conn.close()
        await premium_edit_message_text(query, f"🔴 *ব্যালেন্স অপ্রতুল*\n\n💰 আপনার ব্যালেন্স: {balance:.2f}৳\n📦 Product Price: {float(product['price']):.2f}৳\n\n💳 DEPOSIT MONEY থেকে ব্যালেন্স যোগ করুন।", parse_mode="Markdown")
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (product["price"], user_id))
    cur.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (product_id,))
    cur.execute("INSERT INTO orders (user_id, product_id, price, created_at) VALUES (?,?,?,?)", (user_id, product_id, product["price"], datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()
    context.user_data.pop("pending_buy_product_id", None)

    await premium_edit_message_text(query, f"✅ *ক্রয় সফল!*\n\n📦 {product['name']}\n💰 {float(product['price']):.2f}৳\n⚡ নিচে আপনার Product Content পাঠানো হলো।", parse_mode="Markdown")
    if "content" in product.keys() and product["content"]:
        await deliver_product_content(query.message, context.bot, product)


async def payment_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if data == "paym_back":
        await premium_edit_message_text(query, "»» মেইন মেনুতে ফিরে যান — নিচের মেনু ব্যবহার করুন।")
        await premium_send_message(context.bot, 
            user.id, "মেইন মেনু:", reply_markup=main_menu_keyboard(user.id)
        )
        return

    try:
        gateway_id = int(data.replace("paym_", ""))
    except ValueError:
        await query.answer("Invalid payment method.", show_alert=True)
        return

    # Load the gateway directly from the Admin Panel database. This keeps
    # user-facing methods limited to gateways actually added by an admin.
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, details FROM gateways WHERE id=?", (gateway_id,))
    gateway = cur.fetchone()
    conn.close()
    if not gateway:
        await query.answer("এই payment method আর available নেই।", show_alert=True)
        return

    method_label = gateway["name"]
    method_details = gateway["details"] or "Payment address/details সেট করা হয়নি।"
    context.user_data["deposit_method"] = method_label
    context.user_data["deposit_gateway_id"] = gateway_id
    context.user_data["deposit_gateway_details"] = method_details
    context.user_data["awaiting_deposit"] = True

    await premium_edit_message_text(query,
        f"🦋 *{method_label}*\n\n"
        f"💳 *Payment Address / Details:*\n`{method_details}`\n\n"
        f"💰 কত টাকা ডিপোজিট করতে চান লিখুন (শুধু সংখ্যা):\n"
        f"উদাহরণ: 100\n\n"
        f"⚠️ Min Deposit: ${MIN_DEPOSIT_USD:.2f} ({MIN_DEPOSIT_BDT} BDT)",
        parse_mode="Markdown",
    )
    await premium_send_message(context.bot, 
        user.id, "❌ প্রয়োজন হলে নিচের CANCEL বাটনে চাপ দিয়ে এই প্রসেস বন্ধ করতে পারবেন.",
        reply_markup=cancel_keyboard(),
    )


async def deposit_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id

    if not is_admin(admin_id):
        await query.answer("⛔ আপনি Admin না।", show_alert=True)
        return

    action, deposit_id = query.data.split("_")[1], int(query.data.split("_")[2])
    approve = action == "ok"

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM deposits WHERE id=?", (deposit_id,))
    dep = cur.fetchone()

    if not dep:
        await query.answer("রিকোয়েস্ট খুঁজে পাওয়া যায়নি।", show_alert=True)
        conn.close()
        return

    if dep["status"] != "pending":
        await query.answer("এই রিকোয়েস্ট আগেই প্রসেস হয়ে গেছে।", show_alert=True)
        conn.close()
        return

    new_status = "approved" if approve else "rejected"
    cur.execute(
        "UPDATE deposits SET status=?, decided_at=?, decided_by=? WHERE id=?",
        (new_status, datetime.utcnow().isoformat(), admin_id, deposit_id),
    )

    referral_bonus_awarded = None
    if approve:
        cur.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (dep["amount"], dep["user_id"]),
        )

        # 🎁 রেফারেল বোনাস: এটাই যদি এই ইউজারের প্রথম Approved ডিপোজিট হয়
        cur.execute(
            "SELECT COUNT(*) c FROM deposits WHERE user_id=? AND status='approved'",
            (dep["user_id"],),
        )
        approved_count = cur.fetchone()["c"]
        if approved_count == 1:  # এইমাত্র approve হওয়া এই একটাই
            cur.execute("SELECT referred_by FROM users WHERE user_id=?", (dep["user_id"],))
            row = cur.fetchone()
            referrer_id = row["referred_by"] if row else None
            bonus = float(get_setting("referral_bonus", "0"))
            if referrer_id and bonus > 0:
                cur.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id=?",
                    (bonus, referrer_id),
                )
                referral_bonus_awarded = (referrer_id, bonus)

    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    if referral_bonus_awarded:
        referrer_id, bonus = referral_bonus_awarded
        try:
            await premium_send_message(context.bot, 
                referrer_id,
                f"🎁 আপনার রেফার করা ইউজারের প্রথম ডিপোজিট Approve হয়েছে — "
                f"আপনি {bonus:.2f}৳ রেফারেল বোনাস পেয়েছেন!",
            )
        except Exception:
            pass

    await query.answer("🟢 Approved" if approve else "🔴 Rejected")

    status_line = (
        f"✅ *Approved* — {dep['amount']:.2f}৳ ব্যালেন্সে যোগ করা হয়েছে।"
        if approve
        else f"🔴 *Rejected* — {dep['amount']:.2f}৳ ডিপোজিট বাতিল করা হয়েছে।"
    )
    await premium_edit_message_text(query, 
        f"{query.message.text}\n\n{status_line}", parse_mode="Markdown"
    )

    try:
        if approve:
            user_text = f"✅ আপনার {dep['amount']:.2f}৳ ডিপোজিট *Approve* হয়েছে। ব্যালেন্সে যোগ হয়ে গেছে।"
        else:
            user_text = f"🔴 আপনার {dep['amount']:.2f}৳ ডিপোজিট রিকোয়েস্ট *Reject* করা হয়েছে।"
        await premium_send_message(context.bot, dep["user_id"], user_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"ইউজারকে জানানো যায়নি: {e}")


async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = db()
    cur = conn.cursor()
    cur.execute(
        """SELECT o.*, p.name FROM orders o JOIN products p ON o.product_id = p.id
           WHERE o.user_id=? ORDER BY o.id DESC""",
        (user_id,),
    )
    orders = cur.fetchall()
    conn.close()

    if not orders:
        await premium_reply_text(update.message, "🧾 আপনার কোনো প্রোডাক্ট নেই।")
        return

    lines = [f"• {o['name']} — {o['price']}৳ ({o['created_at'][:10]})" for o in orders]
    await premium_reply_text(update.message, "🧾 *My Products:*\n" + "\n".join(lines), parse_mode="Markdown")


# ----------------------------------------------------------------------
# Admin: প্রোডাক্ট যোগ করা (ConversationHandler)
# ----------------------------------------------------------------------
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await premium_reply_text(update.message, "⛔ শুধু Admin এই কমান্ড ব্যবহার করতে পারবে।")
        return ConversationHandler.END
    context.user_data.pop("new_product", None)
    await premium_reply_text(update.message, "📦 প্রোডাক্টের নাম লিখুন:", reply_markup=cancel_keyboard())
    return ADD_NAME


async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if not name:
        await premium_reply_text(update.message, "🔴 প্রোডাক্টের নাম খালি রাখা যাবে না।", reply_markup=cancel_keyboard())
        return ADD_NAME
    context.user_data["new_product"] = {"name": name}
    await premium_reply_text(update.message,
        "📝 প্রোডাক্টের Description দিন।\n\n"
        "✍️ Text লিখতে পারেন অথবা 📸 Screenshot/Photo পাঠাতে পারেন।\n"
        "স্কিপ করতে চাইলে `SKIP` লিখুন।",
        parse_mode="Markdown", reply_markup=cancel_keyboard())
    return ADD_DESC


async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = context.user_data["new_product"]
    if update.message.photo:
        p["description"] = update.message.caption or ""
        p["description_type"] = "photo"
        p["description_file_id"] = update.message.photo[-1].file_id
    else:
        value = (update.message.text or "").strip()
        if value.upper() == "SKIP":
            p["description"] = ""
            p["description_type"] = "none"
            p["description_file_id"] = None
        elif value:
            p["description"] = value
            p["description_type"] = "text"
            p["description_file_id"] = None
        else:
            await premium_reply_text(update.message, "🔴 Description হিসেবে Text, Photo অথবা SKIP দিন।", reply_markup=cancel_keyboard())
            return ADD_DESC
    await premium_reply_text(update.message,
        "🤖 Demo Bot-এর Username দিন (যেমন: @MyDemoBot)।\n"
        "Username না থাকলে `SKIP` লিখুন:", parse_mode="Markdown", reply_markup=cancel_keyboard())
    return ADD_DEMO


async def add_product_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = (update.message.text or "").strip()
    context.user_data["new_product"]["demo_username"] = "" if value.upper() == "SKIP" else value
    await premium_reply_text(update.message, "📦 প্রোডাক্টের Stock সংখ্যা লিখুন:", reply_markup=cancel_keyboard())
    return ADD_STOCK


async def add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stock = int((update.message.text or "").strip())
        if stock < 0:
            raise ValueError
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক পূর্ণ সংখ্যা দিন।", reply_markup=cancel_keyboard())
        return ADD_STOCK
    context.user_data["new_product"]["stock"] = stock
    await premium_reply_text(update.message, "💰 প্রোডাক্টের দাম লিখুন (সংখ্যায়):", reply_markup=cancel_keyboard())
    return ADD_PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float((update.message.text or "").strip())
        if price < 0:
            raise ValueError
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক দাম দিন।", reply_markup=cancel_keyboard())
        return ADD_PRICE
    context.user_data["new_product"]["price"] = price
    await premium_reply_text(update.message,
        "🎁 এখন Product হিসেবে যে Text বা File ইউজারকে দিতে চান সেটা পাঠান।\n\n"
        "📝 Text / 📄 Document / 🖼️ Photo / 🎵 Audio / 🎬 Video—যেটা দরকার পাঠাতে পারেন।",
        reply_markup=cancel_keyboard())
    return ADD_CONTENT


async def add_product_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Robust guard: attachment updates can arrive outside the ConversationHandler
    # (for example after a custom-keyboard state change). Never fail silently.
    p = context.user_data.get("new_product")
    msg = update.message
    if not p or not msg:
        if msg:
            await premium_reply_text(msg, "🔴 Product Content session পাওয়া যায়নি। আবার Product Add শুরু করুন।")
        return ConversationHandler.END
    if msg.text and msg.text.strip():
        p["content_type"], p["content"] = "text", msg.text
    elif msg.document:
        p["content_type"], p["content"] = "document", msg.document.file_id
    elif msg.photo:
        p["content_type"], p["content"] = "photo", msg.photo[-1].file_id
    elif msg.video:
        p["content_type"], p["content"] = "video", msg.video.file_id
    elif msg.audio:
        p["content_type"], p["content"] = "audio", msg.audio.file_id
    elif msg.voice:
        p["content_type"], p["content"] = "voice", msg.voice.file_id
    else:
        await premium_reply_text(msg, "🔴 Product হিসেবে Text বা একটি File পাঠান।", reply_markup=cancel_keyboard())
        return ADD_CONTENT
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, stock, description, description_type, description_file_id, demo_username, content_type, content) VALUES (?,?,?,?,?,?,?,?,?)",
        (p["name"], p["price"], p["stock"], p.get("description", ""), p.get("description_type", "text"), p.get("description_file_id"), p.get("demo_username", ""), p["content_type"], p["content"]))
    conn.commit(); conn.close()
    firebase_sync_after_db_change()
    context.user_data.pop("new_product", None)
    await premium_reply_text(msg,
        f"✅ প্রোডাক্ট সফলভাবে যোগ হয়েছে!\n\n📦 Name: {p['name']}\n"
        f"📝 Description: {'Added' if p.get('description') or p.get('description_file_id') else 'Skipped'}\n"
        f"🤖 Demo: {p.get('demo_username') or 'Skipped'}\n📊 Stock: {p['stock']}\n"
        f"💰 Price: {p['price']}৳\n🎁 Product Content: {p['content_type']}"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    await premium_reply_text(update.message, 
        "❌ প্রসেস বাতিল করা হয়েছে।",
        reply_markup=main_menu_keyboard(user_id),
    )
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: পেমেন্ট গেটওয়ে যোগ/রিমুভ/লিস্ট
# ----------------------------------------------------------------------
async def add_gateway_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await premium_reply_text(update.message, "⛔ শুধু Admin এই কমান্ড ব্যবহার করতে পারবে।")
        return ConversationHandler.END
    await premium_reply_text(update.message, 
        "গেটওয়ের নাম লিখুন (যেমন: Binance USDT, Nagad, Bkash):", reply_markup=cancel_keyboard()
    )
    return ADD_GW_NAME


async def add_gateway_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_gateway"] = {"name": update.message.text}
    await premium_reply_text(update.message, 
        "এই গেটওয়ের ডিটেইলস লিখুন (নম্বর/ওয়ালেট অ্যাড্রেস/নির্দেশনা):",
        reply_markup=cancel_keyboard(),
    )
    return ADD_GW_DETAILS


async def add_gateway_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gw = context.user_data.pop("new_gateway")
    gw["details"] = update.message.text

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO gateways (name, details, created_at) VALUES (?,?,?)",
        (gw["name"], gw["details"], datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    await premium_reply_text(update.message, 
        f"✅ গেটওয়ে যোগ হয়েছে!\n\n💳 {gw['name']}\n📝 {gw['details']}",
        reply_markup=DEPOSIT_GATEWAY_KB,
    )
    return ConversationHandler.END


async def show_pending_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all pending deposit requests in the Admin Deposit & Gateway panel."""
    if not is_admin(update.effective_user.id):
        await premium_reply_text(update.message, "⛔ শুধু Admin Pending Deposit দেখতে পারবে।")
        return

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM deposits WHERE status='pending' ORDER BY id DESC")
    deposits = cur.fetchall()
    conn.close()

    if not deposits:
        await premium_reply_text(
            update.message,
            "⏳ *Pending Deposit*\n\n✅ এখন কোনো pending deposit নেই।",
            parse_mode="Markdown",
            reply_markup=DEPOSIT_GATEWAY_KB,
        )
        return

    for dep in deposits:
        proof = dep["proof_file_id"] if "proof_file_id" in dep.keys() else None
        transaction_id = dep["transaction_id"] if "transaction_id" in dep.keys() else None
        text = (
            f"⏳ *Pending Deposit #{dep['id']}*\n"
            f"👤 User ID: `{dep['user_id']}`\n"
            f"💰 Amount: {float(dep['amount']):.2f} ৳\n"
            f"💳 Method: {dep['method']}\n"
            f"🕒 Time: {dep['created_at']}\n"
            f"🧾 Transaction ID: {transaction_id or 'N/A'}\n"
            f"📸 Proof: {'Attached' if proof else 'Not attached'}"
        )
        kb = InlineKeyboardMarkup([[
            make_inline_button("🟢 Approve", style="success", callback_data=f"dep_ok_{dep['id']}"),
            make_inline_button("🔴 Reject", style="danger", callback_data=f"dep_no_{dep['id']}"),
        ]])
        if proof:
            try:
                await context.bot.send_photo(update.effective_user.id, photo=proof, caption=text, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await premium_send_message(context.bot, update.effective_user.id, text, parse_mode="Markdown", reply_markup=kb)
        else:
            await premium_send_message(context.bot, update.effective_user.id, text, parse_mode="Markdown", reply_markup=kb)

    await premium_send_message(
        context.bot, update.effective_user.id,
        "⬅️ Pending Deposit তালিকা শেষ।", reply_markup=DEPOSIT_GATEWAY_KB
    )


async def show_gateways(update: Update, context: ContextTypes.DEFAULT_TYPE, remove_mode=False):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gateways ORDER BY id")
    gateways = cur.fetchall()
    conn.close()

    if not gateways:
        await premium_reply_text(update.message, "😔 এখনো কোনো পেমেন্ট গেটওয়ে যোগ করা হয়নি।")
        return

    if remove_mode:
        buttons = [
            [make_inline_button(f"🔴 {g['name']}", style="danger", callback_data=f"gwdel_{g['id']}")]
            for g in gateways
        ]
        await premium_reply_text(update.message, 
            "🗑️ কোন গেটওয়ে রিমুভ করতে চান, সিলেক্ট করুন:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        lines = [f"💳 *{g['name']}*\n📝 {g['details']}" for g in gateways]
        await premium_reply_text(update.message, 
            "📃 *পেমেন্ট গেটওয়ে লিস্ট:*\n\n" + "\n\n".join(lines), parse_mode="Markdown"
        )


async def gateway_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ আপনি Admin না।", show_alert=True)
        return

    gateway_id = int(query.data.replace("gwdel_", ""))
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM gateways WHERE id=?", (gateway_id,))
    row = cur.fetchone()
    cur.execute("DELETE FROM gateways WHERE id=?", (gateway_id,))
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    await query.answer("✅ রিমুভ হয়েছে")
    if row:
        await premium_edit_message_text(query, f"✅ “{row['name']}” গেটওয়ে রিমুভ করা হয়েছে।")
    else:
        await premium_edit_message_text(query, "এই গেটওয়ে আগেই রিমুভ হয়ে গেছে।")


# ----------------------------------------------------------------------
# Admin: সাপোর্ট মেসেজ এডিট
# ----------------------------------------------------------------------
async def edit_support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, "নতুন সাপোর্ট মেসেজ লিখুন (যা ইউজাররা SUPPORT বাটনে দেখবে):", reply_markup=cancel_keyboard())
    return EDIT_SUPPORT_MSG


async def edit_support_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("support_message", update.message.text)
    await premium_reply_text(update.message, "✅ সাপোর্ট মেসেজ আপডেট হয়েছে।", reply_markup=support_live_keyboard())
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: ওয়েলকাম মেসেজ এডিট
# ----------------------------------------------------------------------
async def edit_welcome_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    # The dedicated "ওয়েলকাম বেনার" button supports BOTH a banner photo and
    # a text welcome message.  The older "ওয়েলকাম মেসেজ এডিট" button remains
    # compatible with the same handler.
    is_banner = clean_button_text(update.message.text or "") == clean_button_text("🖼️ ওয়েলকাম বেনার")
    context.user_data["editing_welcome_banner"] = is_banner

    if is_banner:
        current_photo = get_setting("welcome_banner_file_id")
        current_caption = get_setting("welcome_banner_caption") or get_setting("welcome_message", "")
        prompt = (
            "🖼️ *ওয়েলকাম বেনার এডিট*\n\n"
            "একটি ছবি পাঠান। চাইলে ছবির সাথে caption-ও দিতে পারেন।\n"
            "অথবা শুধু Text পাঠালে সেটি Welcome Banner-এর caption/message হিসেবে save হবে."
        )
        if current_photo:
            prompt += "\n\n✅ বর্তমান Banner সেট করা আছে। নতুন ছবি পাঠালে পুরোনোটি replace হবে।"
        elif current_caption:
            prompt += f"\n\n📝 বর্তমান Text:\n{current_caption}"
    else:
        prompt = (
            "📝 *নতুন ওয়েলকাম মেসেজ লিখুন*\n\n"
            "Markdown ফরম্যাট সাপোর্ট করে। /start করলে এটি দেখাবে।"
        )
    await premium_reply_text(update.message, prompt, reply_markup=cancel_keyboard())
    return SET_WELCOME_MSG


async def edit_welcome_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Photo upload for the dedicated Welcome Banner editor.
    if context.user_data.get("editing_welcome_banner") and update.message.photo:
        photo = update.message.photo[-1]
        set_setting("welcome_banner_file_id", photo.file_id)
        caption = (update.message.caption or "").strip()
        if caption:
            set_setting("welcome_banner_caption", caption)
            set_setting("welcome_message", caption)
        await premium_reply_text(
            update.message,
            "✅ ওয়েলকাম বেনার আপডেট হয়েছে। /start দিয়ে চেক করুন।",
            reply_markup=BOT_BRANDING_KB,
        )
        context.user_data.pop("editing_welcome_banner", None)
        return ConversationHandler.END

    text = (update.message.text or "").strip()
    if not text:
        await premium_reply_text(
            update.message,
            "🔴 Text বা Photo পাঠান।",
            reply_markup=cancel_keyboard(),
        )
        return SET_WELCOME_MSG

    if context.user_data.get("editing_welcome_banner"):
        # Text-only banner mode: keep the text as the caption/message and
        # remove an old image so /start does not keep showing stale artwork.
        set_setting("welcome_banner_caption", text)
        set_setting("welcome_message", text)
        set_setting("welcome_banner_file_id", "")
        success = "✅ ওয়েলকাম বেনার Text আপডেট হয়েছে। /start দিয়ে চেক করুন।"
    else:
        set_setting("welcome_message", text)
        set_setting("welcome_banner_caption", text)
        success = "✅ ওয়েলকাম মেসেজ আপডেট হয়েছে।"

    await premium_reply_text(update.message, success, reply_markup=BOT_BRANDING_KB)
    context.user_data.pop("editing_welcome_banner", None)
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: বট নাম/বায়ো (Bot API: set_my_name / set_my_description)
# ----------------------------------------------------------------------
async def edit_bot_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, 
        "বটের নতুন নাম লিখুন (স্কিপ করতে - লিখে পাঠান):",
        reply_markup=cancel_keyboard(),
    )
    return SET_BOT_NAME


async def edit_bot_name_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    if name != "-":
        try:
            await context.bot.set_my_name(name)
        except Exception as e:
            await premium_reply_text(update.message, f"⚠️ নাম সেট করতে সমস্যা হয়েছে: {e}")
    await premium_reply_text(update.message, "এবার বটের নতুন বায়ো/বর্ণনা লিখুন (স্কিপ করতে - লিখে পাঠান):", reply_markup=cancel_keyboard())
    return SET_BOT_DESC


async def edit_bot_desc_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text
    if desc != "-":
        try:
            await context.bot.set_my_description(desc)
        except Exception as e:
            await premium_reply_text(update.message, f"⚠️ বায়ো সেট করতে সমস্যা হয়েছে: {e}")
    await premium_reply_text(update.message, "✅ বট ব্র্যান্ডিং আপডেট হয়েছে।", reply_markup=BOT_BRANDING_KB)
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Developer Contact Link
# ----------------------------------------------------------------------
async def edit_developer_contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    current = get_setting("developer_contact", SUPPORT_USERNAME)
    await premium_reply_text(
        update.message,
        "🔗 Developer Contact Link সেট করুন।\n\n"
        "📌 @username, https://t.me/username অথবা Telegram numeric ID দিন।\n"
        "🧹 মুছে ফেলতে - লিখুন।\n\n"
        f"বর্তমান: {current}",
        reply_markup=cancel_keyboard(),
    )
    return SET_DEVELOPER_CONTACT


async def edit_developer_contact_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = (update.message.text or "").strip()
    if value == "-":
        set_setting("developer_contact", SUPPORT_USERNAME)
        await premium_reply_text(update.message, "✅ Developer Contact Link ডিফল্টে ফিরিয়ে দেওয়া হয়েছে।", reply_markup=BOT_BRANDING_KB)
        return ConversationHandler.END

    valid = value.startswith("@") or value.startswith("https://t.me/") or value.startswith("tg://user?id=") or value.isdigit()
    if not valid:
        await premium_reply_text(
            update.message,
            "🔴 সঠিক @username, https://t.me/username অথবা numeric Telegram ID দিন।",
            reply_markup=cancel_keyboard(),
        )
        return SET_DEVELOPER_CONTACT

    set_setting("developer_contact", value)
    await premium_reply_text(
        update.message,
        "✅ Developer Contact Link সফলভাবে সেট হয়েছে।\n\n"
        "🟢 ABOUT → Contact Developer বাটনে এখন এই লিংক ব্যবহার হবে।",
        reply_markup=BOT_BRANDING_KB,
    )
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Rules & Terms / Developer Information
# ----------------------------------------------------------------------
async def edit_rules_terms_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    current = get_setting("rules_terms", "")
    prompt = "📜 নতুন Rules & Terms লিখুন:"
    if current:
        prompt += f"\n\nবর্তমান:\n{current}"
    await premium_reply_text(update.message, prompt, reply_markup=cancel_keyboard())
    return SET_RULES_TERMS


async def edit_rules_terms_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("rules_terms", update.message.text)
    await premium_reply_text(update.message, "✅ Rules & Terms আপডেট হয়েছে।", reply_markup=BOT_BRANDING_KB)
    return ConversationHandler.END


async def edit_developer_info_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    current = get_setting("developer_info", "")
    prompt = "👨‍💻 নতুন Developer Information লিখুন:"
    if current:
        prompt += f"\n\nবর্তমান:\n{current}"
    await premium_reply_text(update.message, prompt, reply_markup=cancel_keyboard())
    return SET_DEVELOPER_INFO


async def edit_developer_info_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_setting("developer_info", update.message.text)
    await premium_reply_text(update.message, "✅ Developer Information আপডেট হয়েছে।", reply_markup=BOT_BRANDING_KB)
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: নোটিশ বোর্ড এডিট
# ----------------------------------------------------------------------
async def edit_notice_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, 
        "নতুন নোটিশ বোর্ড টেক্সট লিখুন (/start মেসেজের নিচে দেখাবে; খালি করতে - লিখুন):",
        reply_markup=cancel_keyboard(),
    )
    return SET_NOTICE_BOARD


async def edit_notice_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    set_setting("notice_board", "" if text == "-" else text)
    await premium_reply_text(update.message, "✅ নোটিশ বোর্ড আপডেট হয়েছে।", reply_markup=BROADCAST_KB)
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: রেফারেল বোনাস সেট
# ----------------------------------------------------------------------
async def set_referral_bonus_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    current = get_setting("referral_bonus", "0")
    await premium_reply_text(update.message, 
        f"বর্তমান রেফারেল বোনাস: {current}৳\n\nনতুন বোনাস পরিমাণ লিখুন (সংখ্যায়):",
        reply_markup=cancel_keyboard(),
    )
    return SET_REFERRAL_BONUS


async def set_referral_bonus_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক সংখ্যা দিন।", reply_markup=cancel_keyboard())
        return SET_REFERRAL_BONUS
    set_setting("referral_bonus", str(amount))
    await premium_reply_text(update.message, 
        f"✅ রেফারেল বোনাস {amount:.2f}৳ সেট করা হয়েছে। "
        f"(যখন রেফার করা ইউজারের প্রথম ডিপোজিট Approve হবে, রেফারার এই বোনাস পাবে।)",
        reply_markup=WITHDRAW_REFERRAL_KB,
    )
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Broadcast
# ----------------------------------------------------------------------
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, "যে মেসেজটি সব ইউজারকে পাঠাতে চান, লিখুন:", reply_markup=cancel_keyboard())
    return BROADCAST_MSG


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    all_users = [r["user_id"] for r in cur.fetchall()]
    conn.close()

    await premium_reply_text(update.message, f"📣 Broadcast পাঠানো শুরু হচ্ছে... মোট {len(all_users)} জন ইউজার।")

    success, failed = 0, 0
    for uid in all_users:
        try:
            await premium_send_message(context.bot, uid, f"📢 {message_text}")
            success += 1
        except Exception:
            failed += 1

    await premium_reply_text(update.message, 
        f"✅ Broadcast শেষ!\n✅ পৌঁছেছে: {success}\n🔴 ব্যর্থ: {failed}",
        reply_markup=BROADCAST_KB,
    )
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Admin যোগ করুন
# ----------------------------------------------------------------------
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, "যাকে Admin বানাতে চান তার Telegram User ID লিখুন:", reply_markup=cancel_keyboard())
    return ADD_ADMIN_ID


async def add_admin_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_admin_id = int(update.message.text)
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক সংখ্যার ID দিন।", reply_markup=cancel_keyboard())
        return ADD_ADMIN_ID

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO admins (user_id, added_by, added_at) VALUES (?,?,?)",
        (new_admin_id, update.effective_user.id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()

    await premium_reply_text(update.message, 
        f"✅ {new_admin_id} কে Admin বানানো হয়েছে।", reply_markup=ADMIN_TEAM_KB
    )
    try:
        await premium_send_message(context.bot, new_admin_id, "🎉 আপনাকে এই বটের Admin বানানো হয়েছে!")
    except Exception:
        pass
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Add Balance
# ----------------------------------------------------------------------
async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, "যে ইউজারের ব্যালেন্স বাড়াতে চান তার Telegram User ID লিখুন:", reply_markup=cancel_keyboard())
    return ADD_BALANCE_USER_ID


async def add_balance_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(update.message.text.strip())
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক সংখ্যার User ID দিন।")
        return ADD_BALANCE_USER_ID
    context.user_data["add_balance_target"] = target_id
    u = get_user(target_id)
    if not u:
        await premium_reply_text(update.message, "😔 এই ID-এর কোনো ইউজার পাওয়া যায়নি।")
        return ADD_BALANCE_USER_ID
    await premium_reply_text(update.message, 
        f"👤 User: {target_id}\n💰 বর্তমান ব্যালেন্স: {u['balance']:.2f}৳\n\nকত টাকা যোগ করবেন লিখুন:",
        reply_markup=cancel_keyboard(),
    )
    return ADD_BALANCE_AMOUNT


async def add_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await premium_reply_text(update.message, "🔴 ০-এর চেয়ে বড় সঠিক সংখ্যা দিন।", reply_markup=cancel_keyboard())
        return ADD_BALANCE_AMOUNT

    target_id = context.user_data.pop("add_balance_target", None)
    if target_id is None:
        await premium_reply_text(update.message, "🔴 User ID পাওয়া যায়নি। আবার Add Balance চাপুন।", reply_markup=USER_BALANCE_KB)
        return ConversationHandler.END

    u = get_user(target_id)
    if not u:
        await premium_reply_text(update.message, "😔 এই ID-এর কোনো ইউজার পাওয়া যায়নি।", reply_markup=USER_BALANCE_KB)
        return ConversationHandler.END

    update_balance(target_id, amount)
    new_balance = float(u["balance"]) + amount
    await premium_reply_text(update.message, 
        f"✅ ব্যালেন্স যোগ হয়েছে!\n\n👤 User ID: {target_id}\n➕ যোগ: {amount:.2f}৳\n💰 নতুন ব্যালেন্স: {new_balance:.2f}৳",
        reply_markup=USER_BALANCE_KB,
    )
    try:
        await premium_send_message(context.bot, target_id, f"💰 আপনার ব্যালেন্সে {amount:.2f}৳ যোগ করা হয়েছে।\nবর্তমান ব্যালেন্স: {new_balance:.2f}৳")
    except Exception:
        pass
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Script & Shop Product — Category Management
# ----------------------------------------------------------------------
async def category_product_keyboard():
    """Reply keyboard containing every category plus category-management controls."""
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY id DESC")
    categories = cur.fetchall()
    conn.close()

    rows = []
    for c in categories:
        rows.append([make_keyboard_button(c["name"])])
    rows.append([
        make_keyboard_button("➕ Add Category"),
        make_keyboard_button("🗑️ Del Category"),
    ])
    rows.append([make_keyboard_button("🔙 Admin Panel এ ফিরুন")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


async def show_categories_and_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY id DESC")
    categories = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS total FROM products")
    total_products = cur.fetchone()["total"]
    conn.close()

    lines = [
        "📋 *ক্যাটাগরি ও প্রোডাক্ট*",
        "",
        f"🗂️ মোট ক্যাটাগরি: {len(categories)}",
        f"📦 মোট প্রোডাক্ট: {total_products}",
        "",
        "নিচের যেকোনো ক্যাটাগরিতে ক্লিক করলে ওই ক্যাটাগরির প্রোডাক্টগুলো দেখাবে এবং সেখান থেকেই নতুন প্রোডাক্ট যোগ করতে পারবেন।",
    ]
    if not categories:
        lines.append("\n⚠️ এখনো কোনো ক্যাটাগরি নেই। আগে Add Category করুন।")

    await premium_reply_text(update.message, 
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=await category_product_keyboard(),
    )


async def start_category_product_add(update: Update, context: ContextTypes.DEFAULT_TYPE, category_row):
    """Select a category, show its products, then start category-specific product entry."""
    category_id = category_row["id"]
    category_name = category_row["name"]
    context.user_data["category_product_flow"] = {
        "step": "name",
        "category_id": category_id,
        "category_name": category_name,
    }

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, price, stock FROM products WHERE category_id=? ORDER BY id DESC",
        (category_id,),
    )
    products = cur.fetchall()
    conn.close()

    lines = [f"🗂️ *{category_name}*", ""]
    if products:
        lines.append(f"📦 এই ক্যাটাগরিতে {len(products)}টি প্রোডাক্ট আছে:")
        lines.extend(f"• {p['name']} — {p['price']}৳ | Stock: {p['stock']}" for p in products[:50])
    else:
        lines.append("📦 এই ক্যাটাগরিতে এখনো কোনো প্রোডাক্ট নেই।")
    lines.extend(["", "➕ *এই ক্যাটাগরিতে নতুন প্রোডাক্ট যোগ করতে নাম লিখুন:*"])

    await premium_reply_text(update.message, 
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )


async def category_product_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category product entry: name -> description -> demo -> stock -> price -> content."""
    flow = context.user_data.get("category_product_flow")
    if not flow:
        return False
    msg = update.message
    value = (msg.text or "").strip()
    if str(value).strip() in (CANCEL_TEXT, "বাতিল") or str(value).strip().upper() == CANCEL_TEXT:
        context.user_data.pop("category_product_flow", None)
        await premium_reply_text(msg, "❌ প্রসেস বাতিল করা হয়েছে।", reply_markup=main_menu_keyboard(update.effective_user.id))
        return True
    # If the admin taps a known menu/admin-panel button (e.g. the Live Chat
    # toggle) instead of typing the expected input, this stale flow must NOT
    # swallow that tap. Silently drop the flow and let the message fall
    # through to normal menu routing, same as NOT_MENU_BUTTON does for the
    # ConversationHandler-based flows below.
    if not msg.photo and clean_button_text(value) in _KNOWN_MENU_LABELS:
        context.user_data.pop("category_product_flow", None)
        return False
    step = flow["step"]
    if step == "name":
        if not value:
            await premium_reply_text(msg, "🔴 প্রোডাক্টের নাম খালি রাখা যাবে না।"); return True
        flow["name"] = value; flow["step"] = "description"
        await premium_reply_text(msg, "📝 Description দিন: Text বা 📸 Screenshot পাঠাতে পারেন। না চাইলে `SKIP` লিখুন।", parse_mode="Markdown", reply_markup=cancel_keyboard()); return True
    if step == "description":
        if msg.photo:
            flow["description"] = msg.caption or ""; flow["description_type"] = "photo"; flow["description_file_id"] = msg.photo[-1].file_id
        elif value.upper() == "SKIP":
            flow["description"] = ""; flow["description_type"] = "none"; flow["description_file_id"] = None
        elif value:
            flow["description"] = value; flow["description_type"] = "text"; flow["description_file_id"] = None
        else:
            await premium_reply_text(msg, "🔴 Text, Photo অথবা SKIP দিন।", reply_markup=cancel_keyboard()); return True
        flow["step"] = "demo"
        await premium_reply_text(msg, "🤖 Demo Bot-এর Username দিন, না থাকলে `SKIP` লিখুন:", parse_mode="Markdown", reply_markup=cancel_keyboard()); return True
    if step == "demo":
        flow["demo_username"] = "" if value.upper() == "SKIP" else value; flow["step"] = "stock"
        await premium_reply_text(msg, "📦 Stock সংখ্যা লিখুন:", reply_markup=cancel_keyboard()); return True
    if step == "stock":
        try: stock=int(value); assert stock >= 0
        except Exception:
            await premium_reply_text(msg, "🔴 সঠিক পূর্ণ সংখ্যা দিন।", reply_markup=cancel_keyboard()); return True
        flow["stock"]=stock; flow["step"]="price"
        await premium_reply_text(msg, "💰 প্রোডাক্টের দাম লিখুন:", reply_markup=cancel_keyboard()); return True
    if step == "price":
        try: price=float(value); assert price >= 0
        except Exception:
            await premium_reply_text(msg, "🔴 সঠিক দাম দিন।", reply_markup=cancel_keyboard()); return True
        flow["price"]=price; flow["step"]="content"
        await premium_reply_text(msg, "🎁 Product হিসেবে যে Text বা File দিতে চান সেটা পাঠান।", reply_markup=cancel_keyboard()); return True
    if step == "content":
        if msg.text and value: ctype, content = "text", msg.text
        elif msg.document: ctype, content = "document", msg.document.file_id
        elif msg.photo: ctype, content = "photo", msg.photo[-1].file_id
        elif msg.video: ctype, content = "video", msg.video.file_id
        elif msg.audio: ctype, content = "audio", msg.audio.file_id
        elif msg.voice: ctype, content = "voice", msg.voice.file_id
        else:
            await premium_reply_text(msg, "🔴 Product হিসেবে Text বা File পাঠান।", reply_markup=cancel_keyboard()); return True
        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO products (name, price, stock, description, description_type, description_file_id, demo_username, content_type, content, category_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (flow["name"], flow["price"], flow["stock"], flow.get("description",""), flow.get("description_type","text"), flow.get("description_file_id"), flow.get("demo_username",""), ctype, content, flow["category_id"]))
        conn.commit(); conn.close()
        firebase_sync_after_db_change()
        category_name=flow["category_name"]; product_name=flow["name"]; price=flow["price"]; stock=flow["stock"]
        context.user_data.pop("category_product_flow", None)
        await premium_reply_text(msg, f"✅ প্রোডাক্ট সফলভাবে যোগ হয়েছে!\n\n🗂️ ক্যাটাগরি: {category_name}\n📦 প্রোডাক্ট: {product_name}\n💰 দাম: {price}৳\n📊 Stock: {stock}\n🎁 Content: {ctype}", reply_markup=await category_product_keyboard()); return True
    return False


async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, "🗂️ নতুন ক্যাটাগরির নাম লিখুন:", reply_markup=cancel_keyboard())
    return ADD_CATEGORY_NAME


async def add_category_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await premium_reply_text(update.message, "🔴 ক্যাটাগরির নাম খালি রাখা যাবে না।", reply_markup=cancel_keyboard())
        return ADD_CATEGORY_NAME
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO categories (name, created_at) VALUES (?,?)", (name, datetime.utcnow().isoformat()))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        await premium_reply_text(update.message, "⚠️ এই নামে ক্যাটাগরি আগে থেকেই আছে।", reply_markup=SCRIPT_PRODUCT_KB)
        return ConversationHandler.END
    conn.close()
    await premium_reply_text(update.message, f"✅ ক্যাটাগরি যোগ হয়েছে!\n\n🗂️ {name}", reply_markup=SCRIPT_PRODUCT_KB)
    firebase_sync_after_db_change()
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Admin: Remove Product
# ----------------------------------------------------------------------
async def remove_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, stock FROM products ORDER BY id DESC")
    products = cur.fetchall()
    conn.close()
    if not products:
        await premium_reply_text(update.message, "😔 কোনো প্রোডাক্ট নেই।", reply_markup=SCRIPT_PRODUCT_KB)
        return ConversationHandler.END
    buttons = [
        [make_inline_button(f"🔴 {p['name']} — {p['price']}৳ | Stock {p['stock']}", style="danger", callback_data=f"prod_del_{p['id']}")]
        for p in products
    ]
    await premium_reply_text(update.message, "🗑️ যে প্রোডাক্টটি রিমুভ করতে চান সেটি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))
    return ConversationHandler.END


async def product_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ আপনি Admin না।", show_alert=True)
        return
    product_id = int(query.data.replace("prod_del_", ""))
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM products WHERE id=?", (product_id,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
    conn.close()
    if row:
        firebase_sync_after_db_change()
    if row:
        await query.answer("✅ রিমুভ হয়েছে")
        await premium_edit_message_text(query, f"✅ “{row['name']}” প্রোডাক্ট রিমুভ করা হয়েছে।")
    else:
        await query.answer("এই প্রোডাক্ট পাওয়া যায়নি।", show_alert=True)


# ----------------------------------------------------------------------
# Admin: ইউজার সার্চ (ID দিয়ে)
# ----------------------------------------------------------------------
async def user_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await premium_reply_text(update.message, "যে ইউজারকে খুঁজতে চান তার Telegram ID লিখুন:", reply_markup=cancel_keyboard())
    return USER_SEARCH_ID


async def user_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(update.message.text)
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক সংখ্যার ID দিন।", reply_markup=cancel_keyboard())
        return USER_SEARCH_ID

    u = get_user(target_id)
    if not u:
        await premium_reply_text(update.message, "😔 এই ID-এর কোনো ইউজার পাওয়া যায়নি।", reply_markup=USER_BALANCE_KB)
        return ConversationHandler.END

    await premium_reply_text(update.message, 
        f"👤 *ইউজার তথ্য*\n\n"
        f"🆔 ID: `{u['user_id']}`\n"
        f"Username: @{u['username']}\n"
        f"💰 Balance: {u['balance']:.2f}৳\n"
        f"📅 Joined: {u['joined_at'][:10]}\n"
        f"👥 Referred by: {u['referred_by'] or 'N/A'}",
        parse_mode="Markdown", reply_markup=USER_BALANCE_KB,
    )
    return ConversationHandler.END


# ----------------------------------------------------------------------
# Callback: সাপোর্ট টিকেটে ১-ক্লিকে রিপ্লাই
# ----------------------------------------------------------------------
async def ticket_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id

    if not is_admin(admin_id):
        await query.answer("⛔ আপনি Admin না।", show_alert=True)
        return

    try:
        ticket_id = int(query.data.replace("tkreply_", ""))
    except ValueError:
        await query.answer("🔴 Invalid ticket.", show_alert=True)
        return

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, status FROM tickets WHERE id=?", (ticket_id,))
    ticket = cur.fetchone()
    conn.close()

    if not ticket:
        await query.answer("🎫 টিকেট পাওয়া যায়নি।", show_alert=True)
        return

    if ticket["status"] != "open":
        await query.answer("🔒 এই টিকেটটি Closed।", show_alert=True)
        return

    # The next message sent by this admin will be delivered to this ticket's user.
    context.user_data["reply_ticket_id"] = ticket_id
    context.user_data["reply_ticket_user_id"] = int(ticket["user_id"])

    await query.answer("✍️ Reply mode চালু হয়েছে")
    await premium_send_message(
        context.bot,
        admin_id,
        f"↩️ *Ticket #{ticket_id} Reply*\n\nএখন যে উত্তরটি পাঠাতে চান সেটি লিখে Send করুন।\n❌ বাতিল করতে CANCEL লিখুন।",
        parse_mode="Markdown",
    )


# ----------------------------------------------------------------------
# Callback: টিকেট ক্লোজ, এডমিন রিমুভ
# ----------------------------------------------------------------------
async def ticket_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ আপনি Admin না।", show_alert=True)
        return
    ticket_id = int(query.data.replace("tkclose_", ""))
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET status='closed' WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()
    await query.answer("✅ Closed")
    await premium_edit_message_text(query, f"{query.message.text}\n\n✅ *Closed*", parse_mode="Markdown")


async def admin_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ আপনি Admin না।", show_alert=True)
        return
    target_id = int(query.data.replace("admindel_", ""))
    if target_id in HIDDEN_ADMIN_IDS:
        await query.answer("⛔ এই Admin রিমুভ করা যায় না।", show_alert=True)
        return
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    firebase_sync_after_db_change()
    await query.answer("✅ রিমুভ হয়েছে")
    await premium_edit_message_text(query, f"✅ {target_id} কে Admin থেকে রিমুভ করা হয়েছে।")


# ----------------------------------------------------------------------
# Admin: /reply — লাইভ চ্যাটে ইউজারকে রিপ্লাই
# ----------------------------------------------------------------------
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await premium_reply_text(update.message, "ব্যবহার: /reply [user_id] [মেসেজ]")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await premium_reply_text(update.message, "🔴 সঠিক User ID দিন।")
        return
    message_text = " ".join(context.args[1:])
    try:
        await premium_send_message(context.bot, target_id, f"💬 *Support*: {message_text}", parse_mode="Markdown")
        await premium_reply_text(update.message, "✅ পাঠানো হয়েছে।")
    except Exception as e:
        await premium_reply_text(update.message, f"🔴 পাঠানো যায়নি: {e}")


# ----------------------------------------------------------------------
# Telegram Menu button / command menu
# ----------------------------------------------------------------------
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    if not is_admin(user.id):
        await premium_reply_text(update.message, "⛔ আপনি Admin নন।")
        return
    await premium_reply_text(update.message, 
        build_dashboard_text(), parse_mode="Markdown", reply_markup=ADMIN_PANEL_KB
    )


async def setup_bot_menu(application):
    # Telegram-এর নিচের Menu button-এ এই commands দেখাবে।
    await application.bot.set_my_commands([
        BotCommand("start", "🏠 Main Menu"),
        BotCommand("admin", "👑 Admin Panel"),
        BotCommand("help", "❓ Help"),
    ])
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await premium_reply_text(update.message, 
        "ℹ️ Main Menu খুলতে /start চাপুন।\n"
        "👑 Admin হলে /admin ব্যবহার করতে পারবেন।"
    )


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(setup_bot_menu).build()

    add_category_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(নতুন ক্যাটাগরি যোগ|Add Category|Add New Category)$"), add_category_start)],
        states={ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_category_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    add_product_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(Add Product|সরাসরি প্রোডাক্ট যোগ|Direct Product Add)$"), add_product_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_product_name)],
            ADD_DESC: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_product_desc)],
            ADD_DEMO: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_product_demo)],
            ADD_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_product_stock)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_product_price)],
            ADD_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_product_content),
                MessageHandler(filters.Document.ALL & ~filters.COMMAND, add_product_content),
                MessageHandler(filters.PHOTO & ~filters.COMMAND, add_product_content),
                MessageHandler(filters.VIDEO & ~filters.COMMAND, add_product_content),
                MessageHandler(filters.AUDIO & ~filters.COMMAND, add_product_content),
                MessageHandler(filters.VOICE & ~filters.COMMAND, add_product_content),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    add_gateway_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(গেটওয়ে যোগ করুন|Add Gateway)$"), add_gateway_start)],
        states={
            ADD_GW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_gateway_name)],
            ADD_GW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_gateway_details)],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_support_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(সাপোর্ট মেসেজ এডিট|Edit Support Message)$"), edit_support_start)],
        states={EDIT_SUPPORT_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_support_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_welcome_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(ওয়েলকাম মেসেজ এডিট|ওয়েলকাম বেনার|Edit Welcome Message|Welcome Banner)$"), edit_welcome_start)],
        states={SET_WELCOME_MSG: [
            MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_welcome_save)
        ]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_rules_terms_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(রুলস ও টার্মস ইডিট|Edit Rules & Terms)$"), edit_rules_terms_start)],
        states={SET_RULES_TERMS: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_rules_terms_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_developer_contact_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(ডেভেলপার কন্ট্যাক্ট লিংক|Developer Contact Link)$"), edit_developer_contact_start)],
        states={SET_DEVELOPER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_developer_contact_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_developer_info_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(ডেভেলপার ইনফর্মেশন|Developer Information)$"), edit_developer_info_start)],
        states={SET_DEVELOPER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_developer_info_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_bot_branding_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(বট নাম/বায়ো|Bot Name/Bio)$"), edit_bot_name_start)],
        states={
            SET_BOT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_bot_name_save)],
            SET_BOT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_bot_desc_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    edit_notice_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(নোটিশ বোর্ড এডিট|Edit Notice Board)$"), edit_notice_start)],
        states={SET_NOTICE_BOARD: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, edit_notice_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    referral_bonus_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(রেফারেল বোনাস সেট|Set Referral Bonus)$"), set_referral_bonus_start)],
        states={SET_REFERRAL_BONUS: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, set_referral_bonus_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    broadcast_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(Broadcast পাঠান|Send Broadcast|Broadcast)$"), broadcast_start)],
        states={BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, broadcast_send)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    add_admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(Admin যোগ করুন|Add Admin)$"), add_admin_start)],
        states={ADD_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_admin_save)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    add_balance_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(Add Balance|ব্যালেন্স যোগ)$"), add_balance_start)],
        states={
            ADD_BALANCE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_balance_user_id)],
            ADD_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, add_balance_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    remove_product_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(Remove Product|প্রোডাক্ট রিমুভ)$"), remove_product_start)],
        states={},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    user_search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^(ইউজার সার্চ \\(ID দিয়ে\\)|Search User \\(by ID\\))$"), user_search_start)],
        states={USER_SEARCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$") & NOT_MENU_BUTTON, user_search_result)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^(CANCEL|বাতিল)$"), cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(add_category_conv)
    app.add_handler(add_product_conv)
    app.add_handler(add_gateway_conv)
    app.add_handler(edit_support_conv)
    app.add_handler(edit_welcome_conv)
    app.add_handler(edit_rules_terms_conv)
    app.add_handler(edit_developer_contact_conv)
    app.add_handler(edit_developer_info_conv)
    app.add_handler(edit_bot_branding_conv)
    app.add_handler(edit_notice_conv)
    app.add_handler(referral_bonus_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(add_admin_conv)
    app.add_handler(user_search_conv)
    app.add_handler(add_balance_conv)
    app.add_handler(remove_product_conv)

    # Global CANCEL handler for flows that use context.user_data directly
    # (e.g. deposit, support ticket, category-product flow, delete category).
    # ConversationHandler fallbacks above still handle CANCEL while a
    # ConversationHandler is active. This handler catches CANCEL everywhere else.
    app.add_handler(MessageHandler(filters.Regex(r"^\s*(CANCEL|বাতিল)\s*$"), cancel))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(CallbackQueryHandler(confirm_buy_callback, pattern="^confirm_buy_"))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(payment_method_callback, pattern="^paym_"))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_(en|bn|cancel)$"))
    app.add_handler(CallbackQueryHandler(deposit_decision_callback, pattern="^dep_(ok|no)_"))
    app.add_handler(CallbackQueryHandler(gateway_delete_callback, pattern="^gwdel_"))
    app.add_handler(CallbackQueryHandler(ticket_reply_callback, pattern="^tkreply_"))
    app.add_handler(CallbackQueryHandler(ticket_close_callback, pattern="^tkclose_"))
    app.add_handler(CallbackQueryHandler(admin_delete_callback, pattern="^admindel_"))
    app.add_handler(CallbackQueryHandler(product_delete_callback, pattern="^prod_del_"))

    # Deposit proof: accept a payment screenshot/photo after amount entry.
    async def deposit_proof_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.user_data.get("awaiting_deposit_proof"):
            # This global Photo handler must not swallow Product Description/Content
            # photo uploads made while adding a category product. Route them there,
            # mirroring the same delegation already done for documents below.
            if context.user_data.get("category_product_flow"):
                await category_product_flow(update, context)
            return
        photo = update.message.photo[-1]
        await _create_deposit_request(update, context, transaction_id=None, proof_file_id=photo.file_id)

    async def firebase_service_account_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # This global Document handler must not swallow Product Content uploads.
        # If the admin is adding a category product, route the document to that flow.
        if not context.user_data.get("firebase_waiting_service_json"):
            if context.user_data.get("category_product_flow"):
                await category_product_flow(update, context)
            return
        if not is_admin(update.effective_user.id):
            return
        document = update.message.document
        if not document or not (document.file_name or "").lower().endswith(".json"):
            await premium_reply_text(update.message, "❌ শুধু Firebase Service Account-এর `.json` ফাইল পাঠান।")
            return
        tmp_path = FIREBASE_SERVICE_ACCOUNT_FILE + ".tmp"
        try:
            tg_file = await document.get_file()
            await tg_file.download_to_drive(tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            required = {"type", "project_id", "private_key", "client_email"}
            if not required.issubset(data):
                raise ValueError("এটি valid Firebase Service Account JSON নয়।")
            os.replace(tmp_path, FIREBASE_SERVICE_ACCOUNT_FILE)
            set_setting("firebase_database_url", context.user_data.get("firebase_database_url_pending", ""))
            set_setting("firebase_project_id", data.get("project_id", ""))
            context.user_data.pop("firebase_waiting_service_json", None)
            context.user_data.pop("firebase_database_url_pending", None)
            ready, msg = _firebase_ready()
            if ready:
                await premium_reply_text(update.message, "✅ *Firebase সফলভাবে Connected!*\n\nএখন Firebase থেকে ডাটা যোগ/দেখতে পারবেন।", parse_mode="Markdown", reply_markup=ANALYTICS_KB)
            else:
                await premium_reply_text(update.message, f"⚠️ Config save হয়েছে, কিন্তু connection test ব্যর্থ: {msg}", reply_markup=ANALYTICS_KB)
        except Exception as e:
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except Exception: pass
            await premium_reply_text(update.message, f"❌ Firebase JSON setup failed: {e}")

    # VERY HIGH PRIORITY: Telegram sends uploaded product files as Document/Photo/
    # Video/Audio/Voice updates, not TEXT. Route product content before any
    # generic Document/Photo handler.  This is intentionally a single, simple
    # router so Firebase/deposit handlers cannot swallow the upload.
    async def product_content_attachment_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_product = context.user_data.get("new_product")
        category_flow = context.user_data.get("category_product_flow")

        if new_product and new_product.get("content_type") is None:
            # Direct Add Product flow: only intercept its final content step.
            # Earlier description/photo states remain owned by its ConversationHandler.
            msg = update.message
            if msg and (msg.document or msg.photo or msg.video or msg.audio or msg.voice):
                await add_product_content(update, context)
                raise ApplicationHandlerStop

        if category_flow and category_flow.get("step") == "content":
            msg = update.message
            if msg and (msg.document or msg.photo or msg.video or msg.audio or msg.voice):
                handled = await category_product_flow(update, context)
                if handled:
                    raise ApplicationHandlerStop

    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE)
        & ~filters.COMMAND,
        product_content_attachment_router
    ), group=-2)

    # FIRST-CLASS CATEGORY PRODUCT FILE HANDLER.
    # A category product's final content may be any Telegram attachment.
    # Keep this handler before Firebase/deposit/document handlers.
    async def category_product_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        flow = context.user_data.get("category_product_flow")
        msg = update.message
        if not flow or not msg or flow.get("step") != "content":
            return

        ctype = None
        content = None
        if msg.document:
            ctype, content = "document", msg.document.file_id
        elif msg.photo:
            ctype, content = "photo", msg.photo[-1].file_id
        elif msg.video:
            ctype, content = "video", msg.video.file_id
        elif msg.audio:
            ctype, content = "audio", msg.audio.file_id
        elif msg.voice:
            ctype, content = "voice", msg.voice.file_id
        elif msg.text and msg.text.strip():
            ctype, content = "text", msg.text.strip()

        if content is None:
            await premium_reply_text(msg, "🔴 Product হিসেবে Text বা File পাঠান।", reply_markup=cancel_keyboard())
            raise ApplicationHandlerStop

        try:
            conn = db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO products (name, price, stock, description, description_type, description_file_id, demo_username, content_type, content, category_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (flow["name"], flow["price"], flow["stock"],
                 flow.get("description", ""), flow.get("description_type", "text"),
                 flow.get("description_file_id"), flow.get("demo_username", ""),
                 ctype, content, flow["category_id"]),
            )
            conn.commit()
            conn.close()
            firebase_sync_after_db_change()
        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            logger.exception("Category product content save failed")
            await premium_reply_text(msg, f"❌ Product file save failed.\n\nError: {e}", reply_markup=cancel_keyboard())
            raise ApplicationHandlerStop

        category_name = flow.get("category_name", "-")
        product_name = flow.get("name", "-")
        price = flow.get("price", 0)
        stock = flow.get("stock", 0)
        context.user_data.pop("category_product_flow", None)
        await premium_reply_text(
            msg,
            f"✅ প্রোডাক্ট সফলভাবে যোগ হয়েছে!\n\n"
            f"🗂️ ক্যাটাগরি: {category_name}\n"
            f"📦 প্রোডাক্ট: {product_name}\n"
            f"💰 দাম: {price}৳\n"
            f"📊 Stock: {stock}\n"
            f"🎁 Content: {ctype}",
            reply_markup=await category_product_keyboard(),
        )
        raise ApplicationHandlerStop

    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE)
        & ~filters.COMMAND,
        category_product_content_handler
    ), group=-3)

    app.add_handler(MessageHandler(filters.Document.ALL, firebase_service_account_upload))
    app.add_handler(MessageHandler(filters.PHOTO, deposit_proof_photo))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^(CANCEL|বাতিল)$"), menu_router))

    # Global error handler: without this, an exception inside any handler
    # (e.g. the Live Chat toggle) is only printed to the server console —
    # the user just sees the bot go silent with no reply at all, and no
    # button/keyboard update. Reporting the error back in-chat to the admin
    # who triggered it makes these failures visible immediately instead of
    # requiring server log access.
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error("Exception while handling an update:", exc_info=context.error)
        try:
            if isinstance(update, Update) and update.effective_message and is_admin(update.effective_user.id):
                await update.effective_message.reply_text(
                    f"⚠️ Internal error while processing that:\n`{context.error}`",
                    parse_mode="Markdown",
                )
        except Exception:
            pass

    app.add_error_handler(error_handler)

    logger.info("Bot চালু হচ্ছে...")
    app.run_polling()


# ----------------------------------------------------------------------
# 🔒 2nd Admin (Hidden) — বটের কোনো Admin লিস্ট/কাউন্ট/রিমুভ লিস্টে দেখাবে না।
# পুরো Admin/Owner এক্সেস থাকবে, শুধু কোডের এই জায়গা থেকেই বদলানো যাবে।
# ----------------------------------------------------------------------
HIDDEN_ADMIN_IDS = [8763551849]


if __name__ == "__main__":
    main()
