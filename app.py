from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('db address')
db = client.dbsparta


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]}, {"_id": False})
        all_users = list(db.users.find({}, {'_id': False}))
        videos = list(db.videos.find({}, {'_id': False}))

        return render_template('index.html', user_info=user_info, all_user=all_users, videos=videos)
    except jwt.ExpiredSignatureError:
        # 로그인 시간이 만료
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 존재 X
        return redirect(url_for("login"))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "id": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "nickname": nickname_receive,                           # 프로필 이름 기본값은 아이디
                                        # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup_id', methods=['POST'])
def check_dup_id():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"id": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/check_dup_nick', methods=['POST'])
def check_dup_nick():
    nickname_receive = request.form['nickname_give']
    exists = bool(db.users.find_one({"nickname": nickname_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        url_receive = request.form["url_give"]
        emoticon_receive = request.form["emoticon_give"]
        comment_receive = request.form["comment_give"]
        embed = 'https://www.youtube.com/embed/' + url_receive.split('=')[1]

        if embed.find('&') != -1:
            embed = 'https://www.youtube.com/embed/' + embed.split('&')[0]


        doc = {
            "id": user_info["id"],
            "nickname":user_info["nickname"],
            "embed": embed,
            "emoticon":emoticon_receive,
            "comment":comment_receive
        }
        db.videos.insert_one(doc)
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/commenting', methods=['POST'])
def commenting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]

        doc = {
            "id": user_info["id"],
            "nickname": user_info["nickname"],
            "comment": comment_receive,
            "date": date_receive
        }
        db.comments.insert_one(doc)
        return jsonify({"result": "success", 'msg': '댓글 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("writing"))


# @app.route("/writing", methods=['GET'])
# def get_comments():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         comments = list(db.comments.find({}).sort("date", -1).limit(20))
#         for comment in comments:
#             comment["_id"] = str(comment["_id"])
#
#             comment["count_heart"] = db.likes.count_documents({"post_id": comment["_id"], "type": "heart"})
#             comment["heart_by_me"] = bool(
#                 db.likes.find_one({"post_id": comment["_id"], "type": "heart", "id": payload['id']}))
#         return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "comments": comments} )
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 좋아요 수 변경
#         user_info = db.users.find_one({"id": payload["id"]})
#
#         post_id_receive = request.form["post_id_give"]
#         action_receive = request.form["action_give"]
#
#         doc = {
#             "post_id": post_id_receive,
#             "id": user_info["id"],
#         }
#         if action_receive == "like":
#             db.likes.insert_one(doc)
#         else:
#             db.likes.delete_one(doc)
#         count = db.likes.count_documents({"post_id": post_id_receive})
#         return jsonify({"result": "success", 'msg': 'updated', "count": count})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


@app.route('/writing')
def write():
    user_info = list(db.comments.find({}))

    for user in user_info:
        time = user['date'].replace('T', ' ')
        time = time.replace('Z', '')
        user['now'] = time.split('.')[0]

    return render_template('write.html', user_info=user_info)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
