# AutoAssess

Интеллектуальная система автоматизированной оценки письменных работ студентов.

## Компоненты

| Сервис | Порт | Описание |
|--------|------|----------|
| `backend` | 8000 | Информационная система (FastAPI + PostgreSQL) |
| `ai-service` | 8001 | Модуль ИИ (Mistral 7B + адаптеры) |
| `frontend` | 3000 | React 18 + TypeScript |
| `postgres` | 5432 | База данных |

## Быстрый старт

### 1. Модель GGUF (для полноценного ИИ)

```bash
mkdir -p models
wget -O models/mistral-7b-instruct-v0.1.Q4_K_S.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_S.gguf
```

Без GGUF-файла `ai-service` работает в эвристическом режиме (оценка по пересечению слов).

> В папке `Mistral 7B/` лежит safetensors-версия — для `llama-cpp-python` нужен именно **GGUF**.

### 2. Docker Compose

```bash
docker-compose up --build
```

### 3. Вход

- URL: http://localhost:3000
- Админ (создаётся при старте): `admin@example.com` / `admin123`
- Студент: http://localhost:3000/join — код сессии с панели преподавателя

## Локальная разработка

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### AI-service

```bash
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

## Структура

```
AutoAssess/
├── backend/          # ИС
├── ai-service/       # Модуль ИИ
├── frontend/         # React UI
├── models/           # GGUF модель (не в git)
├── dataset/          # Обучающие корпуса
├── training/         # Скрипты обучения адаптеров
├── docs/             # Материалы диссертации
└── docker-compose.yml
```
