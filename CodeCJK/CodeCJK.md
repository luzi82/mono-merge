# CodeCJK

支援中日韓的編程字型檔

## 特點

![Font debug](img/debug_clip.png)

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

* 基礎字型: [Fira Code](https://github.com/tonsky/FiraCode)
* 增補字型: [Inconsolata](https://fonts.google.com/specimen/Inconsolata)
* CJK 字型: [Noto Sans Mono CJK HK](https://github.com/notofonts/noto-cjk/tree/main)

## 下載

[CodeCJK005](https://github.com/luzi82/mono-merge/releases/tag/CodeCJK005)

## 如何生成 CodeCJK 字型檔

```bash
python CodeCJK/build.py
```

## 變體

* **P**CodeCJK 是沒有註明 monospace 的字型，但它的字距還是對齊。
* CodeCJK**123** 是鎖定版本號的發佈。將來版本必定會增加版本數字。如果你想讓不同軟件用不同版本的 CodeCJK，就可以使用這個發佈。

## License

SIL Open Font License, Version 1.1

## 其他

* CodeCJK *是字型檔，不是字型*。因為它只是直接使用坊間既有的字型，而沒有設計自己的字型。
