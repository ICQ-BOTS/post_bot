import sqlite3
import random

database = 'database.sqlite'

def init_db():
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("""
    CREATE table user (
        id integer primary key,
        first_name text,
        last_name text,
        user_id text,
        status text
    );
    """)
    cursor.execute("""
    CREATE table post (
        id integer primary key,
        text_post text,
        status text,
        addtime integer,
        author_id integer,
        is_anon text,
        token text,
        photo text,
        FOREIGN KEY (author_id) REFERENCES user (id)
    );
    """)
    cursor.execute("""
    CREATE table public (
        id integer primary key,
        token text,
        seq_key text,
        chat text
    );
    """)
    cursor.execute("""
    CREATE table admin (
        id integer primary key,
        user_id text,
        public_id text,
        FOREIGN KEY (user_id) REFERENCES user (id),
        FOREIGN KEY (public_id) REFERENCES public (id)
    );
    """)
    cursor.execute("""
    CREATE table string_user (
        id integer primary key,
        user_id text
    );
    """)
    connect.close()

def add_bot(token):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT id FROM public")
    try:
        new_id = str(cursor.fetchall()[-1][0] + 1)
    except:
        new_id = 1
    random_str = "qwertyuiopasdfghjklzxcvbnm123456789"
    seq_key = ""
    for i in range(0,10):
        seq_key += random_str[random.randint(0, 34)]
    cursor.execute("insert into public values ("+str(new_id)+",'"+token+"','"+seq_key+"','chat')")
    connect.commit()
    connect.close()
    return seq_key

def set_public(token,public):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM public WHERE token='"+token+"'")
    public_id = cursor.fetchall()[0][0]
    cursor.execute("UPDATE public SET chat='"+public+"' where id="+str(public_id))
    connect.commit()
    connect.close()

def check_public(token):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM public WHERE token='"+token+"'")
    res = cursor.fetchall()
    connect.close()
    result = {}
    try:
        if res[0]:
            result["not_exist"] = False
            result["seq_key"] = res[0][2]
            result["chat"] = res[0][3]
    except:
        result["not_exist"] = True
    return result

def add_user(user_id,first_name = "",last_name= ""):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT id FROM user")
    try:
        new_id = str(cursor.fetchall()[-1][0] + 1)
    except:
        new_id = 1
    if type(user_id) == str:
        user_id = add_string_user(user_id)
    cursor.execute("insert into user values ("+str(new_id)+",'"+first_name+"','"+last_name+"',"+str(user_id)+",'user')")
    connect.commit()
    connect.close()

def add_string_user(user_id):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT id FROM string_user")
    try:
        new_id = str(cursor.fetchall()[-1][0] + 1)
    except:
        new_id = 1
    cursor.execute("insert into string_user values ("+str(new_id)+",'"+user_id+"')")
    connect.commit()
    connect.close()
    return new_id

def get_string_user(user_id):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM string_user WHERE user_id='" + str(user_id)+"'")
    res = cursor.fetchall()#[0][0]
    connect.commit()
    connect.close()
    try:
        if res[0]:
            return res[0][0]
    except:
        return 0

def check_user(user_id,token=None):
    result = {}
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    if type(user_id) == str:
        user_id = get_string_user(user_id)
    cursor.execute("SELECT * FROM user WHERE user_id=" + str(user_id))
    res = cursor.fetchall()
    if token:
        cursor.execute("SELECT * FROM public WHERE token='"+token+"'")
        public_id = cursor.fetchall()[0][0]
        cursor.execute("SELECT * FROM admin WHERE public_id=" + str(public_id)+" and user_id="+str(user_id))
        admin = cursor.fetchall()
        try:
            if admin[0]:
                result["is_admin"] = True
            else:
                result["is_admin"] = False
        except:
            result["is_admin"] = False
    connect.close()
    try:
        if res[0]:
            result["not_exist"] = False
            result["id"] = res[0][3]
            result["first_name"] = res[0][1]
            result["last_name"] = res[0][2]
    except:
        result["not_exist"] = True
    return result

def add_post(text,addtime,is_anon,user_id,token,photo):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT id FROM post")
    try:
        new_id = str(cursor.fetchall()[-1][0] + 1)
    except:
        new_id = 1
    cursor.execute("SELECT id FROM user")
    author_id = check_user(user_id)["id"]
    cursor.execute("insert into post values ("+str(new_id)+",'"+text+"','non_posted',"+str(addtime)+","+str(author_id)+",'"+is_anon+"','"+token+"','"+photo+"')")
    connect.commit()
    connect.close()
    return new_id
    
def get_post(post_id=None):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    if post_id == None:
        cursor.execute("SELECT * FROM post WHERE status='non_posted'")
    else:
        cursor.execute("SELECT * FROM post WHERE id="+str(post_id))
    posts = cursor.fetchall()
    connect.close()
    if posts:
        post = list(posts[0])
    else:
        return []
    if post[5] == "public":
        info = check_user(post[4])
        post[1] = post[1] + "\n\nАвтор: " + info["first_name"] + " " + info["last_name"]
    return post

def get_post_public(token):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM post WHERE status='non_posted' and token='"+token+"'")
    posts = cursor.fetchall()
    connect.close()
    if posts:
        post = list(posts[0])
    else:
        return []
    if post[5] == "public":
        info = check_user(post[4])
        post[1] = post[1] + "\n\nАвтор: " + info["first_name"] + " " + info["last_name"]
    return post

def add_admin(user_id,token):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    user_id = check_user(user_id)["id"]
    cursor.execute("SELECT * FROM public WHERE token='"+token+"'")
    public_id = cursor.fetchall()[0][0]
    cursor.execute("SELECT id FROM admin")
    try:
        new_id = str(cursor.fetchall()[-1][0] + 1)
    except:
        new_id = 1
    cursor.execute("insert into admin values ("+str(new_id)+","+str(user_id)+","+str(public_id)+")")
    connect.commit()
    connect.close()

def remove_admin(user_id,token):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    user_id = check_user(user_id)["id"]
    cursor.execute("SELECT * FROM public WHERE token='"+token+"'")
    public_id = cursor.fetchall()[0][0]
    cursor.execute("DELETE FROM admin WHERE public_id="+str(public_id)+" and user_id="+str(user_id))
    connect.commit()
    connect.close()

def get_tokens():
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM public")
    publics = cursor.fetchall()
    connect.close()
    tokens = []
    for public in publics:
        tokens.append(public[1])
    return tokens

def update_message(id_post):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("UPDATE post SET status='posted' where id="+str(id_post))
    connect.commit()
    connect.close()

def get_admin(token):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM public WHERE token='"+token+"'")
    public_id = cursor.fetchall()[0][0]
    cursor.execute("SELECT * FROM admin WHERE public_id="+str(public_id))
    admins = cursor.fetchall()
    connect.close()
    result_admins = []
    if admins:
        for admin in admins:
            result_admins.append(admin[1])
    else:
        return []
    return result_admins

def get_db(table):
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM "+table)
    result = cursor.fetchall()
    connect.close()
    return result

if __name__ == '__main__': 
	init_db()