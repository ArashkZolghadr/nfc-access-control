# NFC Access Control System

A production-oriented, simulation-first NFC access control system built with Python.  
The system validates access using configurable policies, logs all access attempts for auditing, and exposes a REST API for management and integration.

Designed to run **without NFC hardware** using mock providers, while supporting real NFC readers via `nfcpy` when deployed in real environments.

---

## Key Features

- NFC UID reading (mocked or real)
- Policy-based access control (whitelist / blacklist)
- Full audit logging with timestamps
- RESTful API for access management
- Exportable logs (JSON / CSV)
- SQLite database (pluggable)
- Clean, testable, and extensible architecture
- Ready for containerized deployment

---

## Architecture Overview

The system is built around a provider-based design:

- **NFC Provider Layer**
  - Mock provider (no hardware required)
  - Real NFC provider using `nfcpy`

- **Access Control Core**
  - UID validation
  - Access decision engine
  - Policy enforcement

- **API Layer**
  - Access management endpoints
  - Log retrieval and export
  - Designed for integration with external systems

---

## Technology Stack

- Python 3.9+
- FastAPI (or Flask)
- SQLite
- nfcpy (optional)
- Uvicorn

---

## How It Works

1. An NFC UID is received (from mock or real reader)
2. The UID is evaluated against access policies
3. Access is granted or denied
4. The decision is logged with a timestamp
5. Data is accessible through the REST API or export files

---

## Running Without NFC Hardware

By default, the system uses a mock NFC provider.  
This allows full functionality, testing, and deployment without any NFC reader or card.

Real NFC support can be enabled by switching the provider implementation.

---

## Use Cases

- Office or lab access control
- Entry logging and auditing
- Attendance systems
- NFC-based automation backends
- Portfolio and real-world demo projects

---

## Project Goals

- Be **usable**, not just demonstrative
- Support real deployment scenarios
- Stay simple, secure, and extensible
- Provide a solid foundation for advanced access control systems

---

## Disclaimer

This project is intended for educational and controlled-environment use.  
It is not a replacement for certified physical security systems.

---

# سیستم کنترل دسترسی NFC

یک سیستم کنترل دسترسی مبتنی بر NFC با رویکرد **قابل استفاده در عمل** و پیاده‌سازی‌شده با Python.  
این سیستم با استفاده از سیاست‌های قابل تنظیم، دسترسی را بررسی می‌کند، تمام تلاش‌های ورود را برای اهداف نظارتی ثبت می‌کند و یک **API** برای مدیریت و یکپارچه‌سازی ارائه می‌دهد.

پروژه به‌صورت **simulation-first** طراحی شده است؛ یعنی بدون نیاز به سخت‌افزار NFC نیز قابل اجراست، اما در محیط‌های واقعی از NFC Reader از طریق `nfcpy` پشتیبانی می‌کند.

---

## ویژگی‌های اصلی

- خواندن UID کارت NFC (واقعی یا شبیه‌سازی‌شده)
- کنترل دسترسی مبتنی بر سیاست (لیست سفید / لیست سیاه)
- ثبت کامل لاگ‌های ورود و خروج با زمان
- REST API برای مدیریت دسترسی
- خروجی گرفتن از لاگ‌ها به‌صورت JSON و CSV
- پایگاه داده SQLite (قابل تعویض)
- معماری تمیز، قابل تست و قابل توسعه
- آماده برای اجرا به‌صورت کانتینری (Docker)

---

## نمای کلی معماری

سیستم بر اساس معماری provider-based طراحی شده است:

- **لایه NFC Provider**
  - Provider شبیه‌سازی‌شده (بدون نیاز به سخت‌افزار)
  - Provider واقعی مبتنی بر `nfcpy`

- **هسته کنترل دسترسی**
  - اعتبارسنجی UID
  - موتور تصمیم‌گیری دسترسی
  - اعمال سیاست‌های امنیتی

- **لایه API**
  - endpointهای مدیریت دسترسی
  - دریافت و خروجی لاگ‌ها
  - مناسب برای اتصال به سیستم‌های دیگر

---

## تکنولوژی‌های استفاده‌شده

- Python 3.9+
- FastAPI یا Flask
- SQLite
- nfcpy (اختیاری)
- Uvicorn

---

## نحوه عملکرد

1. UID کارت NFC (واقعی یا شبیه‌سازی‌شده) دریافت می‌شود
2. UID بر اساس سیاست‌های دسترسی بررسی می‌گردد
3. دسترسی مجاز یا رد می‌شود
4. نتیجه همراه با زمان ثبت می‌شود
5. اطلاعات از طریق API یا فایل‌های خروجی قابل دریافت است

---

## اجرا بدون سخت‌افزار NFC

به‌صورت پیش‌فرض، سیستم از NFC Provider شبیه‌سازی‌شده استفاده می‌کند.  
این موضوع امکان توسعه، تست و حتی استقرار سیستم را بدون NFC Reader فراهم می‌سازد.

در صورت نیاز، می‌توان Provider واقعی NFC را فعال کرد.

---

## موارد استفاده

- کنترل ورود و خروج در محیط‌های اداری یا آزمایشگاهی
- ثبت و نظارت بر تردد افراد
- سیستم‌های حضور و غیاب
- بک‌اند اتوماسیون مبتنی بر NFC
- پروژه حرفه‌ای برای رزومه و گیت‌هاب

---

## اهداف پروژه

- **قابل استفاده واقعی**، نه صرفاً نمایشی
- پشتیبانی از سناریوهای استقرار عملی
- سادگی در کنار امنیت و توسعه‌پذیری
- پایه‌ای مناسب برای سیستم‌های پیشرفته کنترل دسترسی

---

## توجه

این پروژه برای اهداف آموزشی و استفاده در محیط‌های کنترل‌شده طراحی شده است  
و جایگزین سیستم‌های امنیت فیزیکی دارای گواهی رسمی نمی‌باشد.
