# WordDecoder 数据集成说明

本项目将 [RichardoZhao/WordDecoder](https://github.com/RichardoZhao/WordDecoder) 作为主要构词与核心词根校准源。

- 本地镜像：`third_party/worddecoder/`
- 上游数据版本：`lexicon.json` 中的 `meta.version`
- 上游许可证：MIT，见 `third_party/worddecoder/LICENSE`
- 导入范围：中考、高考、四级、六级、考研、托福、雅思
- 排除范围：小学

`sync_vocab_data.py` 只导入具有可用中文释义的词条。归类优先采用原书分析串和教材断法；仅在剩余基础词本身存在于考试/教材词表时才进行保守回溯。没有可靠核心词根证据的词不会按开头字母强行放入通用前缀卡片。

每次构建会生成 `data/worddecoder_import_audit.json`，记录新增词、迁移词、数据版本和可用范围。每个词还会保留 `scopes`、`wordDecoderAnalysis`、`etymologySource` 和结构化 `morphemes`（有可靠拆分时）字段。
