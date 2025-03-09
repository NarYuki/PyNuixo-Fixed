import os
from dataclasses import dataclass
from enum import Enum
import pickle

import requests
from bs4 import BeautifulSoup


def split_list(l, n):
    """
    Listを分割
    :param l: List
    :param n: 分割数
    :return: 
    """
    for idx in range(0, len(l), n):
        yield l[idx:idx + n]


@dataclass
class SubjectScore:
    subject: str
    limit: str
    percentage: int
    score: str


class LoginState(Enum):
    SUCCESS = "成功"
    WRONG_ACCOUNT = "学籍番号またはパスワードが違います"
    NOT_ENTERED = "ログインIDまたはパスワードに未入力項目があります。"
    PASS_RESET = "パスワードのリセットを行ってください"
    REAUTH_FAILED = "再認証失敗"
    NETWORK_ERROR = "ネットワークエラー"
    CANT_USE = "マイページを使用することはできません"


class School(Enum):
    N = "https://secure.nnn.ed.jp"
    S = "https://s-secure.nnn.ed.jp"

    def get_base_url(self):
        return self.value


class MyPageURLs(Enum):
    TOKEN_PATH = "/mypage/"
    LOGIN_PATH = "/mypage/login"
    REAUTH_TOKEN_PATH = "/mypage/reauth_login/index?url=/result/pc/list/index"
    REAUTH_PATH = "/mypage/reauth_login/login"
    SCORE_PATH = "/mypage/result/pc/list/index"
    RESET_PASS_PATH = "/mypage/password_reminder/input"

    def get_url(self, school) -> str:
        return school.get_base_url() + self.value


class PyNuixo:
    def __init__(self, username, password):
        self.username = username.upper()
        self.password = password

        self.cookie_path = "cookies.pkl"
        self.header = {
            'User-Agent': 'PyNuixoFixed'
        }
        self.session = requests.Session()

        if os.path.exists(self.cookie_path):
            self.__load_cookies(self.session)

        self.school = self.__username2school(self.username)

    def login(self) -> LoginState:
        res = self.session.get(MyPageURLs.TOKEN_PATH.get_url(self.school))
        soup = BeautifulSoup(res.text, "html.parser")
        token = soup.find(attrs={'name': '_token'}).get('value')

        data = {
            'loginId': self.username,
            'password': self.password,
            'url': '/result/pc/list/index',
            '_token': token
        }

        response = self.session.post(MyPageURLs.LOGIN_PATH.get_url(self.school), data=data,
                                     headers=self.header, allow_redirects=False)

        login_state = self.__check_login_state(response.text)

        if login_state == LoginState.SUCCESS:
            self.__save_cookies(self.session)

        return login_state

    def reauth(self) -> LoginState:
        reauth_responce = self.session.get(MyPageURLs.REAUTH_TOKEN_PATH.get_url(self.school), headers=self.header)
        soup = BeautifulSoup(reauth_responce.text, "html.parser")
        token = soup.find(attrs={'name': '_token'}).get('value')

        posted = self.session.post(MyPageURLs.REAUTH_PATH.get_url(self.school), data={
            "url": "/result/pc/list/index", "password": self.password, "_token": token}, headers=self.header,
                                   allow_redirects=False)
        if "認証に失敗" in posted.text:
            print("認証に失敗しました。パスワードが正しく入力できているか確認してください。")
            return LoginState.REAUTH_FAILED

        return LoginState.SUCCESS

    def fetch_subject_scores(self) -> [SubjectScore]:
        score_res = self.session.get(MyPageURLs.SCORE_PATH.get_url(self.school), headers=self.header)
        if "reauth_login" in score_res.url:
            self.reauth()
            score_res = self.session.get(MyPageURLs.SCORE_PATH.get_url(self.school), headers=self.header)
        return self.__score_parser(score_res.text)

    def __load_cookies(self, session):
        with open(self.cookie_path, "rb") as f:
            session.cookies = pickle.load(f)

    def __save_cookies(self, session):
        with open(self.cookie_path, "wb") as f:
            pickle.dump(session.cookies, f)

    def __score_parser(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        # 科目ごとのブロックを取得
        subject_blocks = []
        current_subject = None
        
        # 科目名を取得（rowspan='4'の要素）
        subject_elements = soup.find_all(attrs={'class': 'align_left', 'rowspan': '4'})
        
        # 各科目ブロックを処理
        subject_scores = []
        
        for subject_elem in subject_elements:
            subject_name = subject_elem.text.strip().replace('\n', '')
            
            # この科目の行を取得（親のtrから始まる4行）
            subject_row = subject_elem.parent
            
            # 提出期日の行（1行目）
            limit_dates_row = subject_row
            limit_dates = [td.text.strip() for td in limit_dates_row.find_all('td', class_='report_limit_date')]
            
            # 進捗率の行（3行目）
            progress_row = subject_row.find_next_sibling('tr').find_next_sibling('tr')
            progress_values = [td.text.strip().replace('%', '') for td in progress_row.find_all('td', class_='report_progress')]
            
            # 点数の行（4行目）
            score_row = progress_row.find_next_sibling('tr')
            score_values = [td.text.strip() for td in score_row.find_all('td', class_='report_progress')]
            
            # 各レポートの情報を組み合わせる
            for i in range(len(limit_dates)):
                if i >= len(progress_values) or i >= len(score_values):
                    continue
                    
                limit = limit_dates[i]
                if limit == "-":
                    continue
                    
                progress = progress_values[i]
                score = score_values[i]
                
                if not score or score == '-' or score == '採点待':
                    continue
                
                subject_scores.append(
                    SubjectScore(
                        subject=subject_name,
                        limit=limit,
                        percentage=int(progress) if progress.isdigit() else 0,
                        score=score.strip()
                    )
                )
        
        return subject_scores

    def __check_login_state(self, html) -> LoginState:
        if "学籍番号またはパスワードが違います" in html:
            return LoginState.WRONG_ACCOUNT
        elif "必須項目です" in html:
            return LoginState.NOT_ENTERED
        elif "パスワードのリセットを行ってください" in html:
            return LoginState.PASS_RESET
        elif "マイページを使用することはできません" in html:
            return LoginState.CANT_USE

        return LoginState.SUCCESS

    def __username2school(self, username) -> School:
        if "N" in username:
            return School.N
        elif "S" in username:
            return School.S
        else:
            return None
