from datetime import datetime

class PyNuixoTools:
    def __init__(self, subjectScores):
        self.subjectScores = subjectScores

    def get_this_month_subject_scores(self, month=None):
        """
        特定の月の成績情報を取得する
        month: 取得したい月（1〜12）。Noneの場合は今月
        """
        if month is None:
            today = datetime.today()
            month = today.month
        
        # データに存在する月を確認
        available_months = set()
        for ss in self.subjectScores:
            if '/' in ss.limit:
                try:
                    m = int(ss.limit.split('/')[0])
                    available_months.add(m)
                except ValueError:
                    continue
        
        # 指定された月のデータがない場合、利用可能な最新の月を使用
        if month not in available_months and available_months:
            month = max(available_months)
        
        this_month_subjectScores = []
        for ss in self.subjectScores:
            if '/' in ss.limit:
                try:
                    m = int(ss.limit.split('/')[0])
                    if m == month:
                        this_month_subjectScores.append(ss)
                except ValueError:
                    continue
        
        return this_month_subjectScores

    def to_csv(self):
        csv = "教科名, 締め切り, 進捗率, 点数"
        for ss in self.subjectScores:
            csv += f"\n{ss.subject}, {ss.limit}, {ss.percentage}, {ss.score}"
        return csv

    def get_subjects(self):
        all_duplicate_subjects = []
        for subjectScore in self.subjectScores:
            all_duplicate_subjects.append(subjectScore.subject)
        return list(set(all_duplicate_subjects))
