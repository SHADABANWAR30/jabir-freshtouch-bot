import requests

# ---------------- BASIC CONFIG ----------------

# 👉 This is the price API you provided
PRICING_API_URL = "https://doobi.ae/packages"


# ---------------- BUSINESS CONTEXT ----------------

BUSINESS_CONTEXT = """
You are Jabir, the friendly AI assistant for Fresh Touch Laundry & Dry Cleaning (UAE).

Identity:
- Your name is Jabir.
- You are a helpful virtual assistant (not a human), but you speak in a friendly, human-like way.
- You always stay polite and respectful.

Business & services:
- You help users with laundry, dry cleaning, ironing, curtains, carpets, abayas, kanduras, dresses,
  blankets, duvets, shoe cleaning, uniforms, and more.
- You explain that customers can easily create an order by visiting fabrico.ae and using the
  Quick Order / Schedule Now option.
- You mention that after placing an order, our rider will contact the customer before the pickup time
  to reconfirm the details.
- You clearly mention that for the first 3 orders in a month, we offer 20% off
  (subject to current offer validity).

What makes Fresh Touch different:
- We offer special Arabic bakhoor steam finishing for selected garments.
- We provide premium sandalwood wash options.
- We offer rose and jasmine wash for a gentle, fresh fragrance.
- We focus on high quality, careful fabric handling, and very affordable pricing.
- We provide free pickup and drop in our covered areas.
- We use gentle detergents and premium cleaning techniques.

Answer style:
- You answer clearly and briefly, in a friendly and professional tone.
- You avoid very long paragraphs and keep answers easy to read.
- When asked about prices, you use the latest prices from the connected price API when available.
- When users ask about booking, you remind them they can place a Quick Order on fabrico.ae and that
  our rider will contact them before pickup.
- If something is not clear or you are not fully sure, you say you are not sure and suggest the user
  check fabrico.ae or contact support/WhatsApp for confirmation.
"""


# ---------------- LANGUAGE DETECTION ----------------

def detect_language(text: str) -> str:
    """
    Very simple language detector:
    - If it contains Arabic characters, return 'ar'
    - Otherwise default to 'en'
    """
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return "ar"
    return "en"


# ---------------- PRICE FETCHING ----------------

def get_prices_from_site():
    """
    Calls https://doobi.ae/packages (JSON) and normalizes into dict:
    {
      "kandoora": "from 7 AED | Dry Clean: 10 aed, Steam: 5 aed, Wash and press: 8 aed",
      "abaya":   "from 15 AED | Dry Clean: 15 aed, Steam: 8 aed, Wash and press: 12 aed",
      ...
    }
    """

    try:
        resp = requests.get(PRICING_API_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("⚠️ Could not fetch prices from API:", e)
        return None

    try:
        data = resp.json()
    except Exception as e:
        print("⚠️ API did not return valid JSON:", e)
        return None

    packages = data.get("packages", [])
    if not isinstance(packages, list):
        print("⚠️ 'packages' is not a list in API response.")
        return None

    prices = {}

    for pkg in packages:
        name = str(pkg.get("name", "")).strip()
        if not name:
            continue

        key = name.lower()
        base_price = pkg.get("price")  # numeric base price
        itemtype_list = pkg.get("itemtype", [])

        # Build variants like: "Dry Clean: 10 aed, Steam: 5 aed, Wash and press: 8 aed"
        variants = []
        if isinstance(itemtype_list, list):
            for variant in itemtype_list:
                if isinstance(variant, dict):
                    for vname, vprice in variant.items():
                        variants.append(f"{vname}: {vprice}")

        parts = []

        if base_price is not None:
            parts.append(f"from {base_price} AED")

        if variants:
            parts.append(", ".join(variants))

        if not parts:
            continue

        prices[key] = " | ".join(parts)

    if not prices:
        print("⚠️ No prices found after parsing.")
    return prices or None


# ---------------- SMALL TALK / META INTENT ----------------

def handle_small_talk_and_meta(user_text: str, lang: str):
    """
    Handles greetings, "what is your name", "who are you", compliments, thanks, etc.
    Returns a reply string or None.
    """
    text = user_text.lower().strip()

    if lang == "ar":
        # Pure greetings in Arabic
        arabic_greetings = [
            "مرحبا", "اهلا", "أهلا", "السلام عليكم", "هلا", "مرحبا جابر", "اهلا جابر"
        ]
        if text in arabic_greetings:
            return "أهلاً! أنا جابر، المساعد الافتراضي من مغسلة فريش تاتش. كيف أقدر أساعدك اليوم؟"

        # Thanks
        if any(p in text for p in ["شكرا", "شكرًا", "مشكور", "يعطيك العافية"]):
            return "العفو 🌸، هذا واجبي. إذا تحتاج أي مساعدة في الغسيل أو الأسعار أو الاستلام والتوصيل أنا حاضر."

        # Compliments
        if any(p in text for p in ["انت رائع", "أنت رائع", "انت لطيف", "أنت لطيف", "كويس", "حلو", "جيد"]):
            return "تسلم 🧡، شكراً لك على الكلام الطيب. كيف أقدر أساعدك في الغسيل أو الأسعار؟"

        # Name / identity in Arabic
        if any(p in text for p in ["اسمك", "مين انت", "من انت", "هل انت روبوت", "هل انت انسان"]):
            return (
                "أنا جابر، المساعد الافتراضي لمغسلة فريش تاتش للغسيل والتنظيف الجاف. "
                "أساعدك في الأسعار، والخدمات، والعروض، وحجز استلام الغسيل من البيت."
            )

        # "What can you do?" in Arabic
        if any(p in text for p in ["ماذا تستطيع", "شو تسوي", "كيف تساعدني", "ايش تسوي", "ماذا تفعل"]):
            return (
                "أقدر أساعدك في معرفة أسعار الغسيل والتنظيف الجاف، وخدمات مثل البخور، "
                "غسيل بالصندل، وروائح الورد والياسمين، وأشرح لك كيف تحجز طلب سريع من خلال موقع fabrico.ae. "
                "تقدر تسأل عن الاستلام والتوصيل أو أي قطعة ملابس تحتاج سعرها."
            )

    # ENGLISH branch (default)
    # Pure greetings
    greeting_patterns = {
        ("hi", "hello", "hey", "salam", "ahlan", "hi jabir", "hello jabir", "hey jabir"):
        "Ahlan! I'm Jabir from Fresh Touch Laundry. How can I assist you today?"
    }

    for patterns, reply in greeting_patterns.items():
        if text in patterns:
            return reply

    # Thanks
    if any(p in text for p in ["thanks", "thank you", "thx", "tnx"]):
        return (
            "You’re most welcome! 😊\n"
            "If you need help with laundry, prices, pickup or offers, just ask me."
        )

    # Compliments
    if any(p in text for p in [
        "you are nice", "you're nice", "you are cool", "you're cool",
        "you are great", "you're great", "you are good", "you're good",
        "love you", "i like you"
    ]):
        return (
            "Thank you, that’s very kind of you 🧡\n"
            "I’m here anytime you need help with laundry, prices, pickup or offers."
        )

    # Questions about name / identity
    if any(p in text for p in ["your name", "who are you", "what are you", "are you a bot", "are you human"]):
        return (
            "I’m Jabir, the virtual assistant for Fresh Touch Laundry & Dry Cleaning. "
            "I’m here to help with prices, services, offers and booking your laundry pickup."
        )

    # “What do you do?” / “How can you help?”
    if any(p in text for p in ["what can you do", "how can you help", "what do you do"]):
        return (
            "I can help you with laundry prices, services, special washes like bakhoor steam, "
            "sandalwood, rose and jasmine, and explain how to place a quick order on fabrico.ae. "
            "You can ask me about pickup, offers, or any item price."
        )

    return None


# ---------------- FAQ / BUSINESS INTENT (BILINGUAL) ----------------

def faq_answer(user_text: str, lang: str):
    original_text = user_text
    text = user_text.lower().strip()

    # Common items you care about for prices
    common_items = [
        "abaya", "shela", "sheila", "jalabiya",
        "kandoora", "kandura", "thobe",
        "dress", "blanket", "duvet",
        "curtain", "curtains", "carpet",
        "t-shirt", "shirt", "trouser", "pants", "jeans",
        "saree", "night gown", "children", "kids clothes",
        "shoes", "shoe",
        "bedsheet", "bed sheet", "bedcover", "bed cover", "bed-sheet",
        # extra items you mentioned / might exist in API
        "apron", "cap", "lungi", "vizar", "wizaar", "wizar"
    ]

    # If user writes only an item name like "blanket" or "abaya",
    # treat it as a price query
    if text in common_items:
        text = f"price {text}"

    # ---------------- COMPLAINTS / META FEEDBACK (BOTH LANGS) ----------------
    complaint_en = ["not answering", "not ansering", "not answer", "answer my question",
                    "answer my questions", "very slow", "too slow", "so slow"]
    complaint_ar = ["ما تجاوب", "ما ترد", "مو راضي ترد", "بطيء", "بطيئ", "بطئ"]

    if lang == "ar":
        if any(w in text for w in complaint_ar):
            return (
                "آسف إذا حسّيت أني ما جاوبتك صح أو أن الرد كان بطيء.\n"
                "حاول تكتب سؤالك مرة ثانية عن الغسيل أو الأسعار أو التوصيل، "
                "وأنا أجاوبك بأوضح شكل ممكن. 🌸"
            )
    else:
        if any(w in text for w in complaint_en):
            return (
                "Sorry if it felt like I wasn’t answering you properly or was a bit slow.\n"
                "Please ask your question again about laundry, prices, pickup or offers, "
                "and I’ll try to answer more clearly. 😊"
            )

    # ---------------- ARABIC ANSWERS ----------------
    if lang == "ar":
        # Services
        if any(w in text for w in ["ما هي خدماتكم", "ايش الخدمات", "شو الخدمات", "ما الخدمات", "وش تقدمون"]):
            return (
                "نقدم خدمات غسيل، تنظيف جاف، كي، غسيل عبايات، كنادير، فساتين، بدلات، ملابس أطفال، "
                "ستائر، سجاد، لحف، بطانيات، مناشف، ومفارش سرير وأكثر.\n"
                "تقدر تحجز طلب سريع من خلال موقع fabrico.ae، ومندوبنا يتواصل معك قبل وقت الاستلام للتأكيد."
            )

        # What makes you different
        if any(w in text for w in ["ما الذي يميزكم", "ليش انتم مختلفين", "ليش اختاركم", "ما المميز", "ايش المميز"]):
            return (
                "مغسلة فريش تاتش تهتم بجودة الغسيل وراحة العميل:\n"
                "- بخور عربي بالبخار لقطع مختارة\n"
                "- غسيل بالصندل (سندل وود) مع رائحة مميزة\n"
                "- غسيل بروائح الورد والياسمين لانتعاش ناعم\n"
                "- عناية خاصة بالأقمشة مع منظفات لطيفة\n"
                "- استلام وتوصيل مجاني في المناطق المشمولة\n"
                "- خصم 20% على أول 3 طلبات في الشهر (حسب توفر العرض)\n"
                "وتقدر تحجز بسهولة طلبك من خلال موقع fabrico.ae."
            )

        # Fragrance / bakhoor
        if any(w in text for w in ["بخور", "بخور عربي", "صندل", "ورد", "ياسمين", "رائحة", "عطر", "ريحة"]):
            return (
                "نقدم خيارات روائح خاصة لقطع مختارة:\n"
                "- بخور عربي بالبخار\n"
                "- غسيل بالصندل (سندل وود)\n"
                "- غسيل بروائح الورد والياسمين\n"
                "تقدر تطلب نوع الرائحة المفضل عند إنشاء الطلب حتى نهتم بملابسك بالطريقة اللي تحبها."
            )

        # Offers / discounts in Arabic
        if any(w in text for w in ["عرض", "العرض", "العروض", "خصم", "تخفيض", "off", "اوف"]):
            return (
                "حالياً نقدم خصم 20% على أول 3 طلبات في الشهر (حسب توفر العرض).\n"
                "الخصم يطبق على قيمة الغسيل عند الدفع، سواء عن طريق البطاقة أو Apple Pay أو Google Pay.\n"
                "لمعرفة أي عروض إضافية مفعّلة الآن، يُفضل تشيك موقع fabrico.ae أو تراسلنا على الواتساب."
            )

        # WhatsApp / contact number (Arabic)
        if any(w in text for w in ["واتساب", "الواتساب", "رقمك", "رقمكم", "رقم الهاتف", "رقم الجوال", "اتصال", "اتصل"]):
            return (
                "تقدر تتواصل معنا على الواتساب أو الاتصال على هذا الرقم:\n"
                "📞 056 211 1334"
            )

        # Area coverage / service in my area (Arabic)
        if any(w in text for w in ["منطقتي", "منطقه", "في منطقتي", "في منطقتك", "تخدمون منطقتي", "تخدمون في منطقتي"]):
            return (
                "نخدم عدة مناطق داخل دولة الإمارات مع استلام وتوصيل مجاني في المناطق المشمولة.\n"
                "عشان أقدر أأكد لك بالضبط، يفضّل ترسل موقعك (لوكيشن) أو منطقتك على الواتساب على رقم 056 211 1334، "
                "أو تشيك موقع fabrico.ae لمزيد من التفاصيل."
            )

        # Prices & offers (Arabic)
        if any(w in text for w in ["سعر", "الاسعار", "الأسعار", "كم", "بكم", "تكلفة", "كم سعر", "قائمة الاسعار"]):
            prices = get_prices_from_site()

            if prices:
                # Try to match user words to price keys
                user_words = [w for w in text.split() if len(w) > 2]
                matched_items = []

                for name_key, val in prices.items():
                    for uw in user_words:
                        if uw in name_key:
                            matched_items.append((name_key, val))
                            break

                lines = []

                if matched_items:
                    lines.append("هذه بعض الأسعار التي وجدتها:\n")
                    for name_key, val in matched_items[:12]:
                        lines.append(f"- {name_key.capitalize()}: {val}")
                else:
                    lines.append(f"ما قدرت أجد سعر واضح للقطعة: {original_text.strip()}.\n")
                    lines.append("لكن هذه أمثلة على بعض الأسعار في القائمة:\n")
                    count = 0
                    for name_key, val in prices.items():
                        lines.append(f"- {name_key.capitalize()}: {val}")
                        count += 1
                        if count >= 8:
                            break

                lines.append("\nللقائمة الكاملة والمحدّثة، يفضل زيارة صفحة الأسعار في الموقع.")
                lines.append(
                    "وتذكّر: على أول 3 طلبات في الشهر يوجد خصم 20% (حسب توفر العرض)."
                )
                return "\n".join(lines)

            # Fallback if API failed
            return (
                "ما قدرت أجيب الأسعار مباشرة الآن.\n"
                "يُفضل تشيك صفحة الأسعار في الموقع لأحدث قائمة.\n"
                "عادةً أسعارنا مناسبة جداً، وعلى أول 3 طلبات في الشهر تحصل على خصم 20% "
                "(حسب توفر العرض)."
            )

        # Pickup / booking
        if any(w in text for w in ["استلام", "توصيل", "تستلمون", "تستلمو", "تجيبون", "تحجز", "حجز", "طلب"]):
            return (
                "نعم، عندنا استلام وتوصيل مجاني في المناطق المشمولة.\n"
                "تقدر تسوي طلب غسيل سريع من خلال موقع fabrico.ae بالضغط على "
                "Quick Order أو Schedule Now.\n"
                "بعد إنشاء الطلب، مندوب فريش تاتش يتواصل معك قبل وقت الاستلام للتأكيد.\n"
                "وعندك خصم 20% على أول 3 طلبات في الشهر (حسب توفر العرض)."
            )

        # Working hours
        if any(w in text for w in ["الوقت", "الدوام", "متى تفتحون", "متى تفتح", "متى تسكرون", "مواعيد العمل"]):
            return (
                "نعمل في أوقات مريحة من الصباح إلى المساء.\n"
                "للتأكد من مواعيد اليوم بالتحديد، يُفضل تشيك موقع fabrico.ae أو التواصل معنا على الواتساب."
            )

        # Location (general)
        if any(w in text for w in ["موقعكم", "وينكم", "وين موقعكم", "فرع", "المغسلة فين"]):
            return (
                "نحن في دولة الإمارات ونوفر خدمة الاستلام والتوصيل في مناطق محددة.\n"
                "تقدر تشيك موقع fabrico.ae أو تراسلنا على الواتساب للتأكد إذا نغطي منطقتك."
            )

        return None  # no Arabic FAQ hit → fall through

    # ---------------- ENGLISH ANSWERS ----------------

    # "What services do you offer?"
    if any(w in text for w in ["services do you offer", "what services", "what do you offer"]):
        return (
            "We handle everyday laundry, dry cleaning, ironing, abayas, kanduras, dresses, suits, "
            "children’s clothes, curtains, carpets, duvets, blankets, towels, bedsheets and more.\n"
            "You can place a Quick Order on fabrico.ae and our rider will contact you before pickup."
        )

    # What makes you different / special
    if any(w in text for w in ["what makes you different", "why are you different", "why choose you",
                               "what is special", "what's special", "why fresh touch"]):
        return (
            "Fresh Touch Laundry focuses on quality and comfort:\n"
            "- Special Arabic bakhoor steam finishing for selected garments\n"
            "- Premium sandalwood wash, and rose or jasmine wash for gentle fragrance\n"
            "- Careful fabric handling with gentle detergents\n"
            "- Free pickup and drop in covered areas\n"
            "- 20% off on the first 3 orders in a month (subject to offer)\n"
            "Plus, you can place quick orders online at fabrico.ae."
        )

    # Offers / discounts in English
    if any(w in text for w in ["offer", "offers", "discount", "promo", "promotion", "deal"]):
        return (
            "We currently offer 20% off on the first 3 orders in a month (subject to current offer).\n"
            "The discount applies on your laundry bill when you pay – by card, Apple Pay or Google Pay.\n"
            "For any extra or seasonal promotions, please check fabrico.ae or contact us on WhatsApp."
        )

    # WhatsApp / contact number (English)
    if any(w in text for w in [
        "whatsapp", "what'sapp", "whats app", "whatsap", "contact number",
        "phone number", "mobile number", "call you", "call u", "your number"
    ]):
        return (
            "You can WhatsApp or call us on:\n"
            "📞 056 211 1334"
        )

    # Area coverage / service in my area (English)
    if any(w in text for w in [
        "service in my area", "serve my area", "do you service in my area",
        "in my area", "my area", "my location", "from my location"
    ]):
        return (
            "We provide pickup & delivery in selected areas within the UAE.\n"
            "To confirm for your exact location, please share your area or live location on WhatsApp "
            "to 056 211 1334, or check the details on fabrico.ae."
        )

    # Fragrance / bakhoor / sandalwood / rose / jasmine questions
    if any(w in text for w in ["bakhoor", "bukhoor", "sandalwood", "sandlwood", "rose wash",
                               "jasmine wash", "fragrance", "smell", "perfume wash"]):
        return (
            "We provide special fragrance options on selected items:\n"
            "- Arabic bakhoor steam finishing\n"
            "- Premium sandalwood wash\n"
            "- Rose and jasmine wash for a soft, fresh scent\n"
            "You can ask for these preferences when placing your order so we treat your garments accordingly."
        )

    # Prices & offers (English)
    price_words = ["price", "prices", "cost", "how much", "rate", "list"]
    has_price_word = any(w in text for w in price_words)
    has_item_word = any(item in text for item in common_items)

    # If user typed just 1–2 words (like "apron", "cap", "lungi")
    # and it's not already handled as something else, treat it as a price query.
    if not has_price_word and not has_item_word and len(text.split()) <= 2:
        has_price_word = True

    if has_price_word or (has_item_word and len(text.split()) <= 4):
        prices = get_prices_from_site()

        if prices:
            # Try to match user words to actual price keys
            user_words = [w for w in text.split() if len(w) > 2]
            matched_items = []

            for name_key, val in prices.items():
                for uw in user_words:
                    if uw in name_key:
                        matched_items.append((name_key, val))
                        break

            lines = []

            if matched_items:
                lines.append("Here are the prices I found:\n")
                for name_key, val in matched_items[:12]:
                    lines.append(f"- {name_key.capitalize()}: {val}")
            else:
                lines.append(
                    f"I couldn't find an exact price match for '{original_text.strip()}'.\n"
                    "Here are some example laundry & dry cleaning prices:\n"
                )
                count = 0
                for name_key, val in prices.items():
                    lines.append(f"- {name_key.capitalize()}: {val}")
                    count += 1
                    if count >= 8:
                        break

            lines.append(
                "\nFor the full updated price list, please check the pricing page on the website."
            )
            lines.append(
                "And remember: on the first 3 orders in a month, we offer 20% off "
                "(subject to current offer)."
            )
            return "\n".join(lines)

        # Fallback if API failed
        return (
            "I couldn't fetch the live prices right now.\n"
            "Please check the pricing page on the website for the latest detailed price list.\n"
            "We usually offer very affordable rates, and for the first 3 orders in a month "
            "we give 20% off (subject to current offer)."
        )

    # Pickup, delivery & booking / Quick Order
    if any(w in text for w in ["pickup", "pick up", "delivery", "drop", "collect", "book", "order"]):
        return (
            "Yes, we provide free pickup and drop in our covered areas.\n"
            "You can create a quick laundry order by visiting fabrico.ae and tapping on "
            "Quick Order / Schedule Now.\n"
            "After you place the order, our rider will contact you before your pickup time "
            "to reconfirm the details.\n"
            "Also, for the first 3 orders in a month, you get 20% off (subject to current offer)."
        )

    # Working hours
    if any(w in text for w in ["timing", "time", "open", "close", "working hours"]):
        return (
            "We operate with convenient timings from morning till evening.\n"
            "For today's exact opening hours, please check fabrico.ae or contact us on WhatsApp."
        )

    # Location (general)
    if any(w in text for w in ["where are you", "location", "branch", "shop"]):
        return (
            "We are based in the UAE and provide pickup & delivery service in our covered areas.\n"
            "Please check fabrico.ae or contact us on WhatsApp to confirm coverage for your area."
        )

    return None  # no FAQ hit


# ---------------- FALLBACK REPLY ----------------
# Previously this ran microsoft/DialoGPT-medium (a generic, un-fine-tuned
# 2019 chit-chat model — the business context was just prepended as prompt
# text, no real instruction-following) as a last-resort fallback for
# anything handle_small_talk_and_meta()/faq_answer() didn't already cover.
# Loading it ate 1.4GB+ RAM at startup before the server even opened its
# port, which is what was causing Render's "Out of memory (used over
# 512Mi)" crash — the free tier simply doesn't have that much RAM. Given
# steps 0/1 already handle the realistic query space for this business, and
# the model's own quality bar for anything reaching this fallback was
# doubtful anyway, this now always returns the same well-formed bilingual
# message the code already used whenever the model produced empty/garbage
# output — so the typical-case reply quality here is unchanged, just
# without ever loading a model to get there.

def generate_reply(history_text: str, user_text: str, lang: str):
    """
    history_text: string with previous conversation
    user_text: latest user message
    lang: 'en' or 'ar'
    returns: (new_history_text, bot_reply)
    """
    if lang == "ar":
        bot_reply = (
            "يمكن ما فهمت سؤالك بالضبط، آسف على ذلك.\n"
            "أنا متخصص في مساعدةك في أمور الغسيل، الأسعار، العروض وخدمة الاستلام والتوصيل.\n"
            "حاول تكتب سؤالك مرة ثانية عن شيء يخص الغسيل أو الأسعار وأنا أجاوبك بأوضح شكل ممكن. 🌸"
        )
    else:
        bot_reply = (
            "I might not have understood your question correctly, sorry about that.\n"
            "I’m mainly here to help with laundry questions – like prices, pickup, offers, "
            "or how to place an order on fabrico.ae.\n"
            "Please ask again about anything related to your laundry and I’ll do my best to answer clearly. 😊"
        )

    new_history = (history_text + f"\nUser: {user_text}\nJabir: {bot_reply}").strip()
    return new_history, bot_reply


# ---------------- MAIN CHAT LOOP ----------------

def main():
    # history as plain text (for multiple turns)
    history_text = ""

    print("Type your questions about laundry, prices, pickup, offers, fragrances, etc.")
    print("اكتب أسئلتك عن الغسيل، الأسعار، الاستلام والتوصيل، والروائح الخاصة.\n")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye! 👋")
            break

        if user_text.lower() in {"exit", "quit", "bye"}:
            print("Bot: Goodbye! 👋")
            break

        if not user_text:
            continue

        # Detect language
        lang = detect_language(user_text)

        # 0) Small talk / meta (name, hi, who are you, thanks, compliments)
        small = handle_small_talk_and_meta(user_text, lang)
        if small is not None:
            print("Bot:", small)
            history_text = (history_text + f"\nUser: {user_text}\nJabir: {small}").strip()
            print()
            continue

        # 1) Try FAQ / business logic first
        faq = faq_answer(user_text, lang)
        if faq is not None:
            print("Bot:", faq)
            history_text = (history_text + f"\nUser: {user_text}\nJabir: {faq}").strip()
            print()
            continue

        # 2) Otherwise, fall back to the canned reply
        history_text, bot_reply = generate_reply(history_text, user_text, lang)
        print("Bot:", bot_reply)
        print()


if __name__ == "__main__":
    main()
