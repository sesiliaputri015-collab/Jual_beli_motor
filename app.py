from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'replace-with-secure-key'
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'motortrade.db')

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS motors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    brand TEXT,
                    year INTEGER,
                    price REAL,
                    description TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    motor_id INTEGER,
                    buyer_name TEXT,
                    phone TEXT,
                    address TEXT,
                    price_paid REAL,
                    purchased_at TEXT,
                    FOREIGN KEY(motor_id) REFERENCES motors(id)
                 )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, title, brand, year, price FROM motors ORDER BY id DESC")
    motors = c.fetchall()
    conn.close()
    return render_template('index.html', motors=motors)

@app.route('/motor/<int:motor_id>')
def motor_detail(motor_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM motors WHERE id = ?", (motor_id,))
    m = c.fetchone()
    conn.close()
    if not m:
        flash('Motor tidak ditemukan.')
        return redirect(url_for('index'))
    return render_template('motor_detail.html', motor=m)

@app.route('/add', methods=['GET','POST'])
def add_motor():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        brand = request.form.get('brand','').strip()
        year = request.form.get('year') or None
        price = request.form.get('price') or None
        description = request.form.get('description','').strip()
        if not title or not price:
            flash('Nama dan harga wajib diisi.')
            return redirect(url_for('add_motor'))
        try:
            year = int(year) if year else None
            price = float(price)
        except ValueError:
            flash('Format tahun atau harga tidak valid.')
            return redirect(url_for('add_motor'))
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO motors (title, brand, year, price, description) VALUES (?, ?, ?, ?, ?)",
                  (title, brand, year, price, description))
        conn.commit()
        conn.close()
        flash('Motor berhasil ditambahkan.')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/buy/<int:motor_id>', methods=['GET','POST'])
def buy_motor(motor_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, title, price FROM motors WHERE id = ?", (motor_id,))
    motor = c.fetchone()
    if not motor:
        conn.close()
        flash('Motor tidak ditemukan.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        buyer = request.form.get('buyer','').strip()
        phone = request.form.get('phone','').strip()
        address = request.form.get('address','').strip()
        price_paid = request.form.get('price_paid') or motor[2]
        try:
            price_paid = float(price_paid)
        except ValueError:
            flash('Harga bayar tidak valid.')
            return redirect(url_for('buy_motor', motor_id=motor_id))
        purchased_at = datetime.utcnow().isoformat(timespec='seconds')
        c.execute("INSERT INTO purchases (motor_id, buyer_name, phone, address, price_paid, purchased_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (motor_id, buyer, phone, address, price_paid, purchased_at))
        conn.commit()
        conn.close()
        flash('Pembelian tercatat. Terima kasih!')
        return redirect(url_for('index'))
    conn.close()
    return render_template('buy.html', motor=motor)

@app.route('/purchases')
def purchases():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT p.id, m.title, p.buyer_name, p.price_paid, p.purchased_at
                 FROM purchases p JOIN motors m ON p.motor_id = m.id ORDER BY p.purchased_at DESC''')
    rows = c.fetchall()
    conn.close()
    return render_template('purchases.html', rows=rows)

if __name__ == '__main__':
    with app.app_context():
        init_db()
        # Insert sample data if empty
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM motors")
        if c.fetchone()[0] == 0:
            sample = [
                ('Honda CB150R', 'Honda', 2019, 30000000, 'Motor sport 150cc, kondisi baik.'),
                ('Yamaha NMAX', 'Yamaha', 2020, 25000000, 'Skutik nyaman, irit bahan bakar.'),
                ('Suzuki Satria', 'Suzuki', 2018, 18000000, 'Bebek cepat, perawatan mudah.'),
            ]
            c.executemany("INSERT INTO motors (title, brand, year, price, description) VALUES (?, ?, ?, ?, ?)", sample)
            conn.commit()
        conn.close()
    app.run(host='0.0.0.0', port=5000, debug=True)
