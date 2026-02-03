import argparse
import json
from link_checker.checker import URLChecker

def main():
    parser = argparse.ArgumentParser(description='Агент проверки ссылок на веб-странице')
    parser.add_argument('url', help='URL страницы для проверки')
    parser.add_argument('--output', '-o', help='Файл для сохранения результатов (JSON)')
    parser.add_argument('--max-links', '-m', type=int, default=1000, 
                       help='Максимальное количество ссылок для проверки')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Подробный вывод')
    
    args = parser.parse_args()
    
    # Создаем и запускаем проверку
    checker = URLChecker()
    results = checker.check(args.url, args.max_links)
    
    # Вывод результатов
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Результаты сохранены в {args.output}")
    
    # Консольный вывод
    print(f"\n{'='*50}")
    print(f"Отчет для: {args.url}")
    print(f"Всего проверено: {len(results)}")
    print(f"Рабочих: {sum(1 for r in results if r['ok'])}")
    print(f"Нерабочих: {sum(1 for r in results if not r['ok'])}")
    
    if args.verbose:
        print("\nДетальные результаты:")
        for result in results:
            status = '✓' if result['ok'] else '✗'
            print(f"{status} {result['url']} [{result['status'] or 'ERROR'}]")

if __name__ == '__main__':
    main()
