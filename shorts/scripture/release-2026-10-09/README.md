# 2026년 10월 9일 말씀 영상 5편

각 34초, 1080x1920, 30fps, H264/AAC. B 목소리(Supertonic 3 M2, speed 0.90, steps 12)와 기존 피아노 음악을 유지했습니다.

## 영상

- 06-today.mp4: 내일 걱정으로 오늘이 힘들 때 · 마태복음 6:34
- 07-valley.mp4: 두려운 시간을 지나고 있는 당신에게 · 시편 23:4
- 08-peace.mp4: 마음의 평안이 필요한 날 듣는 말씀 · 요한복음 14:27
- 09-morning.mp4: 다시 시작할 힘이 필요한 아침 · 예레미야애가 3:22–23
- 10-family.mp4: 가족 걱정이 많은 날 함께 드리는 기도 · 시편 121:1–2

UPLOAD_GUIDE.md 및 각 *-upload.txt의 제목·설명·음악 출처를 복사하여 사용합니다. 공개 업로드는 실행하지 않았습니다.

## 새 배경과 프롬프트

내장 image_gen을 사용해 생성했습니다. API/CLI 생성은 사용하지 않았습니다.

- C:/blog/shorts/scripture/release-2026-10-09/backgrounds/lake.png
- C:/blog/shorts/scripture/release-2026-10-09/backgrounds/forest.png
- C:/blog/shorts/scripture/release-2026-10-09/backgrounds/meadow.png

최종 전체 프롬프트는 같은 backgrounds 폴더의 lake-prompt.md, forest-prompt.md, meadow-prompt.md에 있습니다. 공통 방향은 기존 승인 성화와 일관된 얼굴, 부드러운 유화 붓결, 절제된 색, 큰 자막을 위한 중앙 여백입니다.

각 원본에 풍경 영역 애니메이션을 합성하여 *-motion.mp4(12초 반복)를 만들었습니다. 구름 영역 이동, 물결 왜곡, 나뭇잎 또는 풀의 흔들림을 사용했습니다. 예수님 얼굴·손과 십자가를 움직이는 인물 영상은 아닙니다. 영상 생성 서비스는 OAuth 연결이 없어 사용하지 않았습니다.

## 확인

- 개역한글 인용문을 공식 배포 본문과 대조하고, 대본과 자막의 단어 일치를 검사했습니다. 각 편 출처 URL은 episodes.json과 업로드 설명에 있습니다.
- 말씀과 제작 묵상·기도를 화면 표기로 구분합니다.
- 모든 완성 MP4의 전체 디코드가 통과했습니다. 각 폴더의 QA.json에 길이, 음량 최대치와 자막 타이밍을 보존했습니다.
- 세 배경을 로컬 브라우저에서 실제 재생하여 정상 재생을 확인했습니다. 얼굴 영역의 프레임 간 차이는 합성 전 프레임 기준 0이며, 풍경 영역의 프레임 변화가 확인됐습니다. backgrounds/*-motion-QA.json 참고.
- 편별 주요 말씀·기도 화면을 눈으로 확인했습니다. 음성을 실제로 청취해 평가했다고 주장하지 않습니다.

## 제작 코드

- prepare_voice.py: 5편 낭독 생성
- animate_backgrounds.py: 풍경 영역 애니메이션
- build_five.py: 낭독·음악·자막 합성 및 검사
- preview.html: 5편 미리보기
- motion-check.html: 세 배경 동영상 비교

로컬 미리보기 주소: http://127.0.0.1:8872/preview.html
