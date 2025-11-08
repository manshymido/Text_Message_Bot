# دليل اختبار البوت

## خطوات الاختبار

### 1. تشغيل البوت
```bash
python main.py
```

يجب أن ترى:
```
Bot is running. Press Ctrl+C to stop.
```

### 2. اختبار في محادثة خاصة (أسهل للاختبار)

1. افتح Telegram
2. ابحث عن البوت (اسم المستخدم الذي أنشأته)
3. ابدأ محادثة معه
4. أرسل `/start` - يجب أن يرد البوت
5. أرسل رسالة تجريبية:
   ```
   Math assignment due next Monday at 11:59 PM
   ```

**ما يجب أن يحدث:**
- ✅ البوت يرد برسالة تأكيد
- ✅ يتم إنشاء حدث في Google Calendar
- ✅ يتم إنشاء مهمة في Google Tasks (للـ assignments)

### 3. اختبار في مجموعة

1. أنشئ مجموعة أو افتح مجموعة موجودة
2. أضف البوت إلى المجموعة
3. **مهم جداً:** تأكد من أن البوت لديه صلاحية قراءة الرسائل
   - قد تحتاج إلى جعله مشرف (Admin)
   - أو على الأقل تأكد من أنه يمكنه قراءة الرسائل
4. أرسل رسالة في المجموعة:
   ```
   History exam on Friday at 2pm
   ```

### 4. مراقبة السجلات

راقب نافذة PowerShell أو ملف `logs/bot.log` لرؤية:
- الرسائل المستلمة
- ما إذا كانت الرسالة مرت عبر الفلتر
- المعلومات المستخرجة
- الأحداث والمهام المنشأة

### 5. التحقق من النتائج

**في Google Calendar:**
- افتح [Google Calendar](https://calendar.google.com)
- تحقق من وجود أحداث جديدة

**في Google Tasks:**
- افتح [Google Tasks](https://tasks.google.com)
- تحقق من وجود مهام جديدة (للـ assignments فقط)

## أمثلة رسائل للاختبار

### Assignments (ينشئ حدث + مهمة):
```
Math assignment due next Monday at 11:59 PM
Homework due Friday
Project submission deadline: December 20th
```

### Exams (ينشئ حدث فقط):
```
History exam on Friday at 2pm
Math test next Monday
Final exam on December 15th at 10am
```

### Classes (ينشئ حدث فقط):
```
CS101 lecture tomorrow at 10am in room 205
Class on Tuesday at 2pm
Tutorial session next Wednesday
```

## استكشاف الأخطاء

### البوت لا يرد:
1. تأكد من أن البوت يعمل (شاهد نافذة PowerShell)
2. تحقق من السجلات في `logs/bot.log`
3. تأكد من أن البوت في المجموعة وله صلاحيات القراءة

### لا يتم إنشاء أحداث:
1. تحقق من السجلات للأخطاء
2. تأكد من أن Google OAuth تم بنجاح
3. تحقق من أن `credentials/token.json` موجود

### الرسالة لا تمر عبر الفلتر:
- تأكد من أن الرسالة تحتوي على كلمات مفتاحية مثل:
  - assignment, homework, exam, test, class, lecture, due, deadline

## ملاحظات

- البوت يعمل فقط مع الرسائل النصية (لا يعمل مع الصور/الملفات)
- يجب أن تحتوي الرسالة على معلومات تاريخ/وقت واضحة
- البوت يتجاهل الرسائل العادية التي لا تحتوي على معلومات مدرسية

