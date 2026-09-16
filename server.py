from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)

# 配置日志
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

CSV_FILE = 'assets/Data/users.csv'
ARTICLES_DIR = 'assets/files'

def ensure_dir_exists(dir_path):
    """确保目录存在，若不存在则创建"""
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        app.logger.error(f"创建目录失败: {str(e)}")

def ensure_file_exists(file_path):
    """确保文件存在，若不存在则创建"""
    try:
        if not os.path.exists(file_path):
            ensure_dir_exists(os.path.dirname(file_path))
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['username', 'contact', 'contact_type', 'nationality', 'password'])
    except Exception as e:
        app.logger.error(f"创建文件失败: {str(e)}")

# 初始化必要目录和文件
ensure_dir_exists(ARTICLES_DIR)
ensure_file_exists(CSV_FILE)

# API 路由 - 必须在静态文件路由之前定义
@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        'success': True,
        'message': 'Server is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/login', methods=['POST'])
def login():
    app.logger.info('Login attempt received')
    try:
        data = request.get_json()
        app.logger.info(f'Login data: {data}')
        account_type = data.get('accountType')
        account = data.get('account')
        password = data.get('password')
        
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (
                    (account_type == 'username' and row['username'] == account) or
                    (account_type in ['email', 'phone'] and row['contact'] == account and row['contact_type'] == account_type)
                ):
                    if row['password'] == password:
                        app.logger.info(f'Login successful for user: {row["username"]}')
                        return jsonify({
                            'success': True,
                            'username': row['username']
                        })
                    else:
                        app.logger.warning(f'Invalid password for user: {account}')
                        return jsonify({
                            'success': False,
                            'error': 'invalid_password'
                        })
        
        app.logger.warning(f'Account not found: {account}')
        return jsonify({
            'success': False,
            'error': 'account_not_found'
        })
    
    except Exception as e:
        app.logger.error(f'Login error: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': str(e)
        })

@app.route('/register', methods=['POST'])
def register():
    app.logger.info('Registration attempt received')
    try:
        data = request.get_json()
        app.logger.info(f'Registration data: {data}')
        ensure_dir_exists(ARTICLES_DIR)
        
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过表头
            for row in reader:
                if row[0] == data.get('username') or (row[1] == data.get('contact') and row[2] == data.get('contactType')):
                    app.logger.warning(f'Username or contact already registered: {data.get("username")}')
                    return jsonify({
                        'success': False,
                        'message': '用户名或联系方式已被注册'
                    })
        
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([data.get('username'), data.get('contact'), data.get('contactType'), data.get('nationality'), data.get('password')])
        
        app.logger.info(f'Registration successful for user: {data.get("username")}')
        return jsonify({'success': True})
    
    except Exception as e:
        app.logger.error(f'Registration error: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/articles', methods=['GET'])
def get_articles():
    try:
        articles = []
        for username in os.listdir(ARTICLES_DIR):
            user_dir = os.path.join(ARTICLES_DIR, username)
            if os.path.isdir(user_dir):
                for article_file in os.listdir(user_dir):
                    if article_file.endswith('.json'):
                        article_path = os.path.join(user_dir, article_file)
                        with open(article_path, 'r', encoding='utf-8') as f:
                            try:
                                article_data = json.load(f)
                                # 过滤掉已删除的文章
                                if article_data.get('del') != "t":
                                    article_data.update({
                                        'id': f"{username}/{article_file}",
                                        'username': username,
                                        'date': article_file.split('.json')[0],
                                        'views': article_data.get('views', 0),
                                        'likes': article_data.get('likes', []),
                                        'comments': article_data.get('comments', [])
                                    })
                                    articles.append(article_data)
                            except json.JSONDecodeError:
                                continue
        
        articles.sort(key=lambda x: x['date'], reverse=True)
        return jsonify(articles)
    except Exception as e:
        print(f"Error getting articles: {str(e)}")
        return jsonify([])

@app.route('/api/articles', methods=['POST'])
def create_article():
    data = request.get_json()
    username = data.get('username')
    title = data.get('title')
    content = data.get('content')

    article_data = {
        "title": title,
        "content": content,
        "allowLikes": True,
        "allowComments": True,
        "views": 0,
        "likes": [],
        "comments": [],
        "username": username,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "del": "f"  # 添加删除标记字段
    }

    user_dir = os.path.join(ARTICLES_DIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    article_id = f"{datetime.now().strftime('%Y-%m-%d-%H.%M.%S')}.json"
    article_path = os.path.join(user_dir, article_id)

    with open(article_path, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=4)

    return jsonify({'success': True, 'message': '文章已创建'}), 201

@app.route('/api/articles/<path:article_id>/like', methods=['POST'])
def like_article(article_id):
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'message': '缺少用户名'})
    
    article_path = os.path.join(ARTICLES_DIR, article_id)
    
    with open(article_path, 'r', encoding='utf-8') as f:
        article_data = json.load(f)
    
    if username not in article_data['likes']:
        article_data['likes'].append(username)
    else:
        article_data['likes'].remove(username)
    
    with open(article_path, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/articles/<path:article_id>', methods=['GET'])
def get_article(article_id):
    try:
        # 路径安全校验
        if '..' in article_id or article_id.startswith('/'):
            return jsonify({'success': False, 'message': '非法路径'}), 400
            
        article_path = os.path.join(ARTICLES_DIR, article_id)
        
        if not os.path.exists(article_path):
            return jsonify({'success': False, 'message': '文章不存在'}), 404

        with open(article_path, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
            
        return jsonify({
            'success': True,
            'title': article_data.get('title', '无标题'),
            'content': article_data.get('content', ''),
            'username': article_data.get('username', '未知用户'),
            'date': article_data.get('date', '未知时间'),
            'allowComments': article_data.get('allowComments', True),
            'comments': article_data.get('comments', []),
            'del': article_data.get('del', 'f')
        })
    except json.JSONDecodeError:
        return jsonify({'success': False, 'message': '文章数据格式错误'}), 500
    except Exception as e:
        app.logger.error(f"获取文章失败: {str(e)}")
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500


@app.route('/api/articles/<path:article_id>/comments', methods=['POST'])
def add_comment(article_id):
    data = request.get_json()
    username = data.get('username')
    content = data.get('content')
    
    if not all([username, content]):
        return jsonify({'success': False, 'message': '缺少必要参数'})
    
    article_path = os.path.join(ARTICLES_DIR, article_id)
    
    with open(article_path, 'r', encoding='utf-8') as f:
        article_data = json.load(f)
    
    if not article_data.get('allowComments', True):
        return jsonify({'success': False, 'message': '该文章不允许评论'})
    
    comment = {
        'username': username,
        'content': content,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    article_data['comments'].append(comment)
    
    with open(article_path, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/articles/<path:article_id>', methods=['DELETE'])
def delete_article(article_id):
    try:
        # 获取请求数据
        data = request.get_json()
        current_user = data.get('username', '').strip()
        
        # 基础验证
        if not current_user:
            return jsonify({'success': False, 'message': '未提供用户信息'}), 401

        # 加载文章数据
        article_path = os.path.join(ARTICLES_DIR, article_id)
        if not os.path.exists(article_path):
            return jsonify({'success': False, 'message': '文章不存在'}), 404
            
        with open(article_path, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
            
        # 权限验证
        if article_data.get('username', '').strip() != current_user:
            return jsonify({'success': False, 'message': '无操作权限'}), 403

        # 执行删除
        os.remove(article_path)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500
@app.route('/')
def serve_index():
    return send_from_directory('..', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('..', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)