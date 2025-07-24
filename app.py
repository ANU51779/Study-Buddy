from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this for production

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///planner.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tasks = db.relationship("Task", backref="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        tasks = Task.query.filter_by(user_id=user.id).all()
        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task.completed])
        progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        return render_template(
            "index.html", tasks=tasks, username=user.username, progress=progress
        )
    else:
        return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return "Username already exists!"
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/add", methods=["GET", "POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        task_name = request.form["task"]
        new_task = Task(name=task_name, user_id=session["user_id"])
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_task.html")


@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session.get("user_id"):
        return "Unauthorized!"
    task.completed = True
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session.get("user_id"):
        return "Unauthorized!"
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/suggest")
def suggest_schedule():
    if "user_id" not in session:
        return redirect(url_for("login"))
    pending_tasks = Task.query.filter_by(
        user_id=session["user_id"], completed=False
    ).all()
    return render_template("suggest.html", pending_tasks=pending_tasks)


if __name__ == "__main__":
    app.run(debug=True)
