from app import db
from datetime import datetime, timedelta

class Debate(db.Model):
    """辯論模型"""
    __tablename__ = "debates"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    
    # 參與者
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pro_participant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    con_participant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # 狀態
    status = db.Column(db.String(20), default='waiting')  # waiting, ongoing, judging, completed
    
    # 時間設定
    time_limit_hours = db.Column(db.Integer, default=24)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    current_deadline = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # 當前輪次
    current_round = db.Column(db.Integer, default=0)
    current_turn = db.Column(db.String(10), nullable=True)  # 'pro' or 'con'
    
    # 設定
    need_sources = db.Column(db.Boolean, default=True)
    allow_audience = db.Column(db.Boolean, default=True)
    level_limit = db.Column(db.String(20), nullable=True)
    
    # 統計
    views = db.Column(db.Integer, default=0)
    
    # 關聯
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_debates')
    pro_participant = db.relationship('User', foreign_keys=[pro_participant_id])
    con_participant = db.relationship('User', foreign_keys=[con_participant_id])
    arguments = db.relationship('Argument', backref='debate', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def participants_count(self):
        """參與者數量"""
        count = 0
        if self.pro_participant_id:
            count += 1
        if self.con_participant_id:
            count += 1
        return count
    
    @property
    def is_full(self):
        """是否已滿員"""
        return self.pro_participant_id is not None and self.con_participant_id is not None
    
    @property
    def time_remaining(self):
        """剩餘時間"""
        if self.current_deadline:
            remaining = self.current_deadline - datetime.utcnow()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                if hours > 0:
                    return f"{hours}小時{minutes}分鐘"
                else:
                    return f"{minutes}分鐘"
        return None
    
    @property
    def is_urgent(self):
        """是否緊急（剩餘時間少於6小時）"""
        if self.current_deadline:
            remaining = self.current_deadline - datetime.utcnow()
            return remaining.total_seconds() < 6 * 3600
        return False

class Argument(db.Model):
    """論述模型"""
    __tablename__ = "arguments"

    id = db.Column(db.Integer, primary_key=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    position = db.Column(db.String(10), nullable=False)  # 'pro' or 'con'
    round_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text, nullable=True)  # JSON格式儲存來源
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref='arguments')

class HallMessage(db.Model):
    """大廳訊息模型"""
    __tablename__ = "hall_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='general')  # general, challenge
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref='hall_messages')

class DebateRating(db.Model):
    """辯論評分模型"""
    __tablename__ = "debate_ratings"

    id = db.Column(db.Integer, primary_key=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    pro_score = db.Column(db.Integer, nullable=False)  # 1-10分
    con_score = db.Column(db.Integer, nullable=False)  # 1-10分
    winner = db.Column(db.String(10), nullable=True)  # 'pro', 'con', or 'tie'
    
    # 評分標準
    logic_score_pro = db.Column(db.Integer, nullable=True)
    logic_score_con = db.Column(db.Integer, nullable=True)
    evidence_score_pro = db.Column(db.Integer, nullable=True)
    evidence_score_con = db.Column(db.Integer, nullable=True)
    presentation_score_pro = db.Column(db.Integer, nullable=True)
    presentation_score_con = db.Column(db.Integer, nullable=True)
    
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    debate = db.relationship('Debate', backref='ratings')
    judge = db.relationship('User', backref='judge_ratings')

class UserStats(db.Model):
    """用戶統計模型"""
    __tablename__ = "user_stats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 基本統計
    total_debates = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    ties = db.Column(db.Integer, default=0)
    
    # 評分
    rating = db.Column(db.Integer, default=1200)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    # 專業領域
    best_categories = db.Column(db.Text, nullable=True)  # JSON格式
    
    # 時間統計
    total_time_debating = db.Column(db.Integer, default=0)  # 分鐘
    average_response_time = db.Column(db.Integer, default=0)  # 分鐘
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref=db.backref('stats', uselist=False))
    
    @property
    def win_rate(self):
        """勝率"""
        if self.total_debates == 0:
            return 0
        return round((self.wins / self.total_debates) * 100, 1)

class DebateFollow(db.Model):
    """辯論關注模型"""
    __tablename__ = "debate_follows"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 設定唯一約束
    __table_args__ = (db.UniqueConstraint('user_id', 'debate_id'),)
    
    # 關聯
    user = db.relationship('User', backref='followed_debates')
    debate = db.relationship('Debate', backref='followers_rel')