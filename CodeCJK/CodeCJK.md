# CodeCJK

支援中日韓的編程字型檔

## 特點

![Font debug](debug_clip.png)

* 支援中日韓字元。
* 字距等寛，Monospace。
  * 半型字如 Ascii 寛度為 1 單位。
  * 全型字如中文寛度為 2 單位。
* 容易辨別相似的字元，如 1Il| 0O 。

## 支援軟件

* Visual Studio Code
* Notepad++
* Eclipse
* PuTTY

## 不支援軟件

* 中文 Windows 11 Notepad: 自己的細明體也顯示不了等距，英文 Windows 反而正常。

## 來源字型

這個字型檔使用了以下字型

* 主要字型: [JetBrains Mono NL](https://www.jetbrains.com/lp/mono/)
* CJK 字型: [Noto Sans Mono CJK HK](https://github.com/notofonts/noto-cjk/tree/main)

## 下載

[CodeCJK004](https://www.dropbox.com/scl/fo/d5k6lswmoa31vuvgooshe/AEa-e7DcBrXNyI5zDMiW3KI?rlkey=5c1ftf6xpk7n0apns5xw500zn&st=61aq0pv6&dl=0)

## 如何製造 CodeCJK 字型檔

```bash
CodeCJK/build.sh
```

## 其他

* CodeCJK *是字型檔，不是字型*。因為它只是直接使用坊間既有的字型，而沒有設計自己的字型。
