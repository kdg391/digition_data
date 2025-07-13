# Data

- 키워드: "SKT", "유심"
- 각 타임 별로 약 100 ~ 1,000개의 데이터 수집
- 광고, 뉴스 기사 필터링은 직접 진행

## 속성

|이름|설명|예시|
|-|-|-|
|created_at|트윗 작성 시간(YYYY-mm-DD HH:MM:SS)|2025-04-23 06:57:17|
|text|트윗 내용|당장은 유심 잠금이라도 해놔야… 오늘 가서 유심 바꾸던가 해야겠다. SKT놈들이 공짜로 해줘야 하는거 아니냐!!|
|sentiment|감정 분석 결과(positive, negative)<br>score가 0.5이상일 경우 positive, 아니면 negative|positive|
|score|0에 가까울수록 negative, 1에 가까울수록 positive|0.03234325203|

## 감정 분석 모델

<https://huggingface.co/sangrimlee/bert-base-multilingual-cased-nsmc>

[Naver sentiment movie corpus](https://github.com/e9t/nsmc) 데이터를 파인 튜닝한 한국어 감정 분석 모델
