<!-- ![PyNuixoHeader](https://user-images.githubusercontent.com/50548952/129435406-b7a3e8f6-ad04-4183-a3e6-aac9ba699c2c.png) -->

# N高 S高成績確認 Python版 Nuixo

> [!IMPORTANT]
> NarYukiがGPL3.0ライセンスに基づき、改変しているものです。
> 
> フォーク元への問い合わせなどはお控えください。

## Usage

### Python Script

```py
from pynuixo import PyNuixo
from pynuixo import LoginState
from pynuixotools import PyNuixoTools

# ユーザーIDとパスワードを入力してください
nuixo = PyNuixo("ID", "PASSWORD")

login_state = nuixo.login()
if login_state == LoginState.SUCCESS:
    print("ログインに成功しました。")
else:
    print(f"ログインに失敗しました: {login_state.value}")
    exit()

subject_scores = nuixo.fetch_subject_scores()

print("\n取得した成績情報:")
for score in subject_scores:
    print(f"科目名: {score.subject}, 提出期日: {score.limit}, 進捗率: {score.percentage}%, 点数: {score.score}")

nuixo_tools = PyNuixoTools(subject_scores)

csv_output = nuixo_tools.to_csv()
print("\nCSV形式での成績情報:")
print(csv_output)

# 今月の成績情報を取得（データがない場合は利用可能な最新の月を使用）
this_month_scores = nuixo_tools.get_this_month_subject_scores()
month_used = this_month_scores[0].limit.split('/')[0] if this_month_scores else "データなし"
print(f"\n{month_used}月の成績情報:")
for score in this_month_scores:
    print(f"科目名: {score.subject}, 提出期日: {score.limit}, 進捗率: {score.percentage}%, 点数: {score.score}")

```


Options

```py
nuixo.cookie_path = ""
```

### Command line

comming soon
<!-- ```
$ nuixopy this_month
``` -->

## Install

```
$pip3 install https://github.com/Nuixo/PyNuixo
```

## License

under the GPL v3.
