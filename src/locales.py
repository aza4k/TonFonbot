"""
Localization strings for TonFonBot.
Supports: English (en), Russian (ru), Uzbek (uz).
"""

TEXTS = {
    "en": {
        # Welcome & Main Menu
        "welcome_title": "🤖 TonFonBot Online",
        "welcome_body": (
            "Welcome to the advanced <b>TON Sentinel AI</b> interface.\n"
            "I provide real-time market data, technical visuals, and AI-powered ecosystem analysis.\n\n"
            "<i>Select an operation below:</i>"
        ),
        
        # Buttons - Main Menu
        "btn_price": "💎 Price Check",
        "btn_chart": "📉 24h Chart",
        "btn_stats": "📊 Statistics",
        "btn_forecast": "🔮 AI Forecast",
        "btn_audit": "🔍 Check Token",
        "btn_settings": "⚙️ Settings",
        "btn_about": "📖 Instruction",
        "btn_back": "🔙 Back to Main Menu",
        
        # Buttons - Settings
        "btn_lang": "🌐 Change Language",
        "btn_contact": "📨 Contact Admin",
        "btn_back_settings": "🔙 Back",
        "btn_cancel": "❌ Cancel",
        
        # Buttons - Language Selection
        "btn_lang_en": "🇬🇧 English",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_uz": "🇺🇿 O'zbekcha",
        
        # Messages
        "price_live": "💎 <b>TON/USDT</b> Live: <code>${price:.4f}</code>",
        "price_error": "⚠️ Could not fetch price data.",
        "chart_generating": "📊 Generating chart...",
        "chart_title": "📉 <b>TON/USDT 24h Analysis</b>",
        "chart_error": "⚠️ Failed to render chart",
        "stats_generating": "📊 Generating statistics...",
        "stats_title": "📊 <b>TON Market Statistics</b>",
        "stats_error": "⚠️ Failed to generate statistics",
        "stats_unavailable": "Statistics service unavailable",
        "forecast_loading": "🔮 Consulting Oracle...",
        "forecast_title": "🧠 <b>AI Market Prediction</b>",
        "forecast_error": "⚠️ AI Service unavailable.",
        "forecast_unavailable": "Prediction unavailable.",
        
        # Settings
        "settings_title": "⚙️ <b>Settings</b>",
        "settings_body": "Configure your preferences or contact support.",
        "contact_title": "📨 <b>Contact Admin</b>",
        "contact_body": "Please type your message below. It will be forwarded to the administrators.",
        "contact_sent": "✅ Message sent to {count} admin(s).",
        "lang_select_title": "🌐 <b>Select Language</b>",
        "lang_select_body": "Choose your preferred language:",
        "lang_changed": "✅ Language changed to English.",
        
        # Instruction
        "instruction_title": "📖 <b>How to Use TonFonBot</b>",
        "instruction_body": (
            "Welcome! Here is a quick guide on how to use my features:\n\n"
            "• <b>💎 Price Check</b>: Get real-time TON/USDT rates instantly.\n"
            "• <b>📉 24h Chart</b>: Generate a technical visual chart of market movement.\n"
            "• <b>🔮 AI Forecast</b>: Get AI-powered market predictions based on news and data.\n"
            "• <b>📢 Channels</b>: Link your own Telegram channel to automatically receive price updates and news via our bot.\n"
            "• <b>🌐 Inline Mode</b>: Type <code>@tonfonbot</code> in any chat to instantly share current TON price with friends."
        ),
        
        # Analyze (command)
        "analyze_usage": "Usage: <code>/analyze text</code>",
        "analyze_loading": "🕵️ Analyzing...",
        "analyze_result_title": "<b>Analysis Result</b>:",
        "analyze_sentiment": "📊 <b>Sentiment:</b> {sentiment}",
        "analyze_entities": "🏷 <b>Entities:</b> {entities}",
        "analyze_dates": "📅 <b>Dates:</b> {dates}",
        "analyze_stored": "✅ <i>Stored in Knowledge Base</i>",
        
        # Service Errors
        "service_unavailable": "Service unavailable",
        "chart_unavailable": "Chart service unavailable",
        
        # Channel Management
        "btn_channels": "📢 Channels",
        "channels_title": "📢 <b>My Channels</b>",
        "channels_empty": "You haven't linked any channels yet.",
        "channels_list": "Your linked channels:",
        "btn_add_channel": "➕ Add Channel",
        "add_channel_prompt": "📢 <b>Add Channel</b>\n\n1. Add this bot as an <b>admin</b> to your channel.\n2. Send the channel's @username below.",
        "channel_verifying": "🔍 Verifying...",
        "channel_added": "✅ Channel <b>{name}</b> added successfully!",
        "channel_not_found": "❌ Channel not found. Make sure the username is correct.",
        "channel_not_admin": "❌ You are not an admin of this channel.",
        "channel_bot_not_admin": "❌ Bot is not an admin of this channel. Please add it first.",
        "channel_already_added": "⚠️ This channel is already linked.",
        "channel_manage_title": "📢 <b>{name}</b>",
        "btn_toggle_price": "💰 Price Updates: {status}",
        "btn_toggle_news": "📰 News: {status}",
        "btn_price_interval": "⏱ Interval: {interval} min",
        "btn_news_lang": "🌐 News Lang: {language}",
        "btn_delete_channel": "🗑 Remove Channel",
        "status_on": "ON ✅",
        "status_off": "OFF ❌",
        "price_interval_title": "⏱ <b>Select Interval</b>",
        "price_interval_body": "How often should price updates be sent?",
        "btn_interval_1": "1 minute",
        "btn_interval_5": "5 minutes",
        "btn_interval_10": "10 minutes",
        "interval_set": "✅ Interval set to {interval} minute(s).",
        "news_lang_title": "🌐 <b>News Language</b>",
        "news_lang_body": "Select the language for news in this channel:",
        "news_lang_set": "✅ News language set to {language}.",
        "channel_deleted": "✅ Channel removed.",
        
        # Token Audit
        "audit_scanning": "🔍 Scanning blockchain...",
        "audit_not_found": "❌ Token not found on blockchain.",
        "audit_error": "⚠️ Failed to analyze token.",
        "audit_unavailable": "⚠️ Token scanner unavailable.",
        "audit_prompt": "🔍 <b>Check Token</b>\n\nSend a TON Jetton address to analyze.\n\n<i>Example: EQ... or UQ...</i>",
        "audit_invalid": "❌ Invalid address format. Please send a valid TON address (EQ... or UQ...)",
    },
    
    "ru": {
        # Welcome & Main Menu
        "welcome_title": "🤖 TonFonBot Онлайн",
        "welcome_body": (
            "Добро пожаловать в продвинутый интерфейс <b>TON Sentinel AI</b>.\n"
            "Я предоставляю рыночные данные в реальном времени, технические визуализации и анализ экосистемы TON на основе ИИ.\n\n"
            "<i>Выберите операцию ниже:</i>"
        ),
        
        # Buttons - Main Menu
        "btn_price": "💎 Проверить цену",
        "btn_chart": "📉 График 24ч",
        "btn_stats": "📊 Статистика",
        "btn_forecast": "🔮 Прогноз ИИ",
        "btn_audit": "🔍 Проверить токен",
        "btn_settings": "⚙️ Настройки",
        "btn_about": "📖 Инструкция",
        "btn_back": "🔙 Главное меню",
        
        # Buttons - Settings
        "btn_lang": "🌐 Сменить язык",
        "btn_contact": "📨 Связаться с админом",
        "btn_back_settings": "🔙 Назад",
        "btn_cancel": "❌ Отмена",
        
        # Buttons - Language Selection
        "btn_lang_en": "🇬🇧 English",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_uz": "🇺🇿 O'zbekcha",
        
        # Messages
        "price_live": "💎 <b>TON/USDT</b> Текущая: <code>${price:.4f}</code>",
        "price_error": "⚠️ Не удалось получить данные о цене.",
        "chart_generating": "📊 Генерация графика...",
        "chart_title": "📉 <b>TON/USDT Анализ за 24ч</b>",
        "chart_error": "⚠️ Не удалось создать график",
        "stats_generating": "📊 Генерация статистики...",
        "stats_title": "📊 <b>Статистика рынка TON</b>",
        "stats_error": "⚠️ Не удалось создать статистику",
        "stats_unavailable": "Сервис статистики недоступен",
        "forecast_loading": "🔮 Консультируюсь с Оракулом...",
        "forecast_title": "🧠 <b>Прогноз рынка от ИИ</b>",
        "forecast_error": "⚠️ Сервис ИИ недоступен.",
        "forecast_unavailable": "Прогноз недоступен.",
        
        # Settings
        "settings_title": "⚙️ <b>Настройки</b>",
        "settings_body": "Настройте свои предпочтения или свяжитесь с поддержкой.",
        "contact_title": "📨 <b>Связаться с админом</b>",
        "contact_body": "Напишите ваше сообщение ниже. Оно будет отправлено администраторам.",
        "contact_sent": "✅ Сообщение отправлено {count} админу(ам).",
        "lang_select_title": "🌐 <b>Выберите язык</b>",
        "lang_select_body": "Выберите предпочитаемый язык:",
        "lang_changed": "✅ Язык изменён на Русский.",
        
        # Instruction
        "instruction_title": "📖 <b>Как пользоваться TonFonBot</b>",
        "instruction_body": (
            "Добро пожаловать! Краткое руководство по моим функциям:\n\n"
            "• <b>💎 Проверка цены</b>: Получайте актуальный курс TON/USDT мгновенно.\n"
            "• <b>📉 График 24ч</b>: Создавайте технические графики движения рынка.\n"
            "• <b>🔮 Прогноз ИИ</b>: Получайте прогнозы рынка на основе нейросетей и данных.\n"
            "• <b>📢 Каналы</b>: Подключите свой канал для автоматического получения цен и новостей.\n"
            "• <b>🌐 Инлайн режим</b>: Введите <code>@tonfonbot</code> в любом чате, чтобы поделиться ценой TON с друзьями."
        ),
        
        # Analyze (command)
        "analyze_usage": "Использование: <code>/analyze текст</code>",
        "analyze_loading": "🕵️ Анализирую...",
        "analyze_result_title": "<b>Результат анализа</b>:",
        "analyze_sentiment": "📊 <b>Настроение:</b> {sentiment}",
        "analyze_entities": "🏷 <b>Сущности:</b> {entities}",
        "analyze_dates": "📅 <b>Даты:</b> {dates}",
        "analyze_stored": "✅ <i>Сохранено в базе знаний</i>",
        
        # Service Errors
        "service_unavailable": "Сервис недоступен",
        "chart_unavailable": "Сервис графиков недоступен",
        
        # Channel Management
        "btn_channels": "📢 Каналы",
        "channels_title": "📢 <b>Мои каналы</b>",
        "channels_empty": "Вы ещё не подключили ни одного канала.",
        "channels_list": "Ваши подключённые каналы:",
        "btn_add_channel": "➕ Добавить канал",
        "add_channel_prompt": "📢 <b>Добавить канал</b>\n\n1. Добавьте этого бота <b>администратором</b> в ваш канал.\n2. Отправьте @username канала ниже.",
        "channel_verifying": "🔍 Проверяю...",
        "channel_added": "✅ Канал <b>{name}</b> успешно добавлен!",
        "channel_not_found": "❌ Канал не найден. Проверьте правильность username.",
        "channel_not_admin": "❌ Вы не являетесь администратором этого канала.",
        "channel_bot_not_admin": "❌ Бот не является администратором этого канала. Сначала добавьте его.",
        "channel_already_added": "⚠️ Этот канал уже подключён.",
        "channel_manage_title": "📢 <b>{name}</b>",
        "btn_toggle_price": "💰 Обновления цены: {status}",
        "btn_toggle_news": "📰 Новости: {status}",
        "btn_price_interval": "⏱ Интервал: {interval} мин",
        "btn_news_lang": "🌐 Язык новостей: {language}",
        "btn_delete_channel": "🗑 Удалить канал",
        "status_on": "ВКЛ ✅",
        "status_off": "ВЫКЛ ❌",
        "price_interval_title": "⏱ <b>Выберите интервал</b>",
        "price_interval_body": "Как часто отправлять обновления цены?",
        "btn_interval_1": "1 минута",
        "btn_interval_5": "5 минут",
        "btn_interval_10": "10 минут",
        "interval_set": "✅ Интервал установлен: {interval} минут(ы).",
        "news_lang_title": "🌐 <b>Язык новостей</b>",
        "news_lang_body": "Выберите язык для новостей в этом канале:",
        "news_lang_set": "✅ Язык новостей: {language}.",
        "channel_deleted": "✅ Канал удалён.",
        
        # Token Audit
        "audit_scanning": "🔍 Сканирование блокчейна...",
        "audit_not_found": "❌ Токен не найден в блокчейне.",
        "audit_error": "⚠️ Не удалось проанализировать токен.",
        "audit_unavailable": "⚠️ Сканер токенов недоступен.",
        "audit_prompt": "🔍 <b>Проверка токена</b>\n\nОтправьте адрес TON Jetton для анализа.\n\n<i>Пример: EQ... или UQ...</i>",
        "audit_invalid": "❌ Неверный формат адреса. Отправьте корректный адрес TON (EQ... или UQ...)",
    },
    
    "uz": {
        # Welcome & Main Menu
        "welcome_title": "🤖 TonFonBot Onlayn",
        "welcome_body": (
            "Ilg'or <b>TON Sentinel AI</b> interfeysiga xush kelibsiz.\n"
            "Men real vaqtda bozor ma'lumotlari, texnik vizualizatsiyalar va sun'iy intellekt asosidagi TON ekotizimi tahlilini taqdim etaman.\n\n"
            "<i>Quyidagi operatsiyani tanlang:</i>"
        ),
        
        # Buttons - Main Menu
        "btn_price": "💎 Narxni tekshirish",
        "btn_chart": "📉 24 soatlik grafik",
        "btn_stats": "📊 Statistika",
        "btn_forecast": "🔮 AI Prognoz",
        "btn_audit": "🔍 Tokenni tekshirish",
        "btn_settings": "⚙️ Sozlamalar",
        "btn_about": "📖 Yo'riqnoma",
        "btn_back": "🔙 Asosiy menyu",
        
        # Buttons - Settings
        "btn_lang": "🌐 Tilni o'zgartirish",
        "btn_contact": "📨 Admin bilan bog'lanish",
        "btn_back_settings": "🔙 Orqaga",
        "btn_cancel": "❌ Bekor qilish",
        
        # Buttons - Language Selection
        "btn_lang_en": "🇬🇧 English",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_uz": "🇺🇿 O'zbekcha",
        
        # Messages
        "price_live": "💎 <b>TON/USDT</b> Joriy: <code>${price:.4f}</code>",
        "price_error": "⚠️ Narx ma'lumotlarini olishda xatolik.",
        "chart_generating": "📊 Grafik yaratilmoqda...",
        "chart_title": "📉 <b>TON/USDT 24 soatlik tahlil</b>",
        "chart_error": "⚠️ Grafikni yaratib bo'lmadi",
        "stats_generating": "📊 Statistika yaratilmoqda...",
        "stats_title": "📊 <b>TON Bozor Statistikasi</b>",
        "stats_error": "⚠️ Statistikani yaratib bo'lmadi",
        "stats_unavailable": "Statistika xizmati mavjud emas",
        "forecast_loading": "🔮 Oracle bilan maslahatlashyapman...",
        "forecast_title": "🧠 <b>AI Bozor Prognozi</b>",
        "forecast_error": "⚠️ AI xizmati mavjud emas.",
        "forecast_unavailable": "Prognoz mavjud emas.",
        
        # Settings
        "settings_title": "⚙️ <b>Sozlamalar</b>",
        "settings_body": "Afzalliklaringizni o'zgartiring yoki qo'llab-quvvatlash bilan bog'laning.",
        "contact_title": "📨 <b>Admin bilan bog'lanish</b>",
        "contact_body": "Xabaringizni quyida yozing. U administratorlarga yuboriladi.",
        "contact_sent": "✅ Xabar {count} ta administratorga yuborildi.",
        "lang_select_title": "🌐 <b>Tilni tanlang</b>",
        "lang_select_body": "O'zingizga qulay tilni tanlang:",
        "lang_changed": "✅ Til O'zbekchaga o'zgartirildi.",
        
        # Instruction
        "instruction_title": "📖 <b>Botdan foydalanish bo'yicha yo'riqnoma</b>",
        "instruction_body": (
            "Xush kelibsiz! Mening funksiyalarimdan foydalanish bo'yicha qisqacha qo'llanma:\n\n"
            "• <b>💎 Narxni tekshirish</b>: TON/USDT joriy kursini bir zumda oling.\n"
            "• <b>📉 24 soatlik grafik</b>: Bozor harakatining texnik grafik tahlilini yarating.\n"
            "• <b>🔮 AI Prognozi</b>: Yangiliklar va ma'lumotlar asosida AI prognozlarini oling.\n"
            "• <b>📢 Kanallar</b>: Narxlarni va yangiliklarni avtomatik olish uchun kanalingizni botga ulang.\n"
            "• <b>🌐 Inlayn rejim</b>: TON narxini do'stlaringiz bilan ulashish uchun istalgan chatda <code>@tonfonbot</code> deb yozing."
        ),
        
        # Analyze (command)
        "analyze_usage": "Foydalanish: <code>/analyze matn</code>",
        "analyze_loading": "🕵️ Tahlil qilmoqda...",
        "analyze_result_title": "<b>Tahlil natijasi</b>:",
        "analyze_sentiment": "📊 <b>Kayfiyat:</b> {sentiment}",
        "analyze_entities": "🏷 <b>Ob'ektlar:</b> {entities}",
        "analyze_dates": "📅 <b>Sanalar:</b> {dates}",
        "analyze_stored": "✅ <i>Bilimlar bazasiga saqlandi</i>",
        
        # Service Errors
        "service_unavailable": "Xizmat mavjud emas",
        "chart_unavailable": "Grafik xizmati mavjud emas",
        
        # Channel Management
        "btn_channels": "📢 Kanallar",
        "channels_title": "📢 <b>Mening kanallarim</b>",
        "channels_empty": "Siz hali hech qanday kanal ulamadingiz.",
        "channels_list": "Ulangan kanallaringiz:",
        "btn_add_channel": "➕ Kanal qo'shish",
        "add_channel_prompt": "📢 <b>Kanal qo'shish</b>\n\n1. Bu botni kanalingizga <b>admin</b> sifatida qo'shing.\n2. Kanalning @username'ini quyida yuboring.",
        "channel_verifying": "🔍 Tekshirilmoqda...",
        "channel_added": "✅ <b>{name}</b> kanali muvaffaqiyatli qo'shildi!",
        "channel_not_found": "❌ Kanal topilmadi. Username to'g'riligini tekshiring.",
        "channel_not_admin": "❌ Siz bu kanalning admini emassiz.",
        "channel_bot_not_admin": "❌ Bot bu kanalning admini emas. Avval uni qo'shing.",
        "channel_already_added": "⚠️ Bu kanal allaqachon ulangan.",
        "channel_manage_title": "📢 <b>{name}</b>",
        "btn_toggle_price": "💰 Narx yangilanishlari: {status}",
        "btn_toggle_news": "📰 Yangiliklar: {status}",
        "btn_price_interval": "⏱ Interval: {interval} daqiqa",
        "btn_news_lang": "🌐 Yangilik tili: {language}",
        "btn_delete_channel": "🗑 Kanalni o'chirish",
        "status_on": "YOQILGAN ✅",
        "status_off": "O'CHIRILGAN ❌",
        "price_interval_title": "⏱ <b>Intervalni tanlang</b>",
        "price_interval_body": "Narx yangilanishlari qanchalik tez-tez yuborilsin?",
        "btn_interval_1": "1 daqiqa",
        "btn_interval_5": "5 daqiqa",
        "btn_interval_10": "10 daqiqa",
        "interval_set": "✅ Interval {interval} daqiqaga sozlandi.",
        "news_lang_title": "🌐 <b>Yangilik tili</b>",
        "news_lang_body": "Bu kanal uchun yangiliklar tilini tanlang:",
        "news_lang_set": "✅ Yangilik tili: {language}.",
        "channel_deleted": "✅ Kanal o'chirildi.",
        
        # Token Audit
        "audit_scanning": "🔍 Blokcheyn skanerlanmoqda...",
        "audit_not_found": "❌ Token blokcheynda topilmadi.",
        "audit_error": "⚠️ Tokenni tahlil qilib bo'lmadi.",
        "audit_unavailable": "⚠️ Token skaneri mavjud emas.",
        "audit_prompt": "🔍 <b>Tokenni tekshirish</b>\n\nTahlil qilish uchun TON Jetton manzilini yuboring.\n\n<i>Misol: EQ... yoki UQ...</i>",
        "audit_invalid": "❌ Noto'g'ri manzil formati. Iltimos, to'g'ri TON manzilini yuboring (EQ... yoki UQ...)",
    }
}

# Helper to get text
def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """
    Retrieve a localized string by key.
    Falls back to English if key or language is missing.
    Supports formatting with kwargs.
    """
    lang_dict = TEXTS.get(lang, TEXTS["en"])
    text = lang_dict.get(key, TEXTS["en"].get(key, key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
