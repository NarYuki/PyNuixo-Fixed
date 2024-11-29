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
        subjects = [item.text.strip().replace('\n', '') for item in soup.find_all(attrs={'rowspan': '4'})]
        report_number = len(soup.find_all(attrs={'class': 'header_report_number'}))
        limit_dates = [item.text.strip() for item in soup.find_all(attrs={'class': 'report_limit_date'})]

        progress_rows = soup.find_all('tr', class_='subject_2st_row')
        persents = []
        scores = []
        for row in progress_rows:
            th_text = row.find('th').text.strip()
            if th_text == '進捗率':
                persents += [td.text.strip().replace('%', '') for td in row.find_all('td', class_='report_progress')]
            elif th_text == '点数':
                scores += [td.text.strip() for td in row.find_all('td', class_='report_progress')]

        subject_scores = []
        limit_index = 0
        for i, subject in enumerate(subjects):
            for j in range(report_number):
                if limit_index >= len(limit_dates):
                    break
                limit = limit_dates[limit_index]
                limit_index += 1
                if limit == "-":
                    continue

                index = i * report_number + j
                if index >= len(persents) or index >= len(scores):
                    continue
                persent = persents[index]
                score = scores[index]

                if not score or score == '-' or score == '採点待':
                    continue

                subject_scores.append(
                    SubjectScore(
                        subject=subject,
                        limit=limit,
                        percentage=int(persent) if persent.isdigit() else 0,
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