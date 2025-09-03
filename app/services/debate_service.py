"""
辯論服務層 - 處理辯論相關業務邏輯
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import desc, or_, and_
from app import db
from app.models.debate import Debate, Argument, HallMessage, DebateRating, UserStats
from app.models.user import User


class DebateService:
    """辯論服務類"""
    
    @staticmethod
    def create_debate(user_id: int, data: Dict[str, Any]) -> Debate:
        """創建辯論"""
        debate = Debate(
            title=data['title'],
            description=data.get('description', ''),
            category=data['category'],
            creator_id=user_id,
            status='waiting',
            time_limit_hours=data.get('time_limit', 24),
            level_limit=data.get('level_limit'),
            need_sources=data.get('need_sources', True),
            allow_audience=data.get('allow_audience', True),
            created_at=datetime.utcnow(),
            views=0
        )
        
        # 設定創建者立場
        if data['position'] == 'pro':
            debate.pro_participant_id = user_id
        else:
            debate.con_participant_id = user_id
            
        db.session.add(debate)
        db.session.commit()
        return debate
    
    @staticmethod
    def join_debate(debate_id: int, user_id: int, position: str) -> bool:
        """加入辯論"""
        debate = Debate.query.get(debate_id)
        if not debate or debate.status != 'waiting':
            return False
            
        if position == 'pro' and debate.pro_participant_id is None:
            debate.pro_participant_id = user_id
        elif position == 'con' and debate.con_participant_id is None:
            debate.con_participant_id = user_id
        else:
            return False
            
        # 檢查是否雙方都有參與者
        if debate.pro_participant_id and debate.con_participant_id:
            debate.status = 'ongoing'
            debate.started_at = datetime.utcnow()
            debate.current_deadline = datetime.utcnow() + timedelta(hours=debate.time_limit_hours)
            debate.current_turn = 'pro'  # 正方先發言
            debate.current_round = 1
            
        db.session.commit()
        return True
    
    @staticmethod
    def get_debate_with_arguments(debate_id: int) -> Optional[Debate]:
        """獲取辯論及其論述"""
        debate = Debate.query.get(debate_id)
        if debate:
            # 增加觀看次數
            debate.views = (debate.views or 0) + 1
            db.session.commit()
        return debate
    
    @staticmethod
    def add_argument(debate_id: int, user_id: int, content: str, sources: str = None) -> bool:
        """添加論述"""
        debate = Debate.query.get(debate_id)
        if not debate or debate.status != 'ongoing':
            return False
            
        # 檢查是否輪到該用戶發言
        if (debate.current_turn == 'pro' and debate.pro_participant_id != user_id) or \
           (debate.current_turn == 'con' and debate.con_participant_id != user_id):
            return False
            
        argument = Argument(
            debate_id=debate_id,
            user_id=user_id,
            position=debate.current_turn,
            round_number=debate.current_round,
            content=content,
            sources=sources,
            created_at=datetime.utcnow()
        )
        
        db.session.add(argument)
        
        # 更新辯論狀態
        debate.current_turn = 'con' if debate.current_turn == 'pro' else 'pro'
        debate.current_deadline = datetime.utcnow() + timedelta(hours=debate.time_limit_hours)
        
        # 檢查是否需要進入下一輪
        pro_args = Argument.query.filter_by(
            debate_id=debate_id, 
            position='pro', 
            round_number=debate.current_round
        ).count()
        con_args = Argument.query.filter_by(
            debate_id=debate_id, 
            position='con', 
            round_number=debate.current_round
        ).count()
        
        if pro_args > 0 and con_args > 0:
            debate.current_round += 1
            if debate.current_round > 3:  # 限制最多3輪
                debate.status = 'judging'
                
        db.session.commit()
        return True
    
    @staticmethod
    def search_debates(query: str = '', filters: Dict[str, Any] = None, 
                      sort_by: str = 'newest', page: int = 1, per_page: int = 10):
        """搜尋辯論"""
        debates_query = Debate.query
        
        # 搜尋條件
        if query:
            debates_query = debates_query.filter(
                or_(
                    Debate.title.contains(query),
                    Debate.description.contains(query)
                )
            )
        
        # 篩選條件
        if filters:
            if filters.get('status'):
                debates_query = debates_query.filter(Debate.status.in_(filters['status']))
            if filters.get('category'):
                debates_query = debates_query.filter(Debate.category.in_(filters['category']))
                
        # 排序
        if sort_by == 'hot':
            debates_query = debates_query.order_by(desc(Debate.views))
        elif sort_by == 'urgent':
            debates_query = debates_query.filter(
                and_(Debate.status == 'ongoing', Debate.current_deadline.isnot(None))
            ).order_by(Debate.current_deadline)
        else:  # newest
            debates_query = debates_query.order_by(desc(Debate.created_at))
            
        return debates_query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_hot_debates(limit: int = 10) -> List[Debate]:
        """獲取熱門辯論"""
        return Debate.query.order_by(desc(Debate.views)).limit(limit).all()
    
    @staticmethod
    def get_recent_debates(limit: int = 10) -> List[Debate]:
        """獲取最新辯論"""
        return Debate.query.order_by(desc(Debate.created_at)).limit(limit).all()
    
    @staticmethod
    def get_debate_statistics() -> Dict[str, int]:
        """獲取辯論統計"""
        return {
            'waiting': Debate.query.filter_by(status='waiting').count(),
            'ongoing': Debate.query.filter_by(status='ongoing').count(),
            'judging': Debate.query.filter_by(status='judging').count(),
            'completed': Debate.query.filter_by(status='completed').count(),
            'total': Debate.query.count()
        }


class HallService:
    """大廳服務類"""
    
    @staticmethod
    def post_message(user_id: int, content: str, message_type: str = 'general') -> HallMessage:
        """發送大廳訊息"""
        message = HallMessage(
            user_id=user_id,
            content=content,
            message_type=message_type,
            created_at=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    @staticmethod
    def get_recent_messages(limit: int = 20) -> List[HallMessage]:
        """獲取最近的大廳訊息"""
        return HallMessage.query.order_by(desc(HallMessage.created_at)).limit(limit).all()
    
    @staticmethod
    def get_top_debaters(limit: int = 10) -> List[Dict[str, Any]]:
        """獲取頂級辯手"""
        # 這裡返回示例數據，實際應該從用戶統計計算
        return [
            {'username': 'DebateMaster', 'rating': 1850, 'win_rate': 75, 'level': 15},
            {'username': 'LogicKing', 'rating': 1720, 'win_rate': 68, 'level': 12},
            {'username': 'FactChecker', 'rating': 1680, 'win_rate': 72, 'level': 11},
            {'username': 'ReasonSeeker', 'rating': 1620, 'win_rate': 65, 'level': 10},
            {'username': 'WisdomFinder', 'rating': 1580, 'win_rate': 70, 'level': 9}
        ][:limit]