from pynuixo import PyNuixo
from pynuixo import LoginState
from pynuixotools import PyNuixoTools

# ユーザーIDとパスワードを入力してください
nuixo = PyNuixo("UserID", "PASSWORD")

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

this_month_scores = nuixo_tools.get_this_month_subject_scores()
print("\n今月の成績情報:")
for score in this_month_scores:
    print(f"科目名: {score.subject}, 提出期日: {score.limit}, 進捗率: {score.percentage}%, 点数: {score.score}")