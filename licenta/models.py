# Fișierul conține clasele ale căror instanțe constituie
# tabelele bazei de date
from licenta import database, login_manager, app
from itsdangerous import TimedJSONWebSignatureSerializer
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# clasă pentru tabelul User, conține coloanele definite mai jos ca variabile
# cu constrângerile de unicitatea sau NOT NULL
class User(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    user_name = database.Column(database.String(20), unique=True, nullable=False)
    nume = database.Column(database.String(100), nullable=False)
    email = database.Column(database.String(120), unique=True, nullable=False)
    parola = database.Column(database.String(60), nullable=False)
    adresa = database.Column(database.String(200), nullable=False)
    telefon = database.Column(database.String(11), nullable=False)
    comenzi = database.relationship('Comenzi', backref='utilizator', lazy=True)
    is_admin = database.Column(database.Boolean(), nullable=False, default=False)

    # funcția generează tokenul pentru resetarea parolei
    def reset_token(self, secunde=300):
        s = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'], secunde)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    # funcția verifică dacă tokenul pe care îl captează din link este cel
    # generat de reset_token()
    @staticmethod
    def verif_token(token):
        s = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.user_name}', '{self.nume}, '{self.email}', '{self.adresa}', '{self.telefon}', '{self.comenzi}', '{self.is_admin}')"


class Produs(database.Model):
    # tabelul Produs din baza de date conține informații
    # despre toate produsele din aplicație
    id = database.Column(database.Integer, primary_key=True)
    nume = database.Column(database.String(50), nullable=False, unique=True)
    descriere = database.Column(database.String(200))
    poza = database.Column(database.String(30), nullable=False)
    pret = database.Column(database.Float, nullable=False)
    data_adaugarii = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Produs('{self.id}', '{self.nume}', '{self.descriere}', '{self.poza}', '{self.pret}', '{self.data_adaugarii}')"


class Cos(database.Model):
    # tabel temporar care stochează date despre produsele pe care un utilizator
    # dorește să le comande
    id = database.Column(database.Integer, primary_key=True)
    user = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    produs = database.Column(database.Integer, database.ForeignKey('produs.id'), nullable=False)
    cantitate = database.Column(database.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"Cos('{self.id}', '{self.user}', '{self.produs}', '{self.cantitate}')"


class Comenzi(database.Model):
    # tabelul conține toate comenzile plasate în aplicație
    id = database.Column(database.Integer, primary_key=True)
    user = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    data = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    produse = database.Column(database.String(500), nullable=False)
    date_livrare = database.Column(database.String(200), nullable=False)
    mod_plata = database.Column(database.String(200), nullable=False)
    total = database.Column(database.Float, nullable=False)

    def __repr__(self):
        return f"Comenzi('{self.id}', '{self.data}', '{self.produse}', '{self.user}', '{self.date_livrare}', '{self.mod_plata}', '{self.total}')"


class ProduseComandate(database.Model):
    # am creat acest tabel pentru a avea o evidență a produselor comandate
    # pentru a putea monitoriza produsele cel mai mult sau cel mai puțin
    # comandate, astfel ne putem adapta la nevoile utilizatorilor
    id = database.Column(database.Integer, primary_key=True)
    comanda = database.Column(database.Integer, database.ForeignKey('comenzi.id'), nullable=False)
    produs = database.Column(database.Integer, database.ForeignKey('produs.id'), nullable=False)
    cantitate = database.Column(database.Integer, nullable=False)

    def __repr__(self):
        return f"ProduseComandate('{self.id}', '{self.comanda}', '{self.produs}', '{self.cantitate}')"

    def total_pret(self):
        return self.produs.pret * self.cantitate


class Tranzactii(database.Model):
    # sunt înregistrate tranzacțiile făcute prin aplicație
    id = database.Column(database.Integer, primary_key=True)
    comanda = database.Column(database.Integer, database.ForeignKey('comenzi.id'), nullable=False)
    data = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    total = database.Column(database.Float, nullable=False)

    def __repr__(self):
        return f"Tranzactii('{self.id}', '{self.comanda}', '{self.data}', '{self.total}')"


class MesajeTable(database.Model):
    # conține mesajele trimise de utilizator
    # și primite via email pe adresa server
    id = database.Column(database.Integer, primary_key=True)
    nume = database.Column(database.String(50), nullable=False)
    email = database.Column(database.String(120), nullable=False)
    subiect = database.Column(database.String(120), nullable=False)
    continut = database.Column(database.String(300), nullable=False)
