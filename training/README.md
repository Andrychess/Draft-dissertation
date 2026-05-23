# Обучение адаптеров AutoAssess

## Быстрый запуск (CPU)

```powershell
.\training\run_training.ps1
```

Шаги:

1. `prepare_datasets.py` — объединение файлов из `dataset/` в JSONL.
2. `train_normativity.py` — Parallel-голова (sklearn).
3. `train_logic.py` — Houlsby-голова (sklearn).

## Релевантность (per template)

При загрузке лекции в UI/backend:

- `backend/app/services/lecture_topics.py` → `ai-service/models/adapters/relevance/template_{id}.json`

Скрипт для ручного теста: `train_relevance_template.py`.

## Результаты последнего обучения

| Адаптер | Accuracy | F1 | Файл модели |
|---------|----------|-----|-------------|
| Нормативность | 0,802 | 0,822 | `ai-service/models/adapters/normativity.joblib` |
| Логика | 0,542 | 0,608 | `ai-service/models/adapters/logic.joblib` |

## Полноценное LoRA (опционально, GPU)

Для весов Pfeiffer/Houlsby/Parallel внутри Mistral 7B нужны PyTorch + PEFT + GPU 16+ ГБ. Текущая реализация использует обученные головы на sklearn для работы без GPU.

См. главу: `docs/chapter_technical_design.md`.
