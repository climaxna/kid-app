# 이미지 매니페스트

글마다 `assets/posts/<slug>/manifest.json`을 만들고 이미지 생성·검수 상태를 기록한다.
이 파일은 내부 작업 자료이며 네이버 본문에 넣지 않는다.

```json
{
  "version": 1,
  "content_type": "parenting_info",
  "preset": "PARENTING_PRO_V1",
  "draft": "parenting/example.md",
  "images": [
    {
      "number": 1,
      "role": "thumbnail",
      "section": "도입",
      "mode": "GENERATED_SCENE",
      "ratio": "16:9",
      "file": "assets/posts/example/01-thumbnail.png",
      "prompt": "이 이미지에만 필요한 장면과 문구",
      "status": "ready",
      "qa": {
        "text": true,
        "anatomy": true,
        "safety": true,
        "privacy": true,
        "ratio": true
      }
    }
  ]
}
```

## 규칙

- `prompt`에는 `IMAGE_STYLE_PRESETS.md`의 공통 문장을 반복하지 않고 이 이미지에만 필요한
  장면, 구도, 정확한 짧은 문구와 개별 주의점만 기록한다.
- `status`는 `planned`, `generated`, `ready`, `rejected` 중 하나다.
- 네이버 임시저장 전 사용하는 모든 항목은 `ready`이고 QA 항목이 모두 `true`여야 한다.
- `REAL_PHOTO_REFERENCE` 결과 파일은 `assets/posts/`에 두고 생성 이미지로 공개한다.
- 생성 이미지 항목에는 `disclosure`을 기록하지 않으며 네이버 본문에도 반복 안내 문구를
  붙이지 않는다.
- 원본과 직접 편집 사진은 `private_media/` 아래에 두며 다른 글에서 재사용하지 않는다.

## 섬 비교 전용 규칙

- `content_type`이 `island_compare`이면 이미지 수는 정확히 4장이다.
- 네 장의 `ratio`는 모두 `1:1`, 목표 크기는 1080×1080px이다.
- `role`은 번호 순서대로 `thumbnail`, `comparison_overview`, `attractions`,
  `final_recommendation`을 한 번씩 사용한다.
- `content_type`이 `parenting_info`이면 `thumbnail`, `opening_scene`,
  `key_information`, `summary_recommendation` 4장을 기본으로 한다.
- 각 항목은 독립 파일이어야 하며 한 이미지에 여러 번호의 역할을 합치지 않는다.
- QA에는 `text`, `geography`, `composition`, `privacy`, `ratio`, `photo_first`,
  `independent_file`, `no_duplicate_scene`을 기록한다.
