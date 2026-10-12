# 로컬 클립 제작기

## 실행

이 폴더의 `start.vbs`를 더블클릭합니다. 실행되지 않으면 PowerShell에서:

```powershell
python C:/blog/shorts/local_clipper/app.py
```

1. YouTube 링크를 붙여 넣거나 로컬 영상 파일을 선택합니다.
2. **원본·대사 준비**를 누릅니다. 한국어 음성을 우선 다운로드하고, 로컬 faster-whisper로 대사를 인식합니다.
3. **후보 구간 재생**으로 장면을 확인합니다. 후보는 키워드 기반 초안이며 재미를 이해하는 AI 모델의 순위가 아닙니다.
4. 후보를 선택한 뒤 시작·종료 시간과 제목 두 줄을 수정합니다. 전체 대사를 보고 직접 구간을 지정할 수도 있습니다.
5. 상황 자막을 한 줄에 하나씩 입력하고 **세로 영상 만들기**를 누릅니다.
6. **완성본 재생**으로 확인합니다. 1080×1920 H.264/AAC MP4가 `renders`에 저장됩니다.

이전에 만든 예시는 **샘플 편집 설정 불러오기 → 세로 영상 만들기**로 재현할 수 있습니다.
GUI는 상황 자막을 균등한 시간으로 배분합니다. 장면별 정확한 표시 시간은 JSON 설정을 이용합니다.
자동 대사 인식 결과는 구간 찾기용입니다. 현재 영상 합성에는 원본에 박힌 방송 자막과 직접 입력한 상황 자막을 사용하며, 인식된 전체 대사를 자동으로 덮어쓰지 않습니다.

## 사용량을 줄이는 방식

- 이 프로그램에는 Codex·유료 AI API 호출이 없습니다. 단독 실행 중에는 AI 서비스 토큰을 소비하지 않습니다.
- 링크 다운로드와 최초 모델 다운로드에는 인터넷이 필요합니다. 음성 인식과 편집은 로컬 CPU에서 처리합니다.
- 원본과 모델별 대사를 캐시합니다. 같은 영상은 다시 인식하지 않습니다.
- 같은 원본·편집 설정은 검사가 끝난 완성본을 재사용합니다. 제목만 바꿔도 음성 인식은 반복하지 않습니다.
- AI 도움이 필요할 때만 작업 폴더의 `review-brief.md`를 전달합니다. 최대 6개 후보 대사만 포함하며, 전체 영상이나 긴 로그를 매번 읽힐 필요가 없습니다.
- 검토 자료만으로는 표정·타이밍을 판단하기 어렵습니다. 필요할 때 해당 짧은 구간만 추가 확인합니다.

## 명령줄 및 여러 개 제작

```powershell
python C:/blog/shorts/local_clipper/pipeline.py prepare "https://www.youtube.com/watch?v=VIDEO_ID"
python C:/blog/shorts/local_clipper/pipeline.py render C:/blog/shorts/local_clipper/sample-edit.json
python C:/blog/shorts/local_clipper/pipeline.py batch first.json second.json
```

`sample-edit.json`을 복사해 원본 경로, 시작·종료 초, 제목, 자막을 바꿉니다.
상황 자막의 `start`와 `end`는 원본 시간이 아니라 잘라낸 클립의 0초 기준입니다.
최대 90초, 제목 두 줄, 상황 자막 최대 8개입니다. 긴 제목은 자동 축소하며 너무 길면 오류를 표시합니다.

## 폴더

- `jobs/<id>/source.json`: 원본 정보
- `transcript-small.json`, `transcript.txt`: 시간별 대사
- `candidates.json`, `review.html`: 구간 후보와 로컬 재생 화면
- `review-brief.md`: AI에 전달할 짧은 검토 자료
- `renders/<id>/edit.json`: 완성본을 재현할 편집 설정
- `clip.mp4`, `preview.jpg`, `verified.json`: 영상·미리보기·검사 결과

현재 CPU에서 `small` 모델을 기본으로 사용합니다. `base`는 빠른 초안, `medium`은 더 느린 정밀 인식용입니다. 모델 선택만 바꾸면 캐시를 별도로 저장합니다.
전체 디코딩, 해상도, 길이, 음성 트랙 유무를 자동 검사합니다. 재미·오인식·말 끊김은 사람이 최종 확인해야 합니다.
게시·업로드는 수행하지 않습니다. 다운로드 가능 여부와 재사용 허가는 별개이므로 원본 이용 조건은 별도 확인합니다.

## 설치 및 문제 해결

이 PC에는 필요한 패키지가 설치돼 있습니다. 다른 PC라면 Python과 Node.js를 설치하고 `python -m pip install -r requirements.txt`를 실행합니다. Windows 맑은 고딕 글꼴이 필요합니다.
다운로드 오류는 `download.log`, 인식용 음성 추출 오류는 `audio.log`, 편집 오류는 `render.log`에 남습니다.
YouTube 다운로드 방식이 바뀌면 `python -m pip install --upgrade yt-dlp`로 업데이트합니다. 로그인·유료 구독·접근 제한을 우회하는 기능은 없습니다.

참고: [yt-dlp](https://github.com/yt-dlp/yt-dlp), [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
