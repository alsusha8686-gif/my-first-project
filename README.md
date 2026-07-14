# Telegram-бот: уведомления об отзывах/вопросах WB + AI-черновики ответов

Бот раз в 5 минут проверяет ваш магазин на Wildberries, и если появился новый
отзыв или вопрос — присылает его вам в Telegram с кнопкой
**«🤖 Сгенерировать ответ»**. По нажатию нейросеть (YandexGPT) пишет черновик
ответа, который вы копируете в личный кабинет WB вручную. Ничего не
публикуется автоматически — вы полностью контролируете, что уходит
покупателю.

Инструкция ниже рассчитана на то, чтобы повторить весь путь с нуля.
Ничего не нужно уметь заранее, кроме базового Python и умения работать
с терминалом.

## Что понадобится

- Аккаунт продавца на WB с доступом к Seller API
- Telegram-аккаунт
- Аккаунт в Yandex Cloud (для генерации текста через YandexGPT)
- Python 3.10+ и терминал

## Как это устроено

```
main.py                 — точка входа: поднимает бота и фоновую задачу опроса WB
bot/config.py           — чтение настроек из .env
bot/wb_client.py        — обёртка над Seller API WB (отзывы/вопросы)
bot/yandex_gpt.py       — обёртка над YandexGPT (генерация черновика ответа)
bot/storage.py          — SQLite-таблица с ID уже показанных отзывов/вопросов
bot/notifier.py         — фоновый цикл: раз в N секунд ищет новые отзывы/вопросы
bot/handlers.py         — обработчик нажатия кнопки «Сгенерировать ответ»
bot/keyboards.py        — inline-кнопки
```

Логика работы:

1. Каждые `POLL_INTERVAL_SECONDS` секунд (по умолчанию 300 = 5 минут) бот
   запрашивает у WB неотвеченные отзывы и вопросы.
2. Новые (ещё не показанные) элементы отправляются вам в Telegram с кнопкой
   «🤖 Сгенерировать ответ». ID уже показанных элементов сохраняются в
   локальной базе `wb_bot.db`, чтобы не слать повторно.
3. При нажатии кнопки бот дозапрашивает актуальный текст обращения у WB,
   отправляет его в YandexGPT и присылает черновик ответа отдельным
   сообщением — его остаётся скопировать в личный кабинет WB.

## Шаг 1. Создать Telegram-бота

1. Откройте в Telegram [@BotFather](https://t.me/BotFather) и отправьте `/newbot`.
2. Задайте имя и username бота. BotFather выдаст токен вида
   `123456789:AA...` — это `TELEGRAM_BOT_TOKEN`.
3. Напишите своему новому боту любое сообщение (`/start`), иначе он не
   сможет писать вам первым.
4. Узнайте свой `chat_id`: напишите [@userinfobot](https://t.me/userinfobot) —
   он пришлёт ваш числовой ID. Это `TELEGRAM_CHAT_ID`.

## Шаг 2. Получить токен Seller API Wildberries

1. Зайдите в личный кабинет продавца WB → **Настройки → Доступ к API**.
2. Создайте новый токен и включите для него скоуп **«Вопросы и отзывы»**
   (Feedbacks/Questions).
3. Скопируйте токен — это `WB_API_TOKEN`.

## Шаг 3. Настроить YandexGPT в Yandex Cloud

1. Зарегистрируйтесь на [console.cloud.yandex.ru](https://console.cloud.yandex.ru),
   создайте облако и каталог (folder) — понадобится его ID (`YANDEX_FOLDER_ID`,
   виден в адресной строке или в настройках каталога).
2. В каталоге создайте сервисный аккаунт и назначьте ему роль
   `ai.languageModels.user`.
3. Для этого сервисного аккаунта создайте API-ключ (Service Accounts →
   ваш аккаунт → «Создать новый ключ» → API-ключ) — это `YANDEX_API_KEY`.
4. Модель по умолчанию — `yandexgpt-lite/latest` (дешевле). Если нужно
   качество получше — используйте `yandexgpt/latest`.

## Шаг 4. Установить и запустить проект

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# откройте .env и заполните все переменные из шагов 1–3

python main.py
```

Если всё настроено верно, в логе появится сообщение о старте polling, а бот
начнёт проверять WB каждые 5 минут. Чтобы убедиться, что всё работает,
можно временно поставить `POLL_INTERVAL_SECONDS=30` в `.env`.

## Запуск в фоне (на сервере)

Проще всего — через `systemd`. Создайте файл
`/etc/systemd/system/wb-bot.service`:

```ini
[Unit]
Description=WB reviews Telegram bot
After=network.target

[Service]
WorkingDirectory=/path/to/my-first-project
ExecStart=/path/to/my-first-project/.venv/bin/python main.py
Restart=always
EnvironmentFile=/path/to/my-first-project/.env

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wb-bot
sudo journalctl -u wb-bot -f   # посмотреть логи
```

## Важные ограничения

- Бот **никогда** не публикует ответы на WB автоматически — только
  показывает черновик в Telegram, публикация вручную.
- WB Seller API имеет лимиты на частоту запросов — не ставьте
  `POLL_INTERVAL_SECONDS` меньше ~60 секунд без необходимости.
- Каждый вызов YandexGPT — платный (тарификация Yandex Cloud), генерация
  происходит только по вашему нажатию кнопки, а не автоматически для
  каждого отзыва.
- `wb_bot.db` (SQLite) и `.env` не должны попадать в git — они уже в
  `.gitignore`.
