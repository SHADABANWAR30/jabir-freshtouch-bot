import requests

PRICING_API_URL = "https://doobi.ae/packages"


def detect_language(text: str) -> str:
    """Very simple language detector: Arabic if contains Arabic chars, else English."""
    if any("\u0600" <= ch <= "\u06FF" for ch in text):
        return "ar"
    return "en"


def get_prices_from_site():
    """Fetch and normalize prices from API. Returns dict: name_lower -> description string."""
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

        variants = []
        if isinstance(itemtype_list, list):
            for v in itemtype_list:
                if isinstance(v, dict):
                    for vname, vprice in v.items():
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
        print("⚠️ No prices parsed from API.")
        return None

    return prices


def handle_small_talk_and_meta(text: str, lang: str):
    """Greetings, thanks, compliments, identity questions."""
    t = text.strip().lower()

    if lang == "ar":
        arabic_greetings = [
            "مرحبا",
            "أهلا",
            "اهلا",
            "السلام عليكم",
            "هلا",
            "مرحبا جابر",
            "اهلا جابر",
        ]
        if t in arabic_greetings:
            return "أهلاً! أنا جابر من مغسلة فريش تاتش. كيف أقدر أساعدك اليوم؟"

        if any(p in t for p in ["شكرا", "شكرًا", "مشكور", "يعطيك العافية"]):
            return "العفو 🌸، إذا تحتاج أي مساعدة في الغسيل أو الأسعار أو الاستلام والتوصيل أنا حاضر."

        if any(p in t for p in ["انت رائع", "أنت رائع", "انت لطيف", "أنت لطيف", "كويس", "حلو", "جيد"]):
            return "تسلم 🧡، شكراً على الكلام الطيب. كيف أقدر أساعدك في الغسيل أو الأسعار؟"

        if any(p in t for p in ["اسمك", "مين انت", "من انت", "هل انت روبوت", "هل انت انسان"]):
            return (
                "أنا جابر، المساعد الافتراضي لمغسلة فريش تاتش للغسيل والتنظيف الجاف. "
                "أقدر أساعدك في الأسعار، الخدمات، العروض، وحجز استلام الغسيل من البيت."
            )

        if any(p in t for p in ["ماذا تستطيع", "شو تسوي", "كيف تساعدني", "ايش تسوي", "ماذا تفعل"]):
            return (
                "أقدر أساعدك في معرفة أسعار الغسيل والتنظيف الجاف، وخدمات مثل البخور، "
                "غسيل بالصندل وروائح الورد والياسمين، وأشرح لك طريقة حجز طلب سريع من خلال موقع fabrico.ae."
            )

    # English small talk
    greetings = ["hi", "hello", "hey", "salam", "ahlan", "hi jabir", "hello jabir", "hey jabir"]
    if t in greetings:
        return "Ahlan! I'm Jabir from Fresh Touch Laundry. How can I assist you today?"

    if any(p in t for p in ["thanks", "thank you", "thx", "tnx"]):
        return "You’re most welcome! 😊 If you need help with laundry, prices, pickup or offers, just ask me."

    if any(
        p in t
        for p in [
            "you are nice",
            "you're nice",
            "you are cool",
            "you're cool",
            "you are great",
            "you're great",
            "you are good",
            "you're good",
            "love you",
            "i like you",
        ]
    ):
        return "Thank you, that’s very kind of you 🧡 I’m here anytime you need help with laundry, prices, pickup or offers."

    if any(p in t for p in ["your name", "who are you", "what are you", "are you a bot", "are you human"]):
        return (
            "I’m Jabir, the virtual assistant for Fresh Touch Laundry & Dry Cleaning. "
            "I’m here to help with prices, services, offers and booking your laundry pickup."
        )

    if any(p in t for p in ["what can you do", "how can you help", "what do you do"]):
        return (
            "I can help you with laundry prices, services, special washes like bakhoor steam, "
            "sandalwood, rose and jasmine, and explain how to place a quick order on fabrico.ae."
        )

    return None


def faq_answer(text: str, lang: str):
    """Main FAQ / business logic, bilingual."""
    t = text.strip().lower()

    # Complaints: "not answering", "very slow"
    if lang == "ar":
        if any(p in t for p in ["ما تجاوب", "ما ترد", "بطيء", "بطيئ", "بطئ"]):
            return (
                "آسف إذا حسّيت أني ما جاوبتك صح أو أن الرد كان بطيء.\n"
                "حاول تكتب سؤالك مرة ثانية عن الغسيل أو الأسعار أو التوصيل، وأنا أجاوبك بأوضح شكل ممكن. 🌸"
            )
    else:
        if any(p in t for p in ["not answering", "not ansering", "answer my question", "very slow", "too slow"]):
            return (
                "Sorry if it felt like I wasn’t answering you properly or was a bit slow.\n"
                "Please ask again about laundry, prices, pickup or offers and I’ll try to answer more clearly. 😊"
            )

    # Common items for price detection
    common_items = [
        "abaya",
        "shela",
        "sheila",
        "jalabiya",
        "kandoora",
        "kandura",
        "thobe",
        "dress",
        "blanket",
        "duvet",
        "curtain",
        "curtains",
        "carpet",
        "t-shirt",
        "shirt",
        "trouser",
        "pants",
        "jeans",
        "bedsheet",
        "bed sheet",
        "bedcover",
        "bed cover",
        "apron",
        "cap",
        "lungi",
        "wizar",
        "wizaar",
    ]

    # If user wrote just "abaya" → treat as price query
    if t in common_items:
        t = "price " + t

    # ========== Arabic branch ==========
    if lang == "ar":
        # Services
        if any(p in t for p in ["ما هي خدماتكم", "ايش الخدمات", "شو الخدمات", "ما الخدمات", "وش تقدمون"]):
            return (
                "نقدم غسيل، تنظيف جاف، كي، عبايات، كنادير، فساتين، بدلات، ملابس أطفال، "
                "ستائر، سجاد، لحف، بطانيات، مناشف ومفارش سرير وأكثر.\n"
                "تقدر تحجز طلب سريع عن طريق موقع fabrico.ae، ومندوبنا يتواصل معك قبل الاستلام للتأكيد."
            )

        # Offers / discount
        if any(p in t for p in ["عرض", "العرض", "العروض", "خصم", "تخفيض"]):
            return (
                "حالياً نقدم خصم 20% على أول 3 طلبات في الشهر (حسب توفر العرض).\n"
                "الخصم يطبق على قيمة الغسيل عند الدفع، سواء بالبطاقة أو Apple Pay أو Google Pay."
            )

        # WhatsApp / contact
        if any(p in t for p in ["واتساب", "الواتساب", "رقمك", "رقمكم", "رقم الهاتف", "رقم الجوال", "اتصال"]):
            return "تقدر تتواصل معنا على الواتساب أو الاتصال على: 📞 056 211 1334"

        # Area coverage
        if any(p in t for p in ["منطقتي", "في منطقتي", "تخدمون منطقتي", "تخدمون في منطقتي"]):
            return (
                "نخدم عدة مناطق داخل دولة الإمارات مع استلام وتوصيل مجاني في المناطق المشمولة.\n"
                "الأفضل ترسل موقعك أو منطقتك على الواتساب 056 211 1334 عشان نأكد لك الخدمة."
            )

        # Prices
        if any(p in t for p in ["سعر", "الاسعار", "الأسعار", "كم", "بكم", "تكلفة", "قائمة الاسعار"]):
            prices = get_prices_from_site()
            if prices:
                user_words = [w for w in t.split() if len(w) > 2]
                matched = []
                for name_key, val in prices.items():
                    for uw in user_words:
                        if uw in name_key:
                            matched.append((name_key, val))
                            break

                lines = []
                if matched:
                    lines.append("هذه بعض الأسعار التي وجدتها:\n")
                    for name_key, val in matched[:12]:
                        lines.append(f"- {name_key.capitalize()}: {val}")
                else:
                    lines.append("ما قدرت أجد سعر واضح للقطعة المطلوبة.\n")
                    lines.append("لكن هذه أمثلة من قائمة الأسعار:\n")
                    count = 0
                    for name_key, val in prices.items():
                        lines.append(f"- {name_key.capitalize()}: {val}")
                        count += 1
                        if count >= 8:
                            break

                lines.append("\nللقائمة الكاملة والمحدّثة يفضل زيارة صفحة الأسعار في الموقع.")
                lines.append("وتذكّر: على أول 3 طلبات في الشهر يوجد خصم 20% (حسب توفر العرض).")
                return "\n".join(lines)

            return (
                "ما قدرت أجيب الأسعار الآن.\n"
                "يُفضل تشيك صفحة الأسعار في الموقع لأحدث قائمة.\n"
                "غالباً أسعارنا مناسبة ومع خصم 20% لأول 3 طلبات في الشهر (حسب توفر العرض)."
            )

        # Pickup / booking
        if any(p in t for p in ["استلام", "توصيل", "تحجز", "حجز", "طلب", "أطلب", "اطلب"]):
            return (
                "نعم، عندنا استلام وتوصيل مجاني في المناطق المشمولة.\n"
                "تقدر تسوي طلب غسيل سريع عبر موقع fabrico.ae بالضغط على Quick Order أو Schedule Now.\n"
                "بعد إنشاء الطلب مندوب فريش تاتش يتواصل معك قبل وقت الاستلام للتأكيد.\n"
                "وعندك خصم 20% على أول 3 طلبات في الشهر (حسب توفر العرض)."
            )

        # Working hours
        if any(p in t for p in ["الوقت", "الدوام", "متى تفتحون", "متى تسكرون", "مواعيد العمل"]):
            return (
                "نعمل في أوقات مريحة من الصباح إلى المساء.\n"
                "للتأكد من مواعيد اليوم بالضبط، يفضل تشيك موقع fabrico.ae أو التواصل معنا على الواتساب."
            )

        # Location
        if any(p in t for p in ["موقعكم", "وينكم", "وين موقعكم", "فرع", "المغسلة فين"]):
            return (
                "نحن في دولة الإمارات ونقدم خدمة الاستلام والتوصيل في مناطق محددة.\n"
                "تقدر تشيك موقع fabrico.ae أو تراسلنا على الواتساب للتأكد إذا نغطي منطقتك."
            )

        return None

    # ========== English branch ==========

    # Services
    if any(p in t for p in ["services do you offer", "what services", "what do you offer"]):
        return (
            "We handle everyday laundry, dry cleaning, ironing, abayas, kanduras, dresses, suits, "
            "children’s clothes, curtains, carpets, duvets, blankets, towels, bedsheets and more.\n"
            "You can place a Quick Order on fabrico.ae and our rider will contact you before pickup."
        )

    # Offers / discounts
    if any(p in t for p in ["offer", "offers", "discount", "promo", "promotion", "deal"]):
        return (
            "We currently offer 20% off on the first 3 orders in a month (subject to current offer).\n"
            "The discount applies on your laundry bill when you pay – by card, Apple Pay or Google Pay."
        )

    # WhatsApp / contact
    if any(
        p in t
        for p in [
            "whatsapp",
            "whats app",
            "what'sapp",
            "whatsap",
            "contact number",
            "phone number",
            "mobile number",
            "call you",
            "call u",
            "your number",
        ]
    ):
        return "You can WhatsApp or call us on:\n📞 056 211 1334"

    # Area coverage / service in my area
    if any(
        p in t
        for p in [
            "service in my area",
            "serve my area",
            "do you service in my area",
            "in my area",
            "my area",
            "my location",
            "from my location",
        ]
    ):
        return (
            "We provide pickup & delivery in selected areas within the UAE.\n"
            "To confirm for your exact location, please share your area or live location on WhatsApp "
            "to 056 211 1334, or check details on fabrico.ae."
        )

    # Prices
    if any(p in t for p in ["price", "prices", "cost", "how much", "rate", "list"]):
        prices = get_prices_from_site()
        if prices:
            user_words = [w for w in t.split() if len(w) > 2]
            matched = []
            for name_key, val in prices.items():
                for uw in user_words:
                    if uw in name_key:
                        matched.append((name_key, val))
                        break

            lines = []
            if matched:
                lines.append("Here are the prices I found:\n")
                for name_key, val in matched[:12]:
                    lines.append(f"- {name_key.capitalize()}: {val}")
            else:
                lines.append(
                    "I couldn't find an exact price match for that item.\nHere are some example prices:\n"
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
                "And remember: on the first 3 orders in a month, we offer 20% off (subject to current offer)."
            )
            return "\n".join(lines)

        return (
            "I couldn't fetch the live prices right now.\n"
            "Please check the pricing page on the website for the latest detailed price list.\n"
            "We usually offer very affordable rates, and for the first 3 orders in a month "
            "we give 20% off (subject to current offer)."
        )

    # Pickup / booking
    if any(p in t for p in ["pickup", "pick up", "delivery", "drop", "collect", "book", "order"]):
        return (
            "Yes, we provide free pickup and drop in our covered areas.\n"
            "You can create a quick laundry order by visiting fabrico.ae and tapping on "
            "Quick Order / Schedule Now.\n"
            "After you place the order, our rider will contact you before your pickup time "
            "to reconfirm the details.\n"
            "Also, for the first 3 orders in a month, you get 20% off (subject to current offer)."
        )

    # Working hours
    if any(p in t for p in ["timing", "time", "open", "close", "working hours"]):
        return (
            "We operate with convenient timings from morning till evening.\n"
            "For today's exact opening hours, please check fabrico.ae or contact us on WhatsApp."
        )

    # Location
    if any(p in t for p in ["where are you", "location", "branch", "shop"]):
        return (
            "We are based in the UAE and provide pickup & delivery service in our covered areas.\n"
            "Please check fabrico.ae or contact us on WhatsApp to confirm coverage for your area."
        )

    return None


def answer(user_text: str) -> str:
    """Main entrypoint: decide language, small talk, FAQ, or fallback."""
    lang = detect_language(user_text)

    small = handle_small_talk_and_meta(user_text, lang)
    if small:
        return small

    faq = faq_answer(user_text, lang)
    if faq:
        return faq

    # Fallback if nothing matched
    if lang == "ar":
        return (
            "أعتذر، يمكن سؤالك عام شوي أو خارج نطاق المعلومات اللي عندي.\n"
            "أنا مساعد متخصص في الغسيل، الأسعار، العروض وخدمة الاستلام والتوصيل.\n"
            "حاول تسألني عن شيء بخصوص الغسيل أو الأسعار أو الطلبات وسأحاول أساعدك بأفضل شكل. 🌸"
        )
    else:
        return (
            "I’m mainly trained to help with laundry topics – prices, pickup, offers, "
            "and how to place an order on fabrico.ae.\n"
            "Please ask me about your laundry, items, prices or pickup and I’ll do my best to help. 😊"
        )
