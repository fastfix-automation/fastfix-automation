# FastFix Automation — מדריך מהיר (עברית)

## איפה כל דבר נמצא
- **GitHub** (fastfix-automation/fastfix-automation): הקוד, התורים והאוטומציות. שם הכול רץ, גם כשהמחשב סגור.
- **המחשב (התיקייה הזאת)**: עותק מקומי בלבד. אפשר לעדכן אותו עם `git pull`.
- **Secrets (GitHub → Settings → Secrets → Actions)**: GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN, GBP_ACCOUNT_ID, GBP_LOCATION_ID, וגם שלושת ה-Meta.

## מה התקנו במחשב
- התיקייה הזאת (הפרויקט).
- בתוכה `.venv/`: סביבת Python עם google-auth-oauthlib ו-requests. הייתה נחוצה רק להרצת `scripts/gbp_auth_setup.py` פעם אחת. אפשר למחוק את `.venv`.
- שום דבר אחר לא הותקן במחשב.

## לעדכן את התיקייה
```
cd ~/Desktop/Automation-FastFix/fastfix-automation
git pull
```

## תיקיות חשובות
- `queue/` פוסטים שמחכים לפייסבוק/אינסטגרם | `published/` שפורסמו | `failed/` שנכשלו
- `gbp_queue/` פוסטים שמחכים ל-Google | `gbp_published/` | `gbp_failed/` | `gbp_paused/` מושהים
- `reviews/pending/` ביקורות בלי תשובה | `reviews/replied/` ביקורות שנענו
- `assets/brand/photos/` תמונות עבודה אמיתיות

## תוכנית פוסטים ל-Google (GBP)
1. **מה ידוע:** פוסט טקסט בלבד עבר (Published). פוסטים עם גרפיקה דרך ה-API נדחו.
2. **עד שיש תשובה:** לא מעלים גרפיקות מעוצבות ל-GBP. משתמשים בתמונות עבודה אמיתיות (בלי כיתוב על התמונה).
3. **קצב:** 2 בשבוע (שני וחמישי, 9:00), בדיוק כמו FB/IG.
4. **מבנה פוסט:** משפט פתיחה + שירות + פרבר מרשימת 20 הפרברים + כפתור Call. בלי טלפון בטקסט ובלי הבטחות/מחירים.
5. **פוסטי הפרברים המושהים (`gbp_paused/`):** מומרים לגרסת תמונת-עבודה ומוחזרים לתור אחרי שמאשרים שפוסט עם תמונה אמיתית עובר.
6. **הצעה (15% סופ"ש):** אפשר להעלות כפוסט מסוג Offer, עם קוד WEEKEND15 ותוקף עד 31 בדצמבר.
