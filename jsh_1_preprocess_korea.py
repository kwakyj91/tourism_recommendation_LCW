import pandas as pd
import re
import pickle

CSV_FILE         = "jsh_korea_festival_reviews.csv"
PREPROCESSED_FILE = "jsh_activity_df_korea.pkl"


def is_korean(text):
    text = str(text)
    korean_ratio = sum(1 for c in text if '가' <= c <= '힣') / max(len(text), 1)
    return korean_ratio > 0.1


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^가-힣㄰-㆏\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
    print(f"원본 데이터: {len(df)}행")

    df = df[df["review"].apply(is_korean)].copy()
    print(f"한국어 필터 후: {len(df)}행")

    df["clean_review"] = df["review"].apply(clean_text)

    activity_df = (
        df.groupby(["country", "city", "activity"])["clean_review"]
        .apply(" ".join)
        .reset_index()
    )

    if "month" in df.columns:
        def safe_mode(x):
            valid = x.dropna()
            return int(valid.mode()[0]) if not valid.empty else None
        month_df = df.groupby(["country", "city", "activity"])["month"].agg(safe_mode).reset_index()
        activity_df = activity_df.merge(month_df, on=["country", "city", "activity"])
    else:
        activity_df["month"] = None

    if "rating" in df.columns:
        rating_df = df.groupby(["country", "city", "activity"])["rating"].mean().round(1).reset_index()
        activity_df = activity_df.merge(rating_df, on=["country", "city", "activity"])
    else:
        activity_df["rating"] = None

    activity_df["activity_ko"] = activity_df["activity"]

    print(f"고유 활동 수: {len(activity_df)}개")

    with open(PREPROCESSED_FILE, "wb") as f:
        pickle.dump(activity_df, f)
    print(f"전처리 데이터 저장 완료: {PREPROCESSED_FILE}")


if __name__ == "__main__":
    main()
