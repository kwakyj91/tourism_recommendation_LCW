import numpy as np
import pandas as pd
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PREPROCESSED_FILE = "jsh_activity_df_korea.pkl"
MODEL_FILE        = "jsh_tfidf_model_korea.pkl"


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^가-힣㄰-㆏\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def recommend(query, vectorizer, tfidf_matrix, activity_df, top_n=5):
    query_vec = vectorizer.transform([clean_text(query)])
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_idx = scores.argsort()[::-1][:top_n]
    results = activity_df.iloc[top_idx][["city", "activity", "month", "rating"]].copy()
    results["score"] = np.round(scores[top_idx], 4)
    return results[results["score"] > 0].reset_index(drop=True)


def main():
    with open(PREPROCESSED_FILE, "rb") as f:
        activity_df = pickle.load(f)
    print(f"전처리 데이터 로드 완료: 활동 {len(activity_df)}개")

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(activity_df["clean_review"])
    print(f"TF-IDF 행렬: {tfidf_matrix.shape}")

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(
            {
                "vectorizer": vectorizer,
                "matrix": tfidf_matrix,
                "activities": activity_df,
            },
            f,
        )
    print(f"모델 저장 완료: {MODEL_FILE}\n")

    test_queries = ["불꽃 야경", "전통 문화", "음식 먹거리", "겨울 눈", "봄꽃"]
    for q in test_queries:
        print(f"[쿼리] '{q}'")
        result = recommend(q, vectorizer, tfidf_matrix, activity_df, top_n=3)
        if result.empty:
            print("  결과 없음")
        else:
            for _, row in result.iterrows():
                month_str = f"{int(row['month'])}월" if pd.notna(row['month']) else "-"
                rating_str = f"{row['rating']:.1f}★" if pd.notna(row['rating']) else "-"
                print(f"  {row['city']:10s} | {row['activity'][:30]:30s} | {month_str:4s} | {rating_str} | score={row['score']}")
        print()


if __name__ == "__main__":
    main()
