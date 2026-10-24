# Project 2 — تخمین قیمت فروش و اجاره‌ی ملک (شیپور)

تمرین داده‌کاوی: جمع‌آوری آگهی‌های ملک از شیپور، ویژوالایز، کشف آگهی‌های غیرعادی و تحلیل محله‌ها.

## ساختار

| فایل | توضیح |
|---|---|
| `sheypoor_scraper.py` | اسکرپر کارت‌های عمومی آگهی (رعایت robots.txt، مکث بین درخواست‌ها) |
| `realestate_visualization.py` | پاک‌سازی، نمودارها، آگهی‌های غیرعادی، `summary.txt` |
| `data/sheypoor_all.csv` | داده‌ی استخراج‌شده |
| `output/` | نمودارها و خروجی‌های جدولی |
| `ANALYSIS.md` | تحلیل فارسی هر نمودار |

## اجرا

```bash
cd Project2
pip install -r requirements.txt
python sheypoor_scraper.py --pages 20 --output data/sheypoor_all.csv
python realestate_visualization.py
```

برای فروش و اجاره‌ی جدا: `--csv data/sale.csv --csv data/rent.csv`

تحلیل کامل: [ANALYSIS.md](ANALYSIS.md)
