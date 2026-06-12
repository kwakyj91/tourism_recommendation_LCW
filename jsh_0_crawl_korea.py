"""
한국 축제/행사 네이버 블로그 리뷰 크롤러 — API 키 불필요
출력: korea_festival_reviews.csv  (country, city, activity, review, month, rating)

동작 방식:
  축제명마다 Naver 블로그 검색 "{축제명} 리뷰" (기간 1년, 관련도순) 로
  상위 REVIEWS_PER_FESTIVAL 개의 포스트 설명문을 리뷰로 수집
"""

import re
import time
import random
import requests
import pandas as pd
from urllib.parse import quote
from bs4 import BeautifulSoup

OUTPUT_CSV           = "jsh_korea_festival_reviews.csv"
REVIEWS_PER_FESTIVAL = 150  # 축제당 최대 수집 리뷰 수 (페이지당 30개 → 최대 5페이지)
SLEEP_MIN            = 1.0  # 요청 간 딜레이 범위(초)
SLEEP_MAX            = 2.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://www.naver.com/",
}

# ─── 축제 목록 (지역·시기 분류) ───────────────────────────────────────────────
FESTIVALS = [
    # 서울
    {"city": "서울",  "activity": "서울빛초롱축제",              "month": 11},
    {"city": "서울",  "activity": "서울세계불꽃축제",            "month": 10},
    {"city": "서울",  "activity": "서울재즈페스티벌",            "month": 5},
    {"city": "서울",  "activity": "서울세계도시문화축제",         "month": 5},
    {"city": "서울",  "activity": "한국민속예술축제",            "month": 10},
    {"city": "서울",  "activity": "서울거리예술축제",            "month": 10},
    {"city": "서울",  "activity": "서울국제만화애니메이션페스티벌", "month": 8},
    # 부산
    {"city": "부산",  "activity": "부산국제영화제",              "month": 10},
    {"city": "부산",  "activity": "부산불꽃축제",                "month": 10},
    {"city": "부산",  "activity": "광안리어방축제",              "month": 4},
    {"city": "부산",  "activity": "부산바다축제",                "month": 8},
    {"city": "부산",  "activity": "부산국제록페스티벌",          "month": 8},
    # 제주
    {"city": "제주",  "activity": "제주들불축제",                "month": 3},
    {"city": "제주",  "activity": "제주유채꽃축제",              "month": 3},
    {"city": "제주",  "activity": "제주들꽃축제",                "month": 4},
    {"city": "제주",  "activity": "제주한라문화제",              "month": 10},
    # 강원
    {"city": "강원",  "activity": "화천산천어축제",              "month": 1},
    {"city": "강원",  "activity": "인제빙어축제",                "month": 1},
    {"city": "강원",  "activity": "춘천마임축제",                "month": 5},
    {"city": "강원",  "activity": "평창효석문화제",              "month": 9},
    {"city": "강원",  "activity": "강릉커피축제",                "month": 10},
    {"city": "강원",  "activity": "양양연어축제",                "month": 10},
    {"city": "강원",  "activity": "화천쪽배축제",                "month": 8},
    # 경남
    {"city": "경남",  "activity": "진주남강유등축제",            "month": 10},
    {"city": "경남",  "activity": "통영한산대첩축제",            "month": 8},
    {"city": "경남",  "activity": "함안낙화놀이",               "month": 5},
    {"city": "경남",  "activity": "밀양아리랑대축제",           "month": 5},
    {"city": "경남",  "activity": "거제씨월드축제",             "month": 7},
    # 경북
    {"city": "경북",  "activity": "안동국제탈춤페스티벌",        "month": 9},
    {"city": "경북",  "activity": "문경찻사발축제",              "month": 4},
    {"city": "경북",  "activity": "영덕대게축제",                "month": 3},
    {"city": "경북",  "activity": "청도소싸움축제",              "month": 3},
    {"city": "경북",  "activity": "봉화은어축제",                "month": 8},
    # 전남
    {"city": "전남",  "activity": "순천만갈대축제",              "month": 10},
    {"city": "전남",  "activity": "함평나비대축제",              "month": 4},
    {"city": "전남",  "activity": "여수밤바다불꽃축제",          "month": 8},
    {"city": "전남",  "activity": "보성다향대축제",              "month": 5},
    {"city": "전남",  "activity": "구례산수유꽃축제",            "month": 3},
    {"city": "전남",  "activity": "담양대나무축제",              "month": 5},
    {"city": "전남",  "activity": "화순봄꽃축제",                "month": 4},
    # 전북
    {"city": "전북",  "activity": "김제지평선축제",              "month": 10},
    {"city": "전북",  "activity": "전주한옥마을벚꽃축제",        "month": 4},
    {"city": "전북",  "activity": "전주국제영화제",              "month": 5},
    {"city": "전북",  "activity": "무주반딧불축제",              "month": 9},
    {"city": "전북",  "activity": "남원춘향제",                  "month": 5},
    # 충남
    {"city": "충남",  "activity": "보령머드축제",                "month": 7},
    {"city": "충남",  "activity": "천안흥타령춤축제",            "month": 9},
    {"city": "충남",  "activity": "서산해미읍성역사체험축제",     "month": 10},
    {"city": "충남",  "activity": "태안빛축제",                  "month": 12},
    {"city": "충남",  "activity": "공주백제문화제",              "month": 10},
    {"city": "충남",  "activity": "부여서동연꽃축제",            "month": 7},
    # 충북
    {"city": "충북",  "activity": "청주직지축제",                "month": 9},
    {"city": "충북",  "activity": "괴산고추축제",                "month": 9},
    {"city": "충북",  "activity": "보은대추축제",                "month": 10},
    {"city": "충북",  "activity": "충주세계무술축제",            "month": 9},
    # 경기
    {"city": "경기",  "activity": "수원화성문화제",              "month": 10},
    {"city": "경기",  "activity": "안산국제거리극축제",          "month": 5},
    {"city": "경기",  "activity": "화성뱃놀이축제",              "month": 5},
    {"city": "경기",  "activity": "양평용문산산나물축제",        "month": 4},
    {"city": "경기",  "activity": "연천구석기축제",              "month": 5},
    # 인천
    {"city": "인천",  "activity": "인천펜타포트락페스티벌",      "month": 8},
    {"city": "인천",  "activity": "인천차이나타운문화축제",      "month": 5},
    {"city": "인천",  "activity": "강화고려인삼축제",            "month": 10},
    # 대구
    {"city": "대구",  "activity": "대구치맥페스티벌",            "month": 7},
    {"city": "대구",  "activity": "대구국제뮤지컬페스티벌",      "month": 6},
    {"city": "대구",  "activity": "대구컬러풀페스티벌",          "month": 5},
    # 광주
    {"city": "광주",  "activity": "광주비엔날레",                "month": 9},
    {"city": "광주",  "activity": "광주프린지페스티벌",          "month": 6},
    {"city": "광주",  "activity": "광주김치축제",                "month": 10},
    # 대전
    {"city": "대전",  "activity": "대전사이언스페스티벌",        "month": 10},
    {"city": "대전",  "activity": "대전맥주축제",                "month": 6},
    {"city": "대전",  "activity": "대전효문화뿌리축제",          "month": 10},
    # 울산
    {"city": "울산",  "activity": "울산옹기축제",                "month": 5},
    {"city": "울산",  "activity": "울산고래축제",                "month": 5},
    {"city": "울산",  "activity": "태화강국제설치미술제",        "month": 10},
]


# ─── 네이버 블로그 리뷰 스크래핑 ──────────────────────────────────────────────
def scrape_reviews(festival_name: str, count: int = REVIEWS_PER_FESTIVAL) -> list[str]:
    """페이지당 30개, count에 도달하거나 결과 소진될 때까지 페이지 순회"""
    query = quote(f"{festival_name} 리뷰")
    base_url = (
        f"https://search.naver.com/search.naver"
        f"?ssc=tab.blog.all&query={query}&sm=tab_opt&nso=so%3Ar%2Cp%3A1y"
    )
    reviews = []
    start = 1

    while len(reviews) < count:
        url = f"{base_url}&start={start}"
        try:
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [요청 실패 start={start}] {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        bodies = soup.select("span.sds-comps-text-type-body1")
        if not bodies:
            break  # 결과 소진

        page_reviews = []
        for el in bodies:
            text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
            if len(text) > 30:
                page_reviews.append(text)

        if not page_reviews:
            break

        reviews.extend(page_reviews)
        start += 30

    return reviews[:count]


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  한국 축제/행사 네이버 블로그 리뷰 크롤링")
    print(f"  대상 축제: {len(FESTIVALS)}개 | 축제당 최대 {REVIEWS_PER_FESTIVAL}개")
    print("=" * 60)

    rows = []
    skipped = 0

    for i, fest in enumerate(FESTIVALS, 1):
        name  = fest["activity"]
        city  = fest["city"]
        month = fest["month"]

        reviews = scrape_reviews(name)

        if not reviews:
            print(f"[{i:3d}/{len(FESTIVALS)}] {city} | {name:<20s} → 리뷰 없음")
            skipped += 1
            continue

        for rev in reviews:
            rows.append({
                "country":  "korea",
                "city":     city,
                "activity": name,
                "review":   rev,
                "month":    month,
                "rating":   None,
            })
        print(f"[{i:3d}/{len(FESTIVALS)}] {city} | {name:<20s} → {len(reviews)}개")

    if not rows:
        print("\n수집된 데이터가 없습니다.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print(f"  저장: {OUTPUT_CSV}")
    print(f"  총 {len(df)}행 | 축제 {df['activity'].nunique()}개 | 스킵 {skipped}개")
    print("=" * 60)
    print("\n도시별 리뷰 수:")
    print(df.groupby("city")["review"].count().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
