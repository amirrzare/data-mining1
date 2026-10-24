# Project 1 — ویژوالایز داده‌های آگهی خودرو (باما)

تمرین داده‌کاوی: ویژوالایز آگهی‌های خودرو سایت باما (bama.ir) با Box Plot، هیستوگرام و نمودار پراکندگی، همراه با تحلیل هر نمودار و تعداد نمونه‌ها.

## ساختار

| فایل | توضیح |
|---|---|
| `cars_visualization.py` | پاک‌سازی داده و رسم نمودارها |
| `data/cars_test.csv` | داده‌ی آگهی‌ها (۴۴ ردیف) |
| `output/` | نمودارها |
| `ANALYSIS.md` | تحلیل فارسی هر نمودار |
| `requirements.txt` | کتابخانه‌های لازم |

## اجرا

```bash
cd Project1
pip install -r requirements.txt
python cars_visualization.py
```

داده‌ی خام در `data/cars_test.csv` است و اسکریپت از همان‌جا می‌خواند. خروجی در پوشه‌ی `output/` ساخته می‌شود.

تحلیل کامل: [ANALYSIS.md](ANALYSIS.md)
