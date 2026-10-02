#!/bin/sh
# Downloads the candidate fonts into this folder (git-ignored). Sources are the upstream repositories.
cd "$(dirname "$0")"
N=https://github.com/notofonts/notofonts.github.io/raw/main/fonts
dl(){ [ -f "$2" ] || curl -sSL -f -o "$2" "$1" || echo "FAIL $1"; }
dl $N/NotoSansSymbols2/hinted/ttf/NotoSansSymbols2-Regular.ttf NotoSansSymbols2-Regular.ttf
dl $N/NotoSansSymbols/hinted/ttf/NotoSansSymbols-Regular.ttf NotoSansSymbols-Regular.ttf
dl $N/NotoSansDevanagari/hinted/ttf/NotoSansDevanagari-Regular.ttf NotoSansDevanagari-Regular.ttf
dl $N/NotoSansArabic/hinted/ttf/NotoSansArabic-Regular.ttf NotoSansArabic-Regular.ttf
dl $N/NotoSansHebrew/hinted/ttf/NotoSansHebrew-Regular.ttf NotoSansHebrew-Regular.ttf
dl $N/NotoSansMath/hinted/ttf/NotoSansMath-Regular.ttf NotoSansMath-Regular.ttf
dl 'https://github.com/google/fonts/raw/main/ofl/notoemoji/NotoEmoji%5Bwght%5D.ttf' NotoEmoji-VF.ttf
dl https://github.com/google/fonts/raw/main/ofl/notocoloremoji/NotoColorEmoji-Regular.ttf NotoColorEmoji-Regular.ttf
dl https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf NotoSansJP-Subset.otf
dl https://github.com/notofonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc NotoSansCJK-Regular.ttc
dl https://github.com/mozilla/twemoji-colr/releases/download/v0.7.0/Twemoji.Mozilla.ttf Twemoji.Mozilla.ttf
