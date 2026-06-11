from crawlers.wiki_crawler import WikiVietnamCrawler
from crawlers.tourism_crawler import VietnamTourismCrawler
from utils.parser import DataParser, FALLBACK_EVENTS


def display_menu():
    print("\n" + "=" * 55)
    print("    🌏 베트남 도시별 연례행사 안내 시스템")
    print("=" * 55)


def select_city():
    cities = {
        "1": "하노이",
        "2": "호찌민",
        "3": "다낭",
        "4": "호이안",
        "5": "후에",
        "6": "전체"
    }
    print("\n📌 도시를 선택하세요:")
    for k, v in cities.items():
        print(f"  {k}. {v}")
    choice = input("\n선택: ").strip()
    return cities.get(choice)


def select_month():
    months = {str(i): f"{i}월" for i in range(1, 13)}
    months["13"] = "전체"

    print("\n📌 월을 선택하세요:")
    for k, v in months.items():
        if k != "13":
            print(f"  {k:>2}. {v}", end="\t")
            if int(k) % 4 == 0:
                print()
    print(f"\n  13. 전체\n")

    choice = input("선택: ").strip()
    return months.get(choice)


def display_results(events, city, month):
    print(f"\n{'=' * 55}")
    print(f"  📅 {city} - {month} 연례행사")
    print(f"{'=' * 55}")

    if not events:
        print("  ❌ 해당 조건의 행사가 없습니다.")
        return

    for i, event in enumerate(events, 1):
        print(f"\n  [{i}] 🎉 {event.get('name', '')}")
        print(f"      📍 도시  : {event.get('city', city)}")
        print(f"      📆 월    : {event.get('month', month)}")
        print(f"      📝 설명  : {event.get('description', '')[:100]}...")
        print(f"      🔗 출처  : {event.get('source', '')}")

    print(f"\n  총 {len(events)}개 행사 검색됨")


def main():
    display_menu()

    city = select_city()
    if not city:
        print("❌ 잘못된 선택")
        return

    month = select_month()
    if not month:
        print("❌ 잘못된 선택")
        return

    print(f"\n⏳ {city} - {month} 행사 데이터 수집 중...")
    print("  (크롤링에 약 10~30초 소요될 수 있습니다)")

    # 크롤링 실행
    wiki_crawler = WikiVietnamCrawler()
    tourism_crawler = VietnamTourismCrawler()
    parser = DataParser()

    wiki_data = wiki_crawler.crawl_all()
    tourism_data = tourism_crawler.crawl_all()

    # 데이터 통합
    events = parser.parse_and_merge(wiki_data, tourism_data, city, month)

    # 결과 출력
    display_results(events, city, month)


if __name__ == "__main__":
    main()