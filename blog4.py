
from ast import keyword
from turtle import clear
from unittest import result
from django.shortcuts import render
from flask import Flask, render_template, flash,redirect,url_for,session,logging,request
from sklearn.cluster import mean_shift
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt #paralonın şifrelenmesini sağlar
import email_validator
from functools import wraps #decorator yapısı için

#kullanıcı giriş decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapın","danger")  #giriş yapılmamısa logine git
            return redirect(url_for("login"))
    return decorated_function

#kullanıcı kayıt formu
class RegisterForm(Form):  #form sınıfından inheritence alan bir register form oluşturuldu.
    name = StringField('İsim Soyisim', validators=[validators.Length(min=4, max=25)]) #girilen değğerin şartları liste halinde doldurudulur validator classı ile
    user_name = StringField('Kullanıcı adı', validators=[validators.Length(min=4, max=35)])
    email = StringField('Email adresi', validators=[validators.Email(message="Lütfen geçerli bir email adresi girin")])
    password= PasswordField('Parola', validators=[validators.DataRequired(message='Lütfen bir parola belirleyiniz'), validators.EqualTo(fieldname="confirm",message="Paralonız uyuşmuyor")])
    confirm = PasswordField("Parola Doğrula")

#giriş yapmak için form
class LoginForm(Form): #login formu oluşturma
    username= StringField("Kullanıcı Adı:")
    password= PasswordField("Parola:")

#makale ekleme formu
class ArticleForm(Form):
    title = StringField("Makale başlığı",validators=[validators.length(min=5,max=100)])
    content = TextAreaField("Makale içeriği",validators=[validators.length(min=5)])

app = Flask(__name__)
app.secret_key="ybblog" #flash mesajo oluşturmak için gerekli

app.config["MYSQL_HOST"] = "localhost" #mysql veritabanıa ulaşmak için gerekli şeyler
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"]="ybblog"

app.config["MYSQL_CURSORCLASS"]= "DictCursor"

mysql = MySQL(app) #obje oluşturduk 
#cursor, mysql veritabanında işlem yapmamıza sağlayarak bu yapyı kullanarak sql sorhgularını çalıştıraniliriz.

@app.route("/")

def index():
    articles = [ {"id":1, "title":"Deneme1", "content":"Deneme1 içerik "},
                {"id":2, "title":"Deneme2", "content":"Deneme2 içerik "},
                {"id":3, "title":"Deneme3", "content":"Deneme3 içerik "}
    ]
    return render_template("index.html", articles = articles)

@app.route("/about")

def about():
    return render_template("about.html")

#@app.route("/article/<string:id>")

#def detail(id):
    #return "Article id:" + id

#def about():
    #return render_template("about.html")

#Makale sayfamızın gösterilmesi
@app.route("/articles")
def articles():  #veritabanından makaleleri çekip göstercez
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu) #hiç makale yoksa result 0 döner, 0'dan büyükse makale vardır
    if result>0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles= articles)
    else:
        return render_template("articles.html")


@app.route("/dashboard")
@login_required         #@ işareti ile flaskteki bir decorator çalıştırmış oluruz , kullanıcı girişimiz varsa dashborarda gidilmeli giriş yapılmamışsa kontrol paneline gidilmez
def dashboard():   #decaorator kulllanıcı grişi kontrol edilmesi gereken heryerde kullanılabilir 
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")


#kayıt olma

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate(): #form validate true ya da false döner form için girilenler uygunsa true dönecek ve anasayfaya redirect yapapcak
        #veritabanınına girilen değişkenlerin yüklenmesi gerek
        name = form.name.data
        user_name =form.user_name.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu= "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,user_name,password))
        mysql.connection.commit()#veritabanında değişiklik yapmak istiyorsak güncelleme ya da silme gibi bu komut çalıştırılır.
        cursor.close()#bunu yapmak gerek 
        flash("Başarıyla kayıt oldunuz", "success")# flash mesajı oluşturuldu bir sonraki requestte bu mesaj gözükecek yani indexe redirect yaptığımızda
        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)

#giriş yapa tıkladığımızda gideceğimiz login işlemi fonksiyonu
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data #formdan bilgileri çekmiş olduk bunları veritabanı sorgusu ile sorgulayalım

        cursor=mysql.connection.cursor()
        sorgu = "Select * From users where username= %s"
        result = cursor.execute(sorgu,(username,)) #böyle bir kullancıı yoksa sıfıt döner
        if result > 0:
            data = cursor.fetchone() #db alınan password ile aynı olup olmadığı kontrol edilir.
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Giriş yapıldı", "success")

                session["logged_in"] = True   #session başlatma işlemi???
                session["username"] = username



                return redirect(url_for("index"))# başarılıysa anasayfaya döner
            else:
                flash("Parolanız yanlış girildi","danger")
                return redirect(url_for("login")) #şifre yanlışsa tekrar logine gider

            
        else:
            flash("Kullanıcı bulunamadı","danger")#result = 0 olma durumu
            return redirect(url_for("login"))
        
    return render_template("login.html",form=form)

#makale detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,)) #result 0 ya da 0'dan büyük
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

#makale sil
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor= mysql.connection.cursor()
    sorgu="Select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    
    if result>0:
        sorgu2="Delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok ya da silme yetkiniz yok","danger")
        return redirect(url_for("index"))

#makale güncelle
@app.route("/edit/<string:id>", methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id=%s and author =%s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:                               #makale olmaması ya da bizim olmaması falan durumları
            flash("Böyle bir makale yok ya da yetkiniz yok","danger")
            return redirect(url_for("index"))#anasayfaya git
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form=form)

    else:#post request kısmı
        form = ArticleForm(request.form)
        newtitle=form.title.data
        newcontent=form.content.data

        sorgu2 = "Update articles Set title = %s,content =%s where id=%s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))
        
#logout işlemi
@app.route("/logout")
def logout():
    session.clear() #çıkış yaptığında session biter
    return redirect(url_for("index"))

#makale ekleme kısmı
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi","success")
        return redirect (url_for("dashboard"))

    return render_template("addarticle.html",form=form)

#arama url
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method =="GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword") #bana bir post request yapıldıysa form gelen bilgiyi get ile alırız inputun name değeri keyword
        cursor = mysql.connection.cursor()
        sorgu= "Select * from articles where title like '%" + keyword + "%'"
        result = cursor.execute(sorgu)
        if result == 0: #bu başlığa uygun makale yok
            flash("Aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles=articles)



if __name__ == "__main__":

    app.run(debug=True)

#|safe html içeriğini normal göstermeye yarar ckeditör html şekilde veritabanına kaydediyordu