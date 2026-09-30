from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import calendar
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_date TEXT UNIQUE NOT NULL,
            day_of_week TEXT,
            category TEXT,
            planned_task TEXT,
            status TEXT DEFAULT '未',
            motivation TEXT DEFAULT '-',
            memo TEXT
        )
    ''')
    
    # 既存のDBテーブルに motivation カラムが無い場合は自動追加
    cursor.execute("PRAGMA table_info(daily_tasks)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'motivation' not in columns:
        cursor.execute("ALTER TABLE daily_tasks ADD COLUMN motivation TEXT DEFAULT '-'")
        
    conn.commit()
    conn.close()

init_db()

WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]

@app.route('/')
def index():
    selected_month = request.args.get('month', '2026-09')
    
    year, month = map(int, selected_month.split('-'))
    _, num_days = calendar.monthrange(year, month)
    
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM daily_tasks WHERE strftime('%Y-%m', task_date) = ?", (selected_month,))
    db_rows = cursor.fetchall()
    
    # カラム名と値のマッピングを辞書型で取得
    cursor.execute("PRAGMA table_info(daily_tasks)")
    col_names = [col[1] for col in cursor.fetchall()]
    
    task_dict = {}
    for row in db_rows:
        row_dict = dict(zip(col_names, row))
        task_dict[row_dict['task_date']] = row_dict
    
    monthly_days = []
    for day in range(1, num_days + 1):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        dt = datetime(year, month, day)
        day_of_week = WEEKDAYS_JA[dt.weekday()]
        
        if date_str in task_dict:
            row = task_dict[date_str]
            monthly_days.append({
                'id': row.get('id'),
                'task_date': row.get('task_date'),
                'day_of_week': row.get('day_of_week'),
                'category': row.get('category') or '',
                'planned_task': row.get('planned_task') or '',
                'status': row.get('status') or '未',
                'motivation': row.get('motivation') or '-',
                'memo': row.get('memo') or ''
            })
        else:
            monthly_days.append({
                'id': None,
                'task_date': date_str,
                'day_of_week': day_of_week,
                'category': '',
                'planned_task': '',
                'status': '未',
                'motivation': '-',
                'memo': ''
            })
            
    # 選択月の前後（前2ヶ月 ＋ 今月 ＋ 後3ヶ月）の計6ヶ月タブを作成
    tab_months = []
    for offset in range(-2, 4):
        m_calc = month + offset
        y_calc = year
        if m_calc < 1:
            m_calc += 12
            y_calc -= 1
        elif m_calc > 12:
            m_calc -= 12
            y_calc += 1
        tab_months.append(f"{y_calc:04d}-{m_calc:02d}")
    
    cursor.execute("SELECT DISTINCT strftime('%Y-%m', task_date) FROM daily_tasks")
    db_months = [r[0] for r in cursor.fetchall() if r[0]]
    
    current_year = datetime.now().year
    end_year = max(2028, current_year + 2)
    
    generated_months = []
    for y in range(2026, end_year + 1):
        for m in range(1, 13):
            generated_months.append(f"{y}-{m:02d}")
            
    all_months = sorted(list(set(db_months + generated_months + tab_months)))
    conn.close()
    
    return render_template('index.html', days=monthly_days, months=all_months, tab_months=tab_months, selected_month=selected_month)

@app.route('/update', methods=['POST'])
def update():
    task_date = request.form.get('task_date')
    day_of_week = request.form.get('day_of_week')
    category = request.form.get('category')
    planned_task = request.form.get('planned_task')
    status = request.form.get('status', '未')
    motivation = request.form.get('motivation', '-')
    memo = request.form.get('memo')
    
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO daily_tasks (task_date, day_of_week, category, planned_task, status, motivation, memo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (task_date, day_of_week, category, planned_task, status, motivation, memo))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('index', month=task_date[:7]))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)