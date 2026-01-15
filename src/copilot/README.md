# Copilot Module - Deeplink & Navigation

이 모듈은 PYLON 플랫폼의 딥링크(deep link) 생성 및 필터 상태 동기화를 제공합니다.

## 주요 기능

### 1. FilterParams
표준화된 필터 파라미터를 나타내는 dataclass입니다.

```python
from src.copilot.deeplink import FilterParams

filters = FilterParams(
    yymm=[202401, 202402],
    region=["수도권", "동부"],
    site_type=["기지국"],
    contract_type_major=["정액"],
    contract_target="한전계약(ME)",
    rapa="RAPA",
    network_gen=["5G"]
)
```

### 2. 딥링크 생성

```python
from src.copilot.deeplink import create_deeplink, FilterParams

filters = FilterParams(region=["수도권"], site_type=["기지국"])
url = create_deeplink("1_에너지_인텔리전스", filters=filters)
# Returns: "/1_에너지_인텔리전스?region=수도권&site_type=기지국"
```

### 3. Query Params 파싱

```python
from src.copilot.deeplink import parse_filters_from_query_params

# Streamlit 페이지에서
filter_params = parse_filters_from_query_params()
# URL의 query params에서 필터 값을 읽어옵니다
```

### 4. 필터 동기화

```python
from src.copilot.deeplink import sync_filters_with_query_params

# 기본 필터와 query params를 병합
default_filters = {...}
synced_filters = sync_filters_with_query_params(default_filters)
```

## Query Params 표준

다음 파라미터들이 지원됩니다:

- `yymm`: 월별 코드 리스트 (예: `yymm=202401&yymm=202402`)
- `region`: 지역 리스트 (예: `region=수도권&region=동부`)
- `site_type`: 설비유형 리스트 (예: `site_type=기지국&site_type=중계국`)
- `contract_type_major`: 계약유형 리스트 (예: `contract_type_major=정액`)
- `contract_target`: 계약대상 단일 값 (예: `contract_target=한전계약(ME)`)
- `rapa`: RAPA 여부 단일 값 (예: `rapa=RAPA`)
- `network_gen`: 네트워크 세대 리스트 (예: `network_gen=5G`)
- `month`: 월 선택 (Tab 3 전용, 예: `month=202401`)

## 사용 예시

### 페이지에서 사용

```python
# pages/1_에너지_인텔리전스.py
from components.global_controls import render_sidebar_filters

# Query params와 자동 동기화
filters = render_sidebar_filters(available_yymm, sync_with_query_params=True)
```

### Copilot에서 딥링크 생성

```python
from src.copilot.deeplink import create_deeplink, FilterParams

# 사용자 질의에 따라 필터 생성
filters = FilterParams(
    region=["수도권"],
    site_type=["기지국"],
    yymm=[202401, 202402]
)

# 딥링크 생성
link = create_deeplink("1_에너지_인텔리전스", filters=filters)
# 사용자에게 링크 제공
```

## 완료 기준

✅ 링크에 params가 포함되면 해당 페이지가 동일한 필터로 재현됩니다.

예:
```
http://localhost:8501/1_에너지_인텔리전스?region=수도권&site_type=기지국&yymm=202401
```

이 링크를 열면:
- 지역 필터: 수도권
- 설비유형 필터: 기지국
- 기간 필터: 2024년 1월

이 자동으로 적용됩니다.

