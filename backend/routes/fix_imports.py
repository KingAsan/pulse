with open('hdrezka.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace import
content = content.replace('from services.hdrezka_service import hdrezka_service', 
                         'from services.hdrezka_api_service import hdrezka_api_service')

# Replace all usages
content = content.replace('hdrezka_service.', 'hdrezka_api_service.')

with open('hdrezka.py', 'w', encoding='utf-8') as f:
    f.write(content)

count = content.count('hdrezka_api_service')
print(f'Successfully replaced! Found {count} occurrences of hdrezka_api_service')
