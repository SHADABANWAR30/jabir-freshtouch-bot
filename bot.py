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
        # ✅ VIEW ORDER / TRACK ORDER
        if any(
            p in t
            for p in [
                "اشوف طلبي",
                "أشوف طلبي",
                "اشوف الطلب",
                "أشوف الطلب",
                "طلباتي",
                "طلباتى",
                "اتابع طلبي",
                "أتتبع طلبي",
                "تتبع الطلب",
                "حالة الطلب",
            ]
        ):
            return (
                "عشان تشوف طلبك وتتابع حالته:\n\n"
                "1. افتح موقع fabrico.ae\n"
                "2. اضغط على «تسجيل الدخول برمز OTP»\n"
                "3. حط رقم جوالك، وادخل رمز التحقق اللي يوصلك برسالة SMS\n"
                "4. بعد تسجيل الدخول، ادخل على قائمة «طلباتي» My Orders\n"
                "5. اختر الطلب اللي تبيه\n\n"
                "بتشوف هناك:\n"
                "- حالة الطلب خطوة بخطوة\n"
                "- وقت الاستلام والتسليم المتوقع\n"
                "- حالة الدفع (مدفوع / غير مدفوع)\n"
                "- تفاصيل المبلغ والملابس.\n"
            )

        # ✅ PAYMENT / HOW TO PAY
        if any(
            p in t
            for p in [
                "كيف ادفع",
                "كيف أدفع",
                "طريقة الدفع",
                "الدفع",
                "ادفع",
                "أدفع",
                "سداد",
                "فاتورة",
                "الفاتورة",
                "اسدد",
            ]
        ):
            return (
                "عشان تدفع فاتورة الغسيل أونلاين:\n\n"
                "1. افتح موقع fabrico.ae\n"
                "2. سجّل دخول برقم جوالك باستخدام «تسجيل الدخول برمز OTP»\n"
                "3. ادخل على قسم «طلباتي» My Orders\n"
                "4. اختر الطلب اللي عليه مبلغ مستحق\n"
                "5. اضغط زر «الدفع» Pay\n"
                "6. اختر طريقة الدفع المناسبة:\n"
                "   - بطاقة بنكية (Debit / Credit Card)\n"
                "   - Apple Pay\n"
                "   - Google Pay\n"
                "7. بعد الدفع، تقدر تشوف تأكيد الدفع وتحمل الفاتورة.\n\n"
                "لو واجهتك أي مشكلة في الدفع، تقدر تتواصل معنا على الواتساب 056 211 1334. 😊"
            )

        # ✅ OTP LOGIN / ACCOUNT / TRACK (generic)
        if any(
            p in t
            for p in [
                "تسجيل الدخول",
                "تسجيل دخول",
                "كيف ادخل",
                "كيف أسجل",
                "الدخول",
                "otp",
                "رمز",
                "رمز تحقق",
                "رمز التحقق",
                "دخول بالحساب",
                "حسابي",
            ]
        ):
            return (
                "طريقة تسجيل الدخول باستخدام رمز OTP سهلة جداً!\n\n"
                "1. افتح موقع fabrico.ae\n"
                "2. اضغط على خيار «تسجيل الدخول برمز OTP»\n"
                "3. اكتب رقم جوالك\n"
                "4. بيصلك رمز تحقق مكوّن من 6 أرقام في رسالة SMS\n"
                "5. أدخل الرمز وبيتم تسجيل دخولك فوراً\n\n"
                "بعدها تقدر:\n"
                "- تشوف كل طلباتك السابقة والجديدة\n"
                "- تتابع حالة الطلب خطوة بخطوة\n"
                "- تعرف حالة الدفع\n"
                "- تدفع بالبطاقة أو Apple Pay أو Google Pay\n"
                "- تحمّل الفاتورة والإيصال\n\n"
                "ما تحتاج كلمة سر — فقط رمز OTP السريع. 😊"
            )

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

    # ✅ VIEW ORDER / TRACK ORDER
    if any(
        p in t
        for p in [
            "view my order",
            "see my order",
            "view order",
            "see order",
            "my orders",
            "order history",
            "track my order",
            "track order",
            "order status",
        ]
    ):
        return (
            "To view and track your order:\n\n"
            "1. Go to fabrico.ae\n"
            "2. Tap 'Login with OTP'\n"
            "3. Enter your mobile number and the 6-digit OTP you receive by SMS\n"
            "4. Once logged in, open the 'My Orders' section\n"
            "5. Select the order you want to see\n\n"
            "There you can view:\n"
            "- The full status timeline\n"
            "- Pickup and delivery details\n"
            "- Payment status (paid / unpaid)\n"
            "- The bill and garment details.\n"
        )

    # ✅ PAYMENT / HOW TO PAY
    if any(
        p in t
        for p in [
            "how to pay",
            "pay my order",
            "make payment",
            "payment",
            "pay now",
            "pay bill",
            "pay invoice",
            "settle bill",
            "settle my bill",
        ]
    ):
        return (
            "To pay for your laundry order online:\n\n"
            "1. Go to fabrico.ae\n"
            "2. Log in using 'Login with OTP' (mobile number + 6-digit OTP)\n"
            "3. Open the 'My Orders' section\n"
            "4. Select the order that has an outstanding amount\n"
            "5. Tap the 'Pay' button\n"
            "6. Choose your payment method:\n"
            "   - Card (debit / credit)\n"
            "   - Apple Pay\n"
            "   - Google Pay\n"
            "7. After payment, you will see confirmation and can download your receipt.\n\n"
            "If you face any issue with payment, you can also WhatsApp us on 056 211 1334. 😊"
        )

    # ✅ OTP LOGIN / ACCOUNT / TRACK (generic)
    if any(
        p in t
        for p in [
            "login",
            "log in",
            "login with otp",
            "otp login",
            "how to login",
            "how to log in",
            "sign in",
            "sign-in",
            "my account",
            "account",
        ]
    ):
        return (
            "It's very simple to log in using OTP on Fresh Touch Laundry:\n\n"
            "1. Go to fabrico.ae\n"
            "2. Tap 'Login with OTP'\n"
            "3. Enter your mobile number\n"
            "4. You will receive a 6-digit OTP by SMS\n"
            "5. Enter the OTP to log in instantly\n\n"
            "Once logged in, you can:\n"
            "- View all your orders\n"
            "- Track order progress step-by-step\n"
            "- Check payment status\n"
            "- Pay using card, Apple Pay or Google Pay\n"
            "- Download your receipts\n\n"
            "No password is needed — just quick OTP login. 😊"
        )

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
            "and how to place an order or pay for your order on fabrico.ae.\n"
            "Please ask me about your laundry, items, prices, orders or pickup and I’ll do my best to help. 😊"
        )
