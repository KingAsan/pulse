# HDRezka VPN Setup - Работа для всех приложений

## Проблема
VPN работает только для браузера, но не для Python/приложений.

## Решение: Настроить VPN для всех приложений

### Windows 10/11:

#### Способ 1: Встроенный VPN клиент Windows
1. **Settings** → **Network & Internet** → **VPN**
2. **Add a VPN connection**
3. Заполните:
   - VPN provider: **Windows (built-in)**
   - Connection name: **HDRezka VPN**
   - Server name: *(адрес VPN сервера)*
   - VPN type: **Automatic**
   - Type of sign-in info: **User name and password**
4. Подключитесь

#### Способ 2: VPN приложение с System-wide режимом
Если используете расширение браузера VPN:
1. Откройте приложение VPN (не браузер)
2. Найдите настройку **Split Tunneling** или **Mode**
3. Переключите на:
   - **All traffic** / **System-wide** / **Global mode**
   - НЕ **Browser only** или **Proxy mode**

**Популярные VPN с system-wide поддержкой:**
- ✅ **ProtonVPN** (бесплатно) - имеет Windows приложение
- ✅ **Windscribe** (бесплатно 10GB/мес) - Windows приложение  
- ✅ **TunnelBear** (бесплатно 500MB/мес)
- ❌ Браузерные расширения VPN - только для браузера

#### Способ 3: Проверить работает ли VPN для Python
После настройки VPN:

```cmd
# Проверить IP
curl https://api.ipify.org
```

Если IP изменился - VPN работает для всех приложений!

## После настройки VPN

Запустите тест:
```bash
cd backend
python simple_test.py
```

Ожидаемый результат:
```
[1] Direct HDRezka.ag...
    Status: 200 (X.Xs)
    ✅ HDRezka accessible!

[3] Search...
    Status: 200
    ✅ Results: X
    1. Матрица (movie)
    ...
```

## Альтернатива: Деплой на VPS

Если не получается настроить VPN локально:

1. **Railway.app** (бесплатно $5/мес)
   - Деплоите backend туда
   - HDRezka доступен напрямую из США/Европы

2. **Heroku** (бесплатно с ограничениями)
   
3. **DigitalOcean** ($5/мес VPS в Амстердаме)

## Текущий статус интеграции

✅ HdRezkaApi v11.2.3 установлен и настроен
✅ Сервис `hdrezka_api_service.py` готов
✅ Frontend обновлён (выбор качества, переводчиков, сезонов)
✅ Тесты написаны
⏳ Ожидает доступ к HDRezka.ag (через VPN или VPS)

## Как только VPN заработает

1. Убедитесь что VPN работает:
   ```bash
   curl https://api.ipify.org
   # Должен показать IP не из Казахстана
   ```

2. Запустите сервер:
   ```bash
   cd backend
   python app.py
   ```

3. Протестируйте:
   ```bash
   python simple_test.py
   ```

4. Откройте приложение и зайдите в Cinema раздел
