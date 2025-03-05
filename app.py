from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os, uuid
from werkzeug.utils import secure_filename
from config import Config
from models import db, Post, Comment

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

# Ensure that the uploads folder exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

def allowed_file(filename):
    return (
        "." in filename and 
        filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )

# Function to generate file URLs correctly
def file_url(filename):
    return url_for('static', filename=f'uploads/{filename}', _external=False)

# Register the function as a Jinja2 filter (AFTER creating `app`)
app.jinja_env.filters['file_url'] = file_url


@app.route('/')
def index():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == "POST":
        file = request.files.get("image")
        caption = request.form.get("caption")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_filename))
            new_post = Post(image_filename=unique_filename, caption=caption)
            db.session.add(new_post)
            db.session.commit()
            flash("Post created successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid image file.", "danger")
    return render_template("create.html")


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post)


@app.route('/add_comment/<int:post_id>', methods=["POST"])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)

    username = request.form.get("username") or "Anonymous"
    content = request.form.get("content")
    if content:
        comment = Comment(username=username, content=content, post=post)
        db.session.add(comment)
        db.session.commit()
        flash("Comment added!", "success")
    else:
        flash("Comment cannot be empty.", "danger")
    return redirect(url_for("post_detail", post_id=post_id))


@app.route('/like/<int:post_id>', methods=["POST"])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    flash("Post liked!", "success")
   
    return redirect(request.referrer or url_for("index"))


if __name__ == '__main__':
    app.run(debug=True)
