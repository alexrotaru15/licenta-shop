# Acest fișier conține formularele folosite în aplicație

from licenta.models import User, Produs
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, RadioField
from wtforms.validators import ValidationError, DataRequired, Length, Email, EqualTo


# clasa conține formularul afișat pe pagina login, utilizatorul se poate autentifica
# folosind email-ul și parola și are posibilitatea de a rămâne autentificat
# pentru viitoarele sesiuni
class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    parola = PasswordField('Parola', validators=[DataRequired()])
    remember = BooleanField('Ține-ma minte!')
    submit = SubmitField('Autentificare')


# un utilizaotr poate trimite mesaje către serverul aplicației
# utilizând formularul de mai jos prezent în pagina contact
class ContactForm(FlaskForm):
    nume = StringField('Nume complet', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subiect = StringField('Subiect', validators=[DataRequired()])
    continut = TextAreaField('Mesajul tău', validators=[DataRequired()])
    trimite = SubmitField('Trimite mesaj')


# pentru a se înregistra utilizatorul trebuie să completeze formularul
# de înregistrare care conține câmpuri pentru user_name, nume, email,
# parola, confirmarea parolei, adresa și telefon
class RegisterForm(FlaskForm):
    user_name = StringField('Nume utilizator', validators=[DataRequired(), Length(min=1, max=50)])
    nume = StringField('Nume complet', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    parola = PasswordField('Parolă', validators=[DataRequired()])
    confirmare_parola = PasswordField('Confirmare parolă', validators=[DataRequired(), EqualTo('parola')])
    adresa = TextAreaField('Adresa', validators=[DataRequired()])
    telefon = StringField('Telefon', validators=[DataRequired(), Length(min=10, max=10)])
    submit = SubmitField('Înregistrare')

    # verificăm dacă user_name-ul există deja în baza de date și nu permitem
    # înregistrarea unui alt utilizator cu același user_name
    def validate_user_name(self, user_name):
        exista_user = User.query.filter_by(user_name=user_name.data).first()
        if exista_user:
            raise ValidationError('Numele utilizatorului există deja în baza de date, te rugăm să alegi un alt nume de utilizator')

    # verificăm dacă email-ul există deja în baza de date și nu permitem
    # înregistrarea unui alt utilizator cu același email
    def validate_email(self, email):
        exista_user = User.query.filter_by(email=email.data).first()
        if exista_user:
            raise ValidationError('Aceste email există deja în baza de date')


# un utilizator își poate modifica datele introduse în formularul de înregistrare
# inclusiv user_name-ul și emailul, de aceea este necesar să verificăm iar dacă
# acestea există deja în baza de date pentru a putea fi folosite
class UpdateContForm(FlaskForm):
    user_name = StringField('Nume utilizator', validators=[DataRequired(), Length(min=1, max=50)])
    nume = StringField('Nume complet', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    adresa = TextAreaField('Adresa', validators=[DataRequired()])
    telefon = StringField('Telefon', validators=[DataRequired(), Length(min=10, max=10)])
    submit = SubmitField('Modifică')

    def valid_user_name(self, user_name):
        if user_name.data != current_user.user_name:
            exista_user = User.query.filter_by(user_name=user_name.data).first()
            if exista_user:
                raise ValidationError('Numele utilizatorului există deja în baza de date, te rugăm să alegi un alt nume de utilizator')

    def valid_email(self, email):
        if email.data != current_user.email:
            exista_user = User.query.filter_by(email=email.data).first()
            if exista_user:
                raise ValidationError('Aceste email există deja în baza de date')


# formularul este prezent în secțiunea administratorului de introducere a unui nou produs
# nu se poate adăuga un produs nou care are același nume cu un produs existent,
# în acest sens există posibilitatea modificării produsului existent
class AdaugaProdusForm(FlaskForm):
    nume = StringField('Nume produs', validators=[DataRequired()])
    descriere = TextAreaField('Descriere', validators=[DataRequired()])
    poza = FileField('Poza', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    pret = FloatField('Preț', validators=[DataRequired()])
    submit = SubmitField('Adaugă')

    def validate_produs(self, nume):
        exista_produs = Produs.query.filter_by(nume=nume.data).first()
        if exista_produs:
            raise ValidationError('Există deja acest produs!')


# în vederea finalizării comenzii cerem datele de livrare de la utilizator
class ConfirmAdresaForm(FlaskForm):
    nume = StringField('Nume complet', validators=[DataRequired()])
    adresa = TextAreaField('Adresa livrare', validators=[DataRequired()])
    telefon = StringField('Telefon', validators=[DataRequired(), Length(min=10, max=10)])
    mod_plata = RadioField('Selectați modalitatea de plată', choices=[('Ramburs', 'Ramburs'), ('Card', 'Online - cu cardul')])
    submit = SubmitField('Trimite comanda')


# pentru a reseta parola utilizatorul va completa adresa de email
# în formularul următor, dacă adresa de email nu există în baza de date
# se va afișa o eroare
class CereResetareParolaForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Trimite email')

    def valid_email(self, email):
        if email.data != current_user.email:
            exista_user = User.query.filter_by(email=email.data).first()
            if exista_user:
                raise ValidationError('Aceste email există deja în baza de date')


# dupa accesarea link-ului primit pe email, utilizatorul va fi redirecționat
# către pagina de resetare a parolei care conține formularul ResetareParolaForm
class ResetareParolaForm(FlaskForm):
    parola = PasswordField('Parolă', validators=[DataRequired()])
    confirmare_parola = PasswordField('Confirmare parolă', validators=[DataRequired(), EqualTo('parola')])
    submit = SubmitField('Confirmă parola')
