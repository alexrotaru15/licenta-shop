# Fișierul conține funcțiile folosite pentru toate rutele aplicației.
from flask import url_for, flash, redirect, render_template, request
import os
import secrets
import ast
from PIL import Image
from licenta import app, database, bcrypt, email
from licenta.models import User, Produs, Cos, Comenzi, ProduseComandate, MesajeTable, Tranzactii
from licenta.forms import ContactForm, RegisterForm, LoginForm, UpdateContForm, AdaugaProdusForm, ConfirmAdresaForm, CereResetareParolaForm, ResetareParolaForm
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from sqlalchemy.sql.expression import func

# pagina home este pagina pe care utilizatorul o vede la intrarea în aplicație


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    # utilizatorul are posibilitatea de a alege între 4 opțiuni de filtrare
    # a produselor de pe prima pagină
    optiuni = ['Alfabetic A-Z', 'Alfabetic Z-A',
               'Preț crescător', 'Preț descrescător']
    optiune_final = 'Alfabetic A-Z'
    if request.method == 'POST':
        optiune_final = request.form['optiuni_select']
    selectat = optiune_final
    # produsele sunt ordonate în ordinea preferată de utilizator
    if optiune_final == 'Alfabetic A-Z':
        produse = Produs.query.order_by(Produs.nume.asc()).all()
    elif optiune_final == 'Alfabetic Z-A':
        produse = Produs.query.order_by(Produs.nume.desc()).all()
    elif optiune_final == 'Preț crescător':
        produse = Produs.query.order_by(Produs.pret.asc()).all()
    elif optiune_final == 'Preț descrescător':
        produse = Produs.query.order_by(Produs.pret.desc()).all()
    else:
        produse = Produs.query.order_by(func.random()).all()
    return render_template('acasa.html', title='Acasă', produse=produse, optiuni=optiuni, selectat=selectat)


@app.route('/despre_noi')
def despre_noi():
    return render_template('despre_noi.html', title='Despre noi')


@app.route('/livrare')
def livrare():
    return render_template('livrare.html', title='Cum livrăm?')


@app.route('/producatori')
def producatori():
    return render_template('producatori.html', title='Producători')


# pagina admin este accesibilă doar utilizatorilor care au True
# pe coloana is_admin din tabelul User al bazei de date
@app.route('/admin')
def admin():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return render_template('admin.html', title='Admin')
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


# pagina /admin/users conține evidența utilizatorilor înregistrați în aplicație
# administratorul poate verifica utilizatorii vizitând această pagină
@app.route('/admin/users')
def all_users():
    if current_user.is_admin:
        users = User.query.all()
    else:
        return redirect(url_for('home'))
    return render_template('admin_all_users.html', title='Toți utilizatorii - Admin Only', users=users)


# această pagină este disponibilă doar administratorului
# acesta poate verifica comenzile fiecărui utilizator
@app.route('/admin/users/<int:utilizator>')
def user_comenzi(utilizator):
    if current_user.is_admin:
        comenzi = Comenzi.query.filter_by(user=utilizator).all()
    else:
        return redirect(url_for('home'))
    return render_template('comenzi_user.html', title='Comenzi user', comenzi=comenzi)


# administratorul poate vedea comenzile și individual
# pentru fiecare utilizator
@app.route('/admin/users/<int:utilizator>/comenzi/<int:nr_comanda>')
def user_comenzi_indiv(utilizator, nr_comanda):
    if current_user.is_admin:
        linie = Comenzi.query.filter_by(user=utilizator, id=nr_comanda).first()
        produse = linie.produse
        produse_dict = ast.literal_eval(produse)
    else:
        return redirect(url_for('home'))
    return render_template('comenzi_user_indiv.html', title='Comanda', produse=produse_dict, linie=linie)


# utilizatorii vor avea acces la comenzile finalizate
# se execută o interogare a tabelului Comenzi din baza de date
# și comenzile sunt afișate pe ecran în ordinea trimiterii
@app.route('/users/<int:utilizator>/comenzi')
def user_comenzi_interface(utilizator):
    if current_user.is_authenticated:
        comenzi = Comenzi.query.filter_by(user=utilizator).all()
    else:
        return redirect(url_for('home'))
    return render_template('comenzi_user.html', title='Comenzi user', comenzi=comenzi)


@app.route('/users/<int:utilizator>/comenzi/<int:nr_comanda>')
def user_comenzi_interface_indiv(utilizator, nr_comanda):
    if current_user.is_authenticated:
        linie = Comenzi.query.filter_by(user=utilizator, id=nr_comanda).first()
        if linie:
            produse = linie.produse
            produse_dict = ast.literal_eval(produse)
            return render_template('comenzi_user_indiv.html', title='Comanda', produse=produse_dict, linie=linie)
    return redirect(url_for('home'))


# pentru a salva poza produsului îi vom modifica numele și dimensiunea la 250x250
# modificarea numelui este necesară deoarece putem este posibil să adăugam poze
# care au același nume
def save_poza(poza_form):
    random_string = secrets.token_hex(8)
    _, extensie = os.path.splitext(poza_form.filename)
    nume = random_string + extensie
    picture_cale = os.path.join(app.root_path, 'static/pictures', nume)

    output_mar = (250, 250)
    i = Image.open(poza_form)
    i.thumbnail(output_mar)
    i.save(picture_cale)

    return nume


# administratorul are posibilitatea de a adăuga produse noi direct din aplicație
@app.route('/admin/produs/nou', methods=['POST', 'GET'])
def produs_nou():
    formular = AdaugaProdusForm()
    if current_user.is_admin:
        if formular.validate_on_submit():
            # produsul va fi salvat în baza de date și accesat din pagina home
            picture = save_poza(formular.poza.data)
            produs = Produs(nume=formular.nume.data, descriere=formular.descriere.data,
                            poza=picture, pret=formular.pret.data)
            database.session.add(produs)
            database.session.commit()
            flash('Produsul a fost adăugat cu succes', 'success')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))
    return render_template('admin_produs_nou.html', title='Produs Nou', formular=formular)


# administratorul are posibilitatea de a gestiona produsele existente în aplicație
# aceste pot fi modificate sau șterse
@app.route('/admin/produse')
def all_produse():
    if current_user.is_admin:
        produse = Produs.query.all()
    else:
        return redirect(url_for('home'))
    return render_template('admin_all_produse.html', title='Toate Produsele - Admin Only', produse=produse)


@app.route('/admin/produs/<int:produs_id>/update', methods=['POST', 'GET'])
def produs_modif(produs_id):
    if current_user.is_admin:
        produs = Produs.query.get_or_404(produs_id)
        formular = AdaugaProdusForm()
        # pentru a modifica un produs existent, administratorul va avea la dispozitie un formular
        # definit în fișierul forms.py
        # dacă formularul este completat cu succes atunci produsul va fi modificat în baza de date
        # daca formularul nu este completat atunci vor fi afișate datele existente despre produs
        # din baza de date
        if formular.validate_on_submit():
            if formular.poza.data:
                picture = save_poza(formular.poza.data)
                produs.poza = picture
            produs.nume = formular.nume.data
            produs.descriere = formular.descriere.data
            produs.pret = formular.pret.data
            database.session.commit()
            flash('Produsul a fost modificat cu succes', 'success')
            return redirect(url_for('all_produse'))
        elif request.method == 'GET':
            formular.nume.data = produs.nume
            formular.descriere.data = produs.descriere
            formular.pret.data = produs.pret
    else:
        return redirect(url_for('home'))
    return render_template('admin_produs_modif.html', title='Modifică produsul', produs=produs, formular=formular)


@app.route('/admin/produs/<int:produs_id>/sterge', methods=['POST'])
def produs_sterge(produs_id):
    # funcția caută un produs al cărui id îl primește ca parametru și îl șterge din baza de date
    produs = Produs.query.get_or_404(produs_id)
    database.session.delete(produs)
    database.session.commit()
    flash('Produsul a fost șters cu succes!', 'success')
    return redirect(url_for('home'))


@login_required
@app.route('/produs/<int:produs_id>', methods=['POST', 'GET'])
def produs_indiv(produs_id):
    produs = Produs.query.get_or_404(produs_id)
    return render_template('produs_individual.html', title=produs.nume, produs=produs)


@login_required
@app.route('/adauga_in_cos/<int:produs_id>', methods=['POST', 'GET'])
def adauga_in_cos(produs_id):
    if current_user.is_authenticated:
        produs = Produs.query.get_or_404(produs_id)
        # pentru a adăuga un produs în coș funcția primește ca parametru id-ul produsului respectiv
        if request.method == 'POST':
            # verificăm dacă produsul există deja în coș
            exista_produs = Cos.query.filter_by(
                user=current_user.id, produs=produs.id).first()
            cantitate = request.form['cantitate']
            if exista_produs:
                # daca produsul există deja în coș atunci modificăm doar cantitatea
                noua_cantitate = exista_produs.cantitate + int(cantitate)
                exista_produs.cantitate = noua_cantitate
                database.session.commit()
            else:
                # altfel, adăugăm produsul în coș
                item_cos = Cos(user=current_user.id,
                               produs=produs.id, cantitate=cantitate)
                database.session.add(item_cos)
                database.session.commit()
        flash('Produsul a fost adăugat în coș', 'success')
    return redirect(url_for('home'))


# funcția primește ca parametru id-ul produsului pe care utilizatorul îl va șterge din coș
@login_required
@app.route('/sterge_din_cos/<int:produs_id>')
def sterge_din_cos(produs_id):
    produs = Produs.query.get_or_404(produs_id)
    item_cos = Cos.query.filter_by(produs=produs.id).first()
    database.session.delete(item_cos)
    database.session.commit()
    flash('Produsul a fost șters!', 'success')
    return redirect(url_for('cosul_meu'))


@login_required
@app.route('/cosul_meu', methods=['POST', 'GET'])
def cosul_meu():
    if current_user.is_authenticated:
        produse = Produs.query.join(Cos, Produs.id == Cos.produs).add_columns(
            Produs.id, Produs.nume, Produs.poza, Produs.pret, Cos.cantitate).filter(Cos.user == current_user.id)
        if request.method == 'POST':
            for produs in produse:
                # cantitatea poate fi modificată și direct din coș
                linie_cos = Cos.query.filter_by(
                    user=current_user.id, produs=produs.id).first()
                noua_cantitate = request.form[f'cantitate{produs.id}']
                if linie_cos.cantitate != noua_cantitate:
                    linie_cos.cantitate = noua_cantitate
                    database.session.commit()
            flash('Coșul a fost modificat!', 'success')
        subtotal = 0
        # calculăm suma de plată a produselor din coș
        for produs in produse:
            subtotal = subtotal + (produs.cantitate * produs.pret)
        # dacă suma este mai mare decât 75 atunci prețul transportului este 0
        # în caz contrar, se adaugă încă 15 unități prețului total
        if subtotal >= 75:
            transport = 0
        else:
            transport = 15.0
        total = subtotal + transport
        return render_template('cosul_meu.html', title='Coșul Meu', produse=produse, subtotal=subtotal, transport=transport, total=total)
    else:
        flash(
            'Trebuie să vă autentificați pentru a putea vedea produsele din coș!', 'warning')
        return redirect(url_for('home'))


@login_required
@app.route('/continua_comanda', methods=['POST', 'GET'])
def continua_comanda():
    if current_user.is_authenticated:
        formular = ConfirmAdresaForm()
        if formular.validate_on_submit() and request.method == 'POST':
            # pentru a confirma adresa utilizatorul va completa o instanță a formularului
            # ConfirmAdresaForm definit în fișierul forms.py
            # formularul va avea inițial datele introduse de utilizator la înregistrare
            livrare = formular.nume.data + '<br/>' + \
                formular.adresa.data + '<br/>' + formular.telefon.data
            cos_curent = Produs.query.join(Cos, Produs.id == Cos.produs).add_columns(
                Produs.id, Produs.nume, Produs.poza, Produs.pret, Cos.cantitate).filter(Cos.user == current_user.id)
            subtotal = 0
            produse_comandate = {}
            count = Cos.query.count()
            for linie in cos_curent:
                # variabila produse_comandate de tip dicționar conține toate produsele
                # pe care utilizatorul dorește să le comande
                produse_comandate[count] = [
                    linie.nume, linie.cantitate, linie.pret]
                count += 1
                subtotal = subtotal + (linie.cantitate * linie.pret)
            produse_comandate = str(produse_comandate)
            if subtotal >= 75:
                transport = 0
            else:
                transport = 15.0
            total = subtotal + transport
            mod_plata = formular.mod_plata.data
            # după selectarea modalității de plată creăm o un obiect de tip linie a tabelului Comenzi
            # adăugăm produsul în baza de date și salvăm
            comanda = Comenzi(user=current_user.id, produse=produse_comandate,
                              date_livrare=livrare, mod_plata=mod_plata, total=total)
            database.session.add(comanda)
            database.session.commit()
            # adăugăm comanda și în tabelul Tranzactii
            select_comanda = Comenzi.query.order_by(Comenzi.id.desc()).first()
            tranzactie = Tranzactii(comanda=select_comanda.id, total=total)
            database.session.add(tranzactie)
            database.session.commit()
            for linie in cos_curent:
                produs_comandat = ProduseComandate(
                    comanda=comanda.id, produs=linie.nume, cantitate=linie.cantitate)
                database.session.add(produs_comandat)
            database.session.commit()
            cos = Cos.query.all()
            # trimitem un email atât utilizatorului cât și adresei folosite ca server
            trimite_comanda_email(cos_curent, current_user, subtotal, total)
            for linie_cos in cos:
                database.session.delete(linie_cos)
                database.session.commit()
            flash(
                'Comanda a fost trimisă cu success! Veți primi pe email toate detaliile comenzii!', 'success')
            return redirect(url_for('home'))
        elif request.method == 'GET':
            # dacă formularul de confirmare a adresei nu este completat, acesta va conține datele
            # de înregistrare ale utilizatorului
            formular.nume.data = current_user.nume
            formular.adresa.data = current_user.adresa
            formular.telefon.data = current_user.telefon
        return render_template('continua_comanda.html', title='Continuă comanda', formular=formular)
    else:
        return redirect(url_for('home'))


# trimitem email-ul de finalizare a comenzii atât utilizatorului cât și adresei folosite ca server
def trimite_comanda_email(cos_curent, utilizator, subtotal, total):
    mesaj = Message('Comanda dumneavoastră', sender='legumeromanestionline@gmail.com',
                    recipients=[utilizator.email, 'legumeromanestionline@gmail.com'])
    mesaj.html = render_template(
        'trimite_comanda.html', cos_curent=cos_curent, subtotal=subtotal, total=total)
    mesaj.body = render_template('trimite_comanda.txt')
    email.send(mesaj)


# pagina pentru autentificare
@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    formular = LoginForm()
    if formular.validate_on_submit():
        # verificăm dacă există adresa de email folosită pentru autentificare
        # în baza de date și dacă parola introdusă este aceeași cu parola hash
        # din bază
        exista_user = User.query.filter_by(email=formular.email.data).first()
        if exista_user and bcrypt.check_password_hash(exista_user.parola, formular.parola.data):
            login_user(exista_user, remember=formular.remember.data)
            # dacă în titlu există un argument pentru pagina următoare
            # utilizatorul va fi redirecționat către acea pagină
            # în sens contrar, utilizatorul merge la pagina home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash(
                'Adresa de email nu este înregistrată sau parola este greșită', 'danger')
    return render_template('login.html', title='Login', formular=formular)


@app.route('/cont_nou', methods=['POST', 'GET'])
def cont_nou():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    formular = RegisterForm()
    if formular.validate_on_submit():
        # pentru a înregistra un utilizator în aplicație, acesția vor completa
        # o instanță a clasei RegisterForm
        # parola va fi criptată și obiectul de tip utilizatoru va fi adăugat
        # în baza de date
        hashed_pw = bcrypt.generate_password_hash(
            formular.parola.data).decode('utf-8')
        user = User(user_name=formular.user_name.data, nume=formular.nume.data, email=formular.email.data,
                    parola=hashed_pw, adresa=formular.adresa.data, telefon=formular.telefon.data)
        database.session.add(user)
        database.session.commit()
        flash('Contul a fost creat cu succes! Acum vă puteți autentifica pentru a continua cumpărăturile.', 'success')
        return redirect(url_for('login'))
    return render_template('cont_nou.html', title='Cont nou', formular=formular)


@app.route('/contul_meu', methods=['POST', 'GET'])
@login_required
def contul_meu():
    formular = UpdateContForm()
    # utilizatorii își pot modifica datele contului folosind pagina contul_meu
    # valorile default sunt cele din baza de date
    if formular.validate_on_submit():
        current_user.user_name = formular.user_name.data
        current_user.nume = formular.nume.data
        current_user.email = formular.email.data
        current_user.adresa = formular.adresa.data
        current_user.telefon = formular.telefon.data
        database.session.commit()
        flash('Modificările au fost salvate cu success!', 'success')
        return redirect(url_for('contul_meu'))
    elif request.method == 'GET':
        formular.user_name.data = current_user.user_name
        formular.nume.data = current_user.nume
        formular.email.data = current_user.email
        formular.adresa.data = current_user.adresa
        formular.telefon.data = current_user.telefon
    return render_template('contul_meu.html', title='Contul meu', formular=formular)


# utilizatorii pot trimite și mesaje către server via email
def trimite_mesaj_contact(nume, xemail, subiect, continut):
    mesajx = Message(f'Mesaj de la {xemail}', sender='legumeromanestionline@gmail.com',
                     recipients=['legumeromanestionline@gmail.com'])
    mesajx.html = render_template(
        'trimite_mesaj_contact.html', nume=nume, xemail=xemail, subiect=subiect, continut=continut)
    mesajx.body = render_template('trimite_mesaj_contact.txt')
    email.send(mesajx)


@app.route('/contact', methods=['POST', 'GET'])
def contact():
    formular = ContactForm()
    # utilizatorii pot trimite mesaje folosint pagina contact
    # numele și emailul vor fi adăugate ca default dacă utilizatorul este înregistrat,
    # dar pot trimite mesaje și utilizatorii neînregistrați
    if formular.validate_on_submit():
        mesaj = MesajeTable(nume=formular.nume.data, email=formular.email.data,
                            subiect=formular.subiect.data, continut=formular.continut.data)
        database.session.add(mesaj)
        database.session.commit()
        trimite_mesaj_contact(mesaj.nume, mesaj.email,
                              mesaj.subiect, mesaj.continut)
        flash('Mesajul dumneavoastră a fost înregistrat cu succes!', 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET' and current_user.is_authenticated:
        formular.nume.data = current_user.nume
        formular.email.data = current_user.email
    return render_template('contact.html', title='Contact', formular=formular)


# funcția logout_user din flask_login scoate utilizatorul din cont
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# trimite emailul de resetare a parolei utilizatorului primit ca parametru
def trimite_reset_parola_email(utilizator):
    token = utilizator.reset_token()
    mesaj = Message('Cerere de resetare a parolei',
                    sender='legumeromanestionline@gmail.com', recipients=[utilizator.email])
    mesaj.body = f'''Pentru a putea reseta parola, vă rugăm să accesați următorul link fără a-l altera:
{url_for('reset_parola', token=token, _external=True)}

Dacă nu dumneavoastră ați solicitat schimbarea parolei atunci puteți ignora acest email.
    '''
    email.send(mesaj)


@app.route('/reset_parola', methods=['POST', 'GET'])
def cere_reset():
    # nu pot cere resetarea parolei utilizatorii autentificați
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    formular = CereResetareParolaForm()
    if formular.validate_on_submit():
        caut_user = User.query.filter_by(email=formular.email.data).first()
        trimite_reset_parola_email(caut_user)
        flash('Am trimis detaliile de resetare a parolei pe adresa dumneavoastră de email!', 'success')
        return redirect(url_for('login'))
    return render_template('cere_reset.html', title='Resetare Parolă', formular=formular)


@app.route('/reset_parola/<token>', methods=['POST', 'GET'])
def reset_parola(token):
    # dacă utilizatorul este autentificat, acesta nu poate accesa pagina de resetare a parolei
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    trimit_user = User.verif_token(token)
    # folosim funcția verif_token a clasei User pentru a verifica dacă tokenul primit prin link este valid
    # tokenul nu este valid dacă au trecut 300 secunde sau dacă a fost modificat
    if not trimit_user:
        flash('Link-ul nu este activ! Te rugăm să reîncerci', 'warning')
        return redirect(url_for('cere_reset'))
    formular = ResetareParolaForm()
    if formular.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            formular.parola.data).decode('utf-8')
        trimit_user.parola = hashed_pw
        database.session.commit()
        flash('Parola a fost resetată cu success! Acum vă puteți autentifica!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_parola.html', title='Resetare Parolă', formular=formular)


@app.errorhandler(404)
def eroare_404(eroare):
    return render_template('404.html'), 404


@app.errorhandler(500)
def eroare_500(eroare):
    return render_template('500.html'), 500
