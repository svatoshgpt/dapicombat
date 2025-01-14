from flask import Flask, render_template_string, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.root_path, "instance", "clicks.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 1800,
}

instance_path = os.path.join(app.root_path, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clicks = db.Column(db.Integer, default=0)
    energy = db.Column(db.Integer, default=100)
    max_energy = db.Column(db.Integer, default=100)
    multiplier = db.Column(db.Integer, default=1)
    current_skin = db.Column(db.String, default='dapi.jpg')
    owned_skins = db.Column(db.String, default='dapi.jpg')
    energy_upgrade_cost = db.Column(db.Integer, default=200)
    multiplier_upgrade_cost = db.Column(db.Integer, default=100)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

def get_user():
    return User.query.first()

def update_user_energy(user, current_time):
    if user.energy < user.max_energy:
        time_diff = (current_time - user.last_seen).total_seconds()
        energy_regen = int(time_diff / 0.5)
        if energy_regen > 0:
            user.energy = min(user.max_energy, user.energy + energy_regen)
            user.last_seen = current_time
            return True
    return False

with app.app_context():
    db.create_all()
    user = get_user()
    if not user:
        user = User()
        db.session.add(user)
        db.session.commit()

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>DAPICOMBAT</title>
    <style>
        body{background:linear-gradient(180deg,#FFA500 0%,#FFD700 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:Arial,sans-serif;color:#333;position:relative;padding-bottom:60px}h1{font-size:48px;margin-bottom:20px;color:#333}.description{font-size:18px;text-align:center;margin-bottom:40px;color:#333}.stats{font-size:18px;color:#333;margin-bottom:20px;background-color:rgba(255,255,255,0.2);padding:10px 20px;border-radius:8px}.click-area{width:260px;height:260px;background-color:#806600;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;cursor:pointer;margin-bottom:40px;position:relative;padding-top:20px}.cat-image{width:200px;height:200px;border-radius:4px;object-fit:cover}.score{color:white;font-size:32px;font-weight:bold;position:absolute;bottom:10px;left:50%;transform:translateX(-50%)}.buttons{display:flex;gap:20px;margin-bottom:60px}.shop-btn{background-color:#1a1a1a;color:white;padding:12px 24px;border-radius:5px;text-decoration:none;border:none;cursor:pointer;font-size:16px;transition:background-color .2s}.shop-btn:hover{background-color:#333}.energy-bar{width:200px;height:20px;background-color:#ddd;border-radius:10px;overflow:hidden;margin:10px 0}.energy-fill{height:100%;background:linear-gradient(90deg,#ff0000 0%,#ffff00 100%);transition:width .3s ease-in-out}.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000}.modal-content{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;padding:20px;border-radius:8px;width:300px;padding-bottom:60px}.modal-header{display:flex;justify-content:space-between;margin-bottom:20px;color:#333}.modal-header>div{display:flex;flex-direction:column;gap:5px}.modal-header h2{margin:0}.close{cursor:pointer;font-size:24px;color:#333}.upgrade-btn{display:flex;align-items:center;gap:10px;padding:8px;background-color:#1a1a1a;color:white;border-radius:5px;border:none;cursor:pointer;width:100%;margin-bottom:10px;transition:background-color .2s}.upgrade-btn:hover:not(:disabled){background-color:#333}.upgrade-btn:disabled{opacity:.5;cursor:not-allowed}.skins-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}.skin-preview{width:40px;height:40px;object-fit:cover;border-radius:4px}.owned-skin{background-color:#4CAF50}.section-title{margin:20px 0 10px;color:#333;font-size:18px}.modal-bottom-buttons{position:absolute;bottom:0;left:0;right:0;display:flex}.modal-bottom-btn{flex:1;padding:15px;border:none;background:#E31E24;color:white;font-size:16px;text-decoration:none;text-align:center}
    </style>
</head>
<body>
    <h1>DAPICOMBAT</h1>
    <div class="description">
        DAPICOMBAT - это кликер с котиком Дапи! А это просто WEB версия в браузере.
    </div>

    <div class="stats">
        <div>Энергия: <span id="energy">100</span>/<span id="maxEnergy">100</span></div>
        <div class="energy-bar">
            <div class="energy-fill" id="energyFill"></div>
        </div>
        <div>Множитель: x<span id="multiplier">1</span></div>
        <div>Монеты: <span id="score">0</span></div>
    </div>
    
    <div class="click-area" onclick="incrementScore()">
        <img src="/static/dapi.jpg" class="cat-image">
        <div class="score" id="clickScore">0</div>
    </div>
    
    <div class="buttons">
        <button onclick="openShop()" class="shop-btn">Магазин</button>
    </div>

    <div id="shopModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h2>Магазин</h2>
                    <div>Монеты: <span id="shopCoins">0</span></div>
                </div>
                <span class="close" onclick="closeShop()">&times;</span>
            </div>
            
            <h3 class="section-title">Скины</h3>
            <div class="skins-grid">
                <button onclick="buySkin('skin1')" class="upgrade-btn" id="skin1Btn">
                    <img src="/static/skin1.jpg" class="skin-preview">
                    Скин (50)
                </button>
                <button onclick="buySkin('skin2')" class="upgrade-btn" id="skin2Btn">
                    <img src="/static/skin2.jpg" class="skin-preview">
                    Скин (50)
                </button>
                <button onclick="buySkin('skin3')" class="upgrade-btn" id="skin3Btn">
                    <img src="/static/skin3.jpg" class="skin-preview">
                    Скин (50)
                </button>
                <button onclick="buySkin('skin4')" class="upgrade-btn" id="skin4Btn">
                    <img src="/static/skin4.jpg" class="skin-preview">
                    Скин (50)
                </button>
                <button onclick="buySkin('skin5')" class="upgrade-btn" id="skin5Btn">
                    <img src="/static/skin5.jpg" class="skin-preview">
                    Скин (50)
                </button>
            </div>
            <button onclick="setDefaultSkin()" class="upgrade-btn" id="defaultSkinBtn">
                <img src="/static/dapi.jpg" class="skin-preview">
                Стандартный скин
            </button>

            <h3 class="section-title">Улучшения</h3>
            <button onclick="buyUpgrade('multiplier')" class="upgrade-btn" id="multiplierBtn">
                Улучшить множитель (200 кликов)
            </button>
            <button onclick="buyUpgrade('energy')" class="upgrade-btn" id="energyBtn">
                Увеличить энергию (200 кликов)
            </button>

            <div class="modal-bottom-buttons">
                <a href="https://t.me/dapiccombat" class="modal-bottom-btn">наш телеграмм</a>
            </div>
        </div>
    </div>

    <script>
        let userData = {
            score: 0,
            energy: 100,
            max_energy: 100,
            multiplier: 1,
            currentSkin: 'dapi.jpg',
            ownedSkins: ['dapi.jpg'],
            energyUpgradeCost: 200,
            multiplierUpgradeCost: 100
        };

        let updateTimer = null;

        function debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }

        function fetchData() {
            return fetch('/get_data')
                .then(response => response.json())
                .then(data => {
                    userData = data;
                    updateUI();
                })
                .catch(error => console.error('Error fetching data:', error));
        }

        const debouncedUpdateLastSeen = debounce(updateLastSeen, 1000);

        function updateLastSeen() {
            return fetch('/update_last_seen', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            }).catch(error => console.error('Error updating last seen:', error));
        }

        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                fetchData();
            }
            debouncedUpdateLastSeen();
        });

        window.addEventListener('load', debouncedUpdateLastSeen);
        window.addEventListener('beforeunload', updateLastSeen);

        if (updateTimer) clearInterval(updateTimer);
        updateTimer = setInterval(debouncedUpdateLastSeen, 30000);

        fetchData();

        function updateUI() {
            const elements = {
                score: document.getElementById('score'),
                clickScore: document.getElementById('clickScore'),
                energy: document.getElementById('energy'),
                maxEnergy: document.getElementById('maxEnergy'),
                multiplier: document.getElementById('multiplier'),
                shopCoins: document.getElementById('shopCoins'),
                energyBtn: document.getElementById('energyBtn'),
                multiplierBtn: document.getElementById('multiplierBtn'),
                catImage: document.querySelector('.cat-image'),
                energyFill: document.getElementById('energyFill')
            };

            elements.score.textContent = userData.score;
            elements.clickScore.textContent = userData.score;
            elements.energy.textContent = userData.energy;
            elements.maxEnergy.textContent = userData.max_energy;
            elements.multiplier.textContent = userData.multiplier;
            elements.shopCoins.textContent = userData.score;
            elements.energyBtn.textContent = `Увеличить энергию (${userData.energyUpgradeCost} кликов)`;
            elements.multiplierBtn.textContent = `Улучшить множитель (${userData.multiplierUpgradeCost} кликов)`;
            elements.catImage.src = '/static/' + userData.currentSkin;
            
            const energyPercentage = (userData.energy / userData.max_energy) * 100;
            elements.energyFill.style.width = `${energyPercentage}%`;
            
            elements.multiplierBtn.disabled = userData.score < userData.multiplierUpgradeCost;
            elements.energyBtn.disabled = userData.score < userData.energyUpgradeCost;
            
            updateSkinButtons();
        }

        function updateSkinButtons() {
            const skins = ['skin1', 'skin2', 'skin3', 'skin4', 'skin5'];
            skins.forEach(skin => {
                const btn = document.getElementById(skin + 'Btn');
                const skinFileName = skin + '.jpg';
                
                if (!btn) return;
                
                if (userData.ownedSkins.includes(skinFileName)) {
                    btn.classList.add('owned-skin');
                    if (userData.currentSkin === skinFileName) {
                        btn.innerHTML = `<img src="/static/${skinFileName}" class="skin-preview">Выбран`;
                        btn.disabled = true;
                    } else {
                        btn.innerHTML = `<img src="/static/${skinFileName}" class="skin-preview">Выбрать`;
                        btn.disabled = false;
                    }
                } else {
                    btn.disabled = userData.score < 50;
                    btn.innerHTML = `<img src="/static/${skinFileName}" class="skin-preview">Скин (50)`;
                    btn.classList.remove('owned-skin');
                }
            });

            const defaultBtn = document.getElementById('defaultSkinBtn');
            if (defaultBtn) {
                defaultBtn.disabled = userData.currentSkin === 'dapi.jpg';
            }
        }

        const saveData = debounce((data) => {
            return fetch('/save_data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).catch(error => console.error('Error saving data:', error));
        }, 500);

        function buySkin(skinName) {
            const skinFileName = skinName + '.jpg';
            
            if (userData.ownedSkins.includes(skinFileName)) {
                userData.currentSkin = skinFileName;
            } else if (userData.score >= 50) {
                userData.score -= 50;
                if (!Array.isArray(userData.ownedSkins))
                if (!Array.isArray(userData.ownedSkins)) {
                    userData.ownedSkins = userData.ownedSkins.split(',');
                }
                userData.ownedSkins.push(skinFileName);
                userData.currentSkin = skinFileName;
            }
            
            updateUI();
            saveData({
                ...userData,
                ownedSkins: Array.isArray(userData.ownedSkins) ? userData.ownedSkins : userData.ownedSkins.split(',')
            });
        }

        function setDefaultSkin() {
            userData.currentSkin = 'dapi.jpg';
            updateUI();
            saveData(userData);
        }

        let lastIncrementTime = 0;
        const CLICK_DELAY = 50;

        function incrementScore() {
            const now = Date.now();
            if (now - lastIncrementTime < CLICK_DELAY) return;
            lastIncrementTime = now;

            if (userData.energy > 0) {
                userData.score += userData.multiplier;
                userData.energy -= 1;
                updateUI();
                
                fetch('/increment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(userData)
                }).catch(error => console.error('Error incrementing score:', error));
            }
        }

        function buyUpgrade(type) {
            if (type === 'multiplier' && userData.score >= userData.multiplierUpgradeCost) {
                userData.score -= userData.multiplierUpgradeCost;
                userData.multiplier += 1;
                userData.multiplierUpgradeCost *= 2;
            } else if (type === 'energy' && userData.score >= userData.energyUpgradeCost) {
                userData.score -= userData.energyUpgradeCost;
                userData.max_energy += 50;
                userData.energy = Math.min(userData.energy + 50, userData.max_energy);
                userData.energyUpgradeCost *= 2;
            }
            
            updateUI();
            saveData(userData);
        }

        function openShop() {
            const modal = document.getElementById('shopModal');
            if (modal) {
                modal.style.display = 'block';
                document.getElementById('shopCoins').textContent = userData.score;
                updateSkinButtons();
            }
        }

        function closeShop() {
            const modal = document.getElementById('shopModal');
            if (modal) {
                modal.style.display = 'none';
            }
        }

        window.onclick = function(event) {
            const modal = document.getElementById('shopModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    user = get_user()
    current_time = datetime.utcnow()
    update_user_energy(user, current_time)
    db.session.commit()
    return render_template_string(HTML)

@app.route('/update_last_seen', methods=['POST'])
def update_last_seen():
    user = get_user()
    user.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/get_data')
def get_data():
    user = get_user()
    current_time = datetime.utcnow()
    update_user_energy(user, current_time)
    db.session.commit()
    
    return jsonify({
        'score': user.clicks,
        'energy': user.energy,
        'max_energy': user.max_energy,
        'multiplier': user.multiplier,
        'currentSkin': user.current_skin,
        'ownedSkins': user.owned_skins.split(','),
        'energyUpgradeCost': user.energy_upgrade_cost,
        'multiplierUpgradeCost': user.multiplier_upgrade_cost
    })

@app.route('/increment', methods=['POST'])
def increment():
    user = get_user()
    user.clicks += user.multiplier
    user.energy -= 1
    user.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/save_data', methods=['POST'])
def save_data():
    data = request.get_json()
    user = get_user()
    user.clicks = data['score']
    user.energy = data['energy']
    user.max_energy = data['max_energy']
    user.multiplier = data['multiplier']
    user.current_skin = data['currentSkin']
    user.owned_skins = ','.join(data['ownedSkins']) if isinstance(data['ownedSkins'], list) else data['ownedSkins']
    user.energy_upgrade_cost = data.get('energyUpgradeCost', 200)
    user.multiplier_upgrade_cost = data.get('multiplierUpgradeCost', 100)
    user.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
