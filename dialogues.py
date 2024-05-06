import sqlite3
from openai import OpenAI

client = OpenAI(
        api_key='sk-your_api_key'
)

def connect_to_database(database_name):
    return sqlite3.connect(database_name)

def create_dialogues_table(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS dialogues (
                    num INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT,
                    content TEXT
                    )''')

    if cur.execute('''SELECT COUNT(*) FROM dialogues''').fetchone()[0] == 0:
        cur.execute('''INSERT INTO dialogues (role, content) VALUES (?, ?)''',
            ('system', '你是一位有用的助手。回答問題使用正體中文，勿使用簡體字'))

def insert_data(cur, response=None):
    if response is None:
        msg = input('user： ')
        
        if msg != 'quit':
            cur.execute('''INSERT INTO dialogues (role, content) VALUES (?, ?)''', ('user', msg))

        return msg

    else:
        print('assistant： ' + response)

        cur.execute('''INSERT INTO dialogues (role, content) VALUES (?, ?)''', ('assistant', response))

def retrieve_dialogues(cur):
    total_records = cur.execute('''SELECT COUNT(*) FROM dialogues''').fetchone()[0]

    if total_records > 7:

        # 超過11筆清理資料庫
        if total_records > 11:
            keep_first_and_last(cur)

        # 擷取第一筆資料
        cur.execute('''SELECT * FROM dialogues LIMIT 1''')
        first_row = cur.fetchone()
        dialogues = [{'role': first_row[1], 'content': first_row[2]}]

        # 擷取最後七筆資料
        cur.execute('''SELECT * FROM dialogues ORDER BY num DESC LIMIT 7''')
        last_seven_rows = cur.fetchall()[::-1]  # 將資料反向，使最後一筆資料在列表的第一個位置

        for row in last_seven_rows:
            dialogues.append({'role': row[1], 'content': row[2]})

    else:
        # 直接取出所有資料
        cur.execute('''SELECT * FROM dialogues ORDER BY num''')
        dialogues = [{'role': row[1], 'content': row[2]} for row in cur.fetchall()]

    return dialogues

def openai_chat(dialogues):
    completion = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = dialogues
    )
    response = completion.choices[0].message.content

    return response

def keep_first_and_last(cur):

    # 擷取第一筆資料的 ID
    cur.execute('''SELECT num FROM dialogues LIMIT 1''')
    first_row_id = cur.fetchone()[0]

    # 擷取最後七筆資料的 ID
    cur.execute('''SELECT num FROM dialogues ORDER BY num DESC LIMIT 7''')
    last_seven_ids = [row[0] for row in cur.fetchall()]

    # 刪除除了第一筆和最後七筆資料以外的所有資料
    cur.execute('''DELETE FROM dialogues WHERE num NOT IN (?, ?, ?, ?, ?, ?, ?, ?)''', (first_row_id, *last_seven_ids))

def main():    
    database_name = 'dialogues.db'
    conn = connect_to_database(database_name)
    cur = conn.cursor()
    create_dialogues_table(conn)

    while True:

        question = insert_data(cur)
        dialogues = retrieve_dialogues(cur)

        if question == 'quit':
            
            # for dialogue in dialogues:
            #     line = f"{dialogue['role']}: {dialogue['content']}"
            #     print(line)
            
            break

        response = openai_chat(dialogues)
        insert_data(cur, response)

    conn.commit()
    cur.close()
    conn.close()
        

if __name__ == "__main__":
    main()