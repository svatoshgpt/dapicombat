from flask import Flask, render_template_string, jsonify, request
from flask_sqlalchemy import SQLAlchemy 
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clicks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

with app.app_context():
   db.create_all()
   if not User.query.first():
       user = User()
       db.session.add(user)
       db.session.commit()

HTML = '''
<!DOCTYPE html>
<html>
<head>
   <title>DAPICOMBAT</title>
   <style>
       body{background:linear-gradient(180deg,#FFA500 0%,#FFD700 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:Arial,sans-serif;color:#333;position:relative;padding-bottom:60px}h1{font-size:48px;margin-bottom:20px;color:#333}.description{font-size:18px;text-align:center;margin-bottom:40px;color:#333}.stats{font-size:18px;color:#333;margin-bottom:20px;background-color:rgba(255,255,255,0.2);padding:10px 20px;border-radius:8px}.click-area{width:260px;height:260px;background-color:#806600;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;cursor:pointer;margin-bottom:40px;position:relative;padding-top:20px}.cat-image{width:200px;height:200px;border-radius:4px;object-fit:cover}.score{color:white;font-size:32px;font-weight:bold;position:absolute;bottom:10px;left:50%;transform:translateX(-50%)}.buttons{display:flex;gap:20px;margin-bottom:60px}.shop-btn{background-color:#1a1a1a;color:white;padding:12px 24px;border-radius:5px;text-decoration:none;border:none;cursor:pointer;font-size:16px;transition:background-color .2s}.shop-btn:hover{background-color:#333}.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000}.modal-content{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;padding:20px;border-radius:8px;width:300px;padding-bottom:60px}.modal-header{display:flex;justify-content:space-between;margin-bottom:20px;color:#333}.modal-header>div{display:flex;flex-direction:column;gap:5px}.modal-header h2{margin:0}.close{cursor:pointer;font-size:24px;color:#333}.upgrade-btn{display:flex;align-items:center;gap:10px;padding:8px;background-color:#1a1a1a;color:white;border-radius:5px;border:none;cursor:pointer;width:100%;margin-bottom:10px;transition:background-color .2s}.upgrade-btn:hover:not(:disabled){background-color:#333}.upgrade-btn:disabled{opacity:.5;cursor:not-allowed}.skins-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}.skin-preview{width:40px;height:40px;object-fit:cover;border-radius:4px}.owned-skin{background-color:#4CAF50}.section-title{margin:20px 0 10px;color:#333;font-size:18px}.modal-bottom-buttons{position:absolute;bottom:0;left:0;right:0;display:flex}.modal-bottom-btn{flex:1;padding:15px;border:none;background:#E31E24;color:white;font-size:16px;text-decoration:none;text-align:center}
   </style>
</head>
<body>
   <h1>DAPICOMBAT</h1>
   <div class="description">
       DAPICOMBAT - это кликер с котиком Дапи! А это просто WEB версия в браузере.
   </div>

   <div class="stats">
       <div>Энергия: <span id="energy">100</span>/<span id="maxEnergy">100</span></div>
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

       fetch('/get_data')
           .then(response => response.json())
           .then(data => {
               userData = data;
               updateUI();
           });

       function updateUI() {
           document.getElementById('score').textContent = userData.score;
           document.getElementById('clickScore').textContent = userData.score;
           document.getElementById('energy').textContent = userData.energy;
           document.getElementById('maxEnergy').textContent = userData.max_energy;
           document.getElementById('multiplier').textContent = userData.multiplier;
           document.getElementById('shopCoins').textContent = userData.score;
           document.getElementById('energyBtn').textContent = `Увеличить энергию (${userData.energyUpgradeCost} кликов)`;
           document.getElementById('multiplierBtn').textContent = `Улучшить множитель (${userData.multiplierUpgradeCost} кликов)`;
           document.querySelector('.cat-image').src = '/static/' + userData.currentSkin;
           
           document.getElementById('multiplierBtn').disabled = userData.score < userData.multiplierUpgradeCost;
           document.getElementById('energyBtn').disabled = userData.score < userData.energyUpgradeCost;
           updateSkinButtons();
       }

       function updateSkinButtons() {
           ['skin1', 'skin2', 'skin3', 'skin4', 'skin5'].forEach(skin => {
               const btn = document.getElementById(skin + 'Btn');
               const skinFileName = skin + '.jpg';
               
               if (userData.ownedSkins.includes(skinFileName)) {
                   btn.classList.add('owned-skin');
                   if (userData.currentSkin === skinFileName) {
                       btn.innerHTML = `
                           <img src="/static/${skinFileName}" class="skin-preview">
                           Выбран
                       `;
                       btn.disabled = true;
                   } else {
                       btn.innerHTML = `
                           <img src="/static/${skinFileName}" class="skin-preview">
                           Выбрать
                       `;
                       btn.disabled = false;
                   }
               } else {
                   if (userData.score >= 50) {
                       btn.disabled = false;
                   } else {
                       btn.disabled = true;
                   }
                   btn.innerHTML = `
                       <img src="/static/${skinFileName}" class="skin-preview">
                       Скин (50)
                   `;
                   btn.classList.remove('owned-skin');
               }
           });

           const defaultBtn = document.getElementById('defaultSkinBtn');
           defaultBtn.disabled = userData.currentSkin === 'dapi.jpg';
       }

       function buySkin(skinName) {
           const skinFileName = skinName + '.jpg';
           
           if (userData.ownedSkins.includes(skinFileName)) {
               userData.currentSkin = skinFileName;
           } else if (userData.score >= 50) {
               userData.score -= 50;
               if (!Array.isArray(userData.ownedSkins)) {
                   userData.ownedSkins = userData.ownedSkins.split(',');
               }
               userData.ownedSkins.push(skinFileName);
               userData.currentSkin = skinFileName;
           }
           
           updateUI();
           
           fetch('/save_data', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json'
               },
               body: JSON.stringify({
                   ...userData,
                   ownedSkins: Array.isArray(userData.ownedSkins) ? userData.ownedSkins : userData.ownedSkins.split(',')
               })
           });
       }

       function setDefaultSkin() {
           userData.currentSkin = 'dapi.jpg';
           updateUI();
           
           fetch('/save_data', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json'
               },
               body: JSON.stringify(userData)
           });
       }

       function incrementScore() {
           if (userData.energy > 0) {
               userData.score += userData.multiplier;
               userData.energy -= 1;
               updateUI();
               
               fetch('/increment', {
                   method: 'POST',
                   headers: {
                       'Content-Type': 'application/json'
                   },
                   body: JSON.stringify(userData)
               });
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
           fetch('/save_data', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json'
               },
               body: JSON.stringify(userData)
           });
       }

       function openShop() {
           document.getElementById('shopModal').style.display = 'block';
           document.getElementById('shopCoins').textContent = userData.score;
           updateSkinButtons();
       }

       function closeShop() {
           document.getElementById('shopModal').style.display = 'none';
       }

       window.onclick = function(event) {
           let modal = document.getElementById('shopModal');
           if (event.target == modal) {
               modal.style.display = 'none';
           }
       }

       setInterval(() => {
           if (userData.energy < userData.max_energy) {
               userData.energy = Math.min(userData.max_energy, userData.energy + 2);
               updateUI();
               fetch('/save_data', {
                   method: 'POST',
                   headers: {
                       'Content-Type': 'application/json'
                   },
                   body: JSON.stringify(userData)
               });
           }
       }, 1000);
   </script>
</body>
</html>
'''

@app.route('/')
def home():
   return render_template_string(HTML)

@app.route('/get_data')
def get_data():
    user = User.query.first()
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
    user = User.query.first()
    user.clicks += user.multiplier
    user.energy -= 1
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/get_data')
def get_data():
    user = User.query.first()
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

@app.route('/save_data', methods=['POST'])
def save_data():
    data = request.get_json()
    user = User.query.first()
    user.clicks = data['score']
    user.energy = data['energy']
    user.max_energy = data['max_energy']
    user.multiplier = data['multiplier']
    user.current_skin = data['currentSkin']
    user.owned_skins = ','.join(data['ownedSkins']) if isinstance(data['ownedSkins'], list) else data['ownedSkins']
    user.energy_upgrade_cost = data.get('energyUpgradeCost', 200)
    user.multiplier_upgrade_cost = data.get('multiplierUpgradeCost', 100)
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)