from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.debate import Debate, HallMessage
from sqlalchemy import func, desc, or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首頁"""
    # 獲取熱門辯論（示例數據）
    hot_debates = [
        {
            'id': 1,
            'title': 'AI人工智慧是否會造成大規模失業？',
            'category': '科技議題',
            'participants_count': 128,
            'pro_rate': 45,
            'con_rate': 55,
            'created_days_ago': 2
        },
        {
            'id': 2,
            'title': '台灣應該加速廢核還是延役核電？',
            'category': '環境議題',
            'participants_count': 95,
            'pro_rate': 62,
            'con_rate': 38,
            'created_days_ago': 1
        }
    ]
    
    return render_template('index.html', hot_debates=hot_debates)

@main_bp.route('/debate-board')
def debate_board():
    """辯論看板 - 重新設計的主頁面"""
    # 獲取統計數據
    waiting_count = Debate.query.filter_by(status='waiting').count() or 12
    ongoing_count = Debate.query.filter_by(status='ongoing').count() or 8
    completed_count = Debate.query.filter_by(status='completed').count() or 156
    total_participants = 245  # 示例數據
    
    # 獲取熱門辯論（按觀看數排序）
    hot_debates = Debate.query.order_by(desc(Debate.views)).limit(4).all()
    if not hot_debates:
        # 示例數據
        hot_debates = [
            type('Debate', (), {
                'id': 1, 'title': 'AI是否會取代人類工作？', 'status': 'waiting',
                'views': 156, 'category': '科技', 'pro_participant': None, 'con_participant': None
            }),
            type('Debate', (), {
                'id': 2, 'title': '遠距工作是否比實體辦公更有效率？', 'status': 'ongoing',
                'views': 134, 'category': '社會', 'pro_participant': None, 'con_participant': None
            })
        ]
    
    # 獲取最新辯論
    latest_debates = Debate.query.order_by(desc(Debate.created_at)).limit(6).all()
    if not latest_debates:
        # 示例數據
        latest_debates = [
            type('Debate', (), {
                'id': 3, 'title': '電動車是否真的比燃油車環保？', 'category': '環境',
                'creator': type('User', (), {'username': 'EcoDebater'})
            }),
            type('Debate', (), {
                'id': 4, 'title': '線上教育能否完全取代傳統教育？', 'category': '教育',
                'creator': type('User', (), {'username': 'EduExpert'})
            })
        ]
    
    # 分類統計
    categories = [
        {'name': '科技', 'count': 45},
        {'name': '社會', 'count': 38},
        {'name': '環境', 'count': 29},
        {'name': '政治', 'count': 22},
        {'name': '教育', 'count': 31},
        {'name': '經濟', 'count': 19},
        {'name': '文化', 'count': 12},
        {'name': '健康', 'count': 16}
    ]
    
    return render_template('debate_board.html',
                         waiting_count=waiting_count,
                         ongoing_count=ongoing_count,
                         completed_count=completed_count,
                         total_participants=total_participants,
                         hot_debates=hot_debates,
                         latest_debates=latest_debates,
                         categories=categories)

@main_bp.route('/search')
def search_debates():
    """搜尋辯論頁面"""
    # 獲取搜尋參數
    search_query = request.args.get('q', '').strip()
    selected_filters = {
        'status': request.args.getlist('status'),
        'category': request.args.getlist('category'),
        'level': request.args.get('level', 'all')
    }
    
    # 分頁參數
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_by = request.args.get('sort', 'newest')
    
    # 構建查詢
    query = Debate.query
    
    # 搜尋條件
    if search_query:
        query = query.filter(
            or_(
                Debate.title.contains(search_query),
                Debate.description.contains(search_query)
            )
        )
    
    # 狀態篩選
    if selected_filters['status']:
        query = query.filter(Debate.status.in_(selected_filters['status']))
    
    # 分類篩選
    if selected_filters['category']:
        query = query.filter(Debate.category.in_(selected_filters['category']))
    
    # 排序
    if sort_by == 'hot':
        query = query.order_by(desc(Debate.views))
    elif sort_by == 'urgent':
        query = query.filter(Debate.status == 'ongoing').order_by(Debate.current_deadline)
    else:  # newest
        query = query.order_by(desc(Debate.created_at))
    
    # 分頁
    debates_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    debates = debates_pagination.items
    
    # 為每個辯論添加額外信息
    for debate in debates:
        # 計算緊急狀態
        if debate.status == 'ongoing' and debate.current_deadline:
            remaining = debate.current_deadline - datetime.utcnow()
            debate._is_urgent = remaining.total_seconds() < 6 * 3600
        else:
            debate._is_urgent = False
        
        # 添加統計數據（示例）
        if not hasattr(debate, 'views') or debate.views is None:
            debate.views = 42
        debate._arguments_count = 8
        debate._followers = 15
    
    # 分類統計
    categories = [
        {'name': '科技', 'count': 45},
        {'name': '社會', 'count': 38},
        {'name': '環境', 'count': 29},
        {'name': '政治', 'count': 22},
        {'name': '教育', 'count': 31},
        {'name': '經濟', 'count': 19},
        {'name': '文化', 'count': 12},
        {'name': '健康', 'count': 16}
    ]
    
    return render_template('search_debates.html',
                         debates=debates,
                         categories=categories,
                         selected_filters=selected_filters,
                         search_query=search_query,
                         sort_by=sort_by,
                         current_page=page,
                         total_pages=debates_pagination.pages,
                         total_debates=debates_pagination.total)

@main_bp.route('/create')
def create_debate_page():
    """發起辯論頁面"""
    if not session.get('user_id'):
        flash('請先登入才能發起辯論', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('create_debate.html')

@main_bp.route('/debate/<int:debate_id>')
def debate_detail(debate_id):
    """辯論詳情頁"""
    debate = Debate.query.get_or_404(debate_id)
    
    # 增加觀看次數
    if not debate.views:
        debate.views = 1
    else:
        debate.views += 1
    db.session.commit()
    
    return render_template('debate_detail.html', debate=debate)

@main_bp.route('/debate-hall')
def debate_hall():
    """辯手大廳"""
    # 獲取當前進行的辯論（置頂訊息用）
    current_debates = Debate.query.filter_by(status='ongoing').limit(2).all()
    
    # 獲取辯手排行榜（本月）
    top_debaters = [
        {
            'username': 'DebateMaster',
            'rating': 1850,
            'win_rate': 75,
            'level': 15
        },
        {
            'username': 'LogicKing',
            'rating': 1720,
            'win_rate': 68,
            'level': 12
        },
        {
            'username': 'FactChecker',
            'rating': 1680,
            'win_rate': 72,
            'level': 11
        },
        {
            'username': 'ReasonSeeker',
            'rating': 1620,
            'win_rate': 65,
            'level': 10
        },
        {
            'username': 'WisdomFinder',
            'rating': 1580,
            'win_rate': 70,
            'level': 9
        }
    ]
    
    # 今日統計
    today_stats = {
        'active_debates': Debate.query.filter_by(status='ongoing').count() or 12,
        'completed_today': 8
    }
    
    # 獲取大廳訊息
    hall_messages = HallMessage.query.order_by(desc(HallMessage.created_at)).limit(20).all()
    
    # 即時通知（示例）
    recent_notifications = [
        {
            'icon': 'comments',
            'type': 'info',
            'message': '新的辯論對手向您發起挑戰',
            'time_ago': '5分鐘前'
        },
        {
            'icon': 'trophy',
            'type': 'success',
            'message': '您在科技議題辯論中獲勝',
            'time_ago': '1小時前'
        },
        {
            'icon': 'level-up-alt',
            'type': 'warning',
            'message': '恭喜升級到 Lv.8',
            'time_ago': '2小時前'
        }
    ]
    
    # 獲取當前用戶資訊
    current_user = None
    if session.get('user_id'):
        current_user = User.query.get(session['user_id'])
        if current_user:
            current_user.total_debates = 25  # 示例數據
            current_user.wins = 18
            current_user.rating = 1420
            current_user.level = 8
    
    return render_template('debate_hall.html', 
                         current_debates=current_debates,
                         top_debaters=top_debaters,
                         today_stats=today_stats,
                         hall_messages=hall_messages,
                         recent_notifications=recent_notifications,
                         current_user=current_user)

# AJAX 路由
@main_bp.route('/api/hall-messages')
def get_hall_messages():
    """獲取大廳訊息（AJAX）"""
    messages = HallMessage.query.order_by(desc(HallMessage.created_at)).limit(20).all()
    html = render_template('partials/hall_messages.html', messages=messages)
    return jsonify({'html': html})

@main_bp.route('/api/post-hall-message', methods=['POST'])
def post_hall_message():
    """發送大廳訊息"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': '請先登入'})
    
    message_content = request.form.get('message', '').strip()
    message_type = request.form.get('message_type', 'general')
    
    if not message_content:
        flash('訊息內容不能為空', 'error')
        return redirect(url_for('main.debate_hall'))
    
    # 創建新訊息
    new_message = HallMessage(
        user_id=session['user_id'],
        content=message_content,
        message_type=message_type,
        created_at=datetime.utcnow()
    )
    
    try:
        db.session.add(new_message)
        db.session.commit()
        flash('訊息發送成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash('發送失敗，請稍後再試', 'error')
    
    return redirect(url_for('main.debate_hall'))

@main_bp.route('/api/accept-challenge', methods=['POST'])
def accept_challenge():
    """接受挑戰"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': '請先登入'})
    
    data = request.get_json()
    message_id = data.get('message_id')
    
    # 這裡應該實現接受挑戰的邏輯
    # 1. 找到挑戰訊息
    # 2. 創建新的辯論
    # 3. 設定參與者
    
    return jsonify({
        'success': True,
        'debate_url': url_for('main.debate_detail', debate_id=1)
    })

@main_bp.route('/api/find-random-opponent', methods=['POST'])
def find_random_opponent():
    """隨機配對"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': '請先登入'})
    
    # 實現隨機配對邏輯
    # 1. 在等待配對的用戶中尋找
    # 2. 匹配等級相近的對手
    # 3. 創建辯論
    
    return jsonify({
        'success': False,
        'message': '目前沒有可配對的對手，請稍後再試'
    })

@main_bp.route('/api/join-debate', methods=['POST'])
def join_debate():
    """加入辯論"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': '請先登入'})
    
    data = request.get_json()
    debate_id = data.get('debate_id')
    position = data.get('position')  # 'pro' or 'con'
    
    debate = Debate.query.get(debate_id)
    if not debate:
        return jsonify({'success': False, 'message': '找不到該辯論'})
    
    if debate.status != 'waiting':
        return jsonify({'success': False, 'message': '該辯論不接受新的參與者'})
    
    # 檢查是否已經有該立場的參與者
    if position == 'pro' and debate.pro_participant_id:
        return jsonify({'success': False, 'message': '正方已滿'})
    elif position == 'con' and debate.con_participant_id:
        return jsonify({'success': False, 'message': '反方已滿'})
    
    # 加入辯論
    try:
        if position == 'pro':
            debate.pro_participant_id = session['user_id']
        else:
            debate.con_participant_id = session['user_id']
        
        # 如果雙方都有人，開始辯論
        if debate.pro_participant_id and debate.con_participant_id:
            debate.status = 'ongoing'
            debate.started_at = datetime.utcnow()
            debate.current_deadline = datetime.utcnow() + timedelta(hours=debate.time_limit_hours or 24)
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '操作失敗，請稍後再試'})

@main_bp.route('/api/create-debate', methods=['POST'])
def create_debate():
    """創建辯論"""
    if not session.get('user_id'):
        flash('請先登入', 'error')
        return redirect(url_for('auth.login'))
    
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category')
    position = request.form.get('position')
    time_limit = int(request.form.get('time_limit', 24))
    level_limit = request.form.get('level_limit') or None
    need_sources = bool(request.form.get('need_sources'))
    allow_audience = bool(request.form.get('allow_audience'))
    enable_judging = bool(request.form.get('enable_judging'))
    
    if not title or not category or not position:
        flash('請填寫所有必填項目', 'error')
        return redirect(url_for('main.create_debate_page'))
    
    if len(title) < 10:
        flash('辯論主題至少需要10個字元', 'error')
        return redirect(url_for('main.create_debate_page'))
    
    try:
        new_debate = Debate(
            title=title,
            description=description,
            category=category,
            creator_id=session['user_id'],
            status='waiting',
            time_limit_hours=time_limit,
            level_limit=level_limit,
            need_sources=need_sources,
            allow_audience=allow_audience,
            created_at=datetime.utcnow(),
            views=0
        )
        
        # 設定創建者的立場
        if position == 'pro':
            new_debate.pro_participant_id = session['user_id']
        else:
            new_debate.con_participant_id = session['user_id']
        
        db.session.add(new_debate)
        db.session.commit()
        
        flash('辯論創建成功！等待對手加入', 'success')
        return redirect(url_for('main.debate_detail', debate_id=new_debate.id))
    
    except Exception as e:
        db.session.rollback()
        flash('創建失敗，請稍後再試', 'error')
        return redirect(url_for('main.create_debate_page'))