# OpenLines Session Collector

A Python script that fetches chat session histories from a Bitrix24 Open Lines API, filters them, and stores structured dialog data in a MySQL database.

## What it does

- Iterates over chat sessions by ID starting from a configured offset
- Parses dialog messages, identifies senders (company-side vs. client-side)
- Filters out sessions with no external participants
- Stores sessions in a MySQL `sessions` table with fields: `session_id`, `client_id`, `client_name`, `source`, `is_finished`, `text`
- On subsequent runs, updates text for sessions that were not yet marked as finished

## Requirements

- Python 3.10+
- MySQL database
- Bitrix24 REST API access (webhook URL)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root (.example.env is already in the repository):

```env
TOKEN_OL=https://your-bitrix24-domain/rest/1/your-webhook-token/
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

## Usage

```bash
python app.py
```

To reset the database (drop all tables):

```bash
python delete_db.py
```

## Notes

- `FIRST_ID` in `app.py` sets the starting session ID for the initial fetch.
- Sessions are fetched with a 0.5-second delay between requests to avoid rate limiting.
- The `source` field is normalized from Bitrix24 connector names to common platform names (whatsapp, telegram, vk, etc.).

---

## OpenLines Session Collector — описание на русском

Python-скрипт для получения истории чат-сессий через Bitrix24 Open Lines API, их фильтрации и сохранения структурированных диалогов в MySQL базу данных.

## Что делает

- Перебирает чат-сессии по ID начиная с заданного смещения
- Парсит сообщения, определяет отправителей (сотрудник компании или клиент)
- Фильтрует сессии без внешних участников
- Сохраняет сессии в таблицу MySQL `sessions` с полями: `session_id`, `client_id`, `client_name`, `source`, `is_finished`, `text`
- При повторном запуске обновляет текст незавершённых сессий

## Требования

- Python 3.10+
- MySQL база данных
- Доступ к Bitrix24 REST API (webhook URL)

Установка зависимостей:

```bash
pip install -r requirements.txt
```

## Настройка

Создайте файл `.env` в корне проекта (.example.env уже в репозитории):

```env
TOKEN_OL=https://your-bitrix24-domain/rest/1/your-webhook-token/
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

## Запуск

```bash
python app.py
```

Сброс базы данных (удаление всех таблиц):

```bash
python delete_db.py
```

## Примечания

- `FIRST_ID` в `app.py` задаёт стартовый ID сессии при первом запуске.
- Между запросами выдерживается пауза 0.5 секунды во избежание rate limiting.
- Поле `source` нормализуется из внутренних названий коннекторов Bitrix24 в общепринятые платформы (whatsapp, telegram, vk и др.).
