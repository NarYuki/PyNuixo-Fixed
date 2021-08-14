# N高 S高成績確認 Python版 Nuixo

## Usage

### Python Script

```py
from PyNuixo.pynuixo import PyNuixo
from PyNuixo.pynuixotools import PyNuixoTools

nuixo = PyNuixo("00N1111222", "password")

nuixo.login()
# <LoginState.SUCCESS: '成功'>

subject_scores = nuixo.fetch_subject_scores()
# SubjectScore(subject='国語総合(東京書籍版)', limit='6/15', percentage=100, score='100000000000')
# SubjectScore(subject='国語総合(東京書籍版)', limit='6/15', percentage=100, score='0')
# ...

nuixo_tools = PyNuixoTools(subject_scores)

csv = nuixo_tools.to_csv()
# 教科名, 締め切り, 進捗率, 点数

subjects = nuixo_tools.get_subjects()
# ("国語総合", "コミュ英", "古文",...)

# 今月のを返す。
this_month = nuixo_tools.get_this_month_subject_scores()

```


Options

```py
nuixo.cookie_path = ""
```

### Command line

```
$ nuixopy this_month
```

## Install

```
$pip3 install <this repoository URL>
```

## License

under the GPL v3.

**商用利用厳禁。**