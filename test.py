import os
from orm_lite import Model, StringField, IntegerField, BooleanField, DateTimeField, ForeignKey, db

if os.path.exists("omer.db"):
    os.remove("omer.db")

db("omer.db")

class User(Model):
    name = StringField(nullable=False, unique=True)
    age = IntegerField(default=18)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

class Post(Model):
    title = StringField(nullable=False)
    content = StringField()
    user_id = ForeignKey(User, on_delete="CASCADE")

User.migrate()
Post.migrate()

# Bulk create – now works without NOT NULL error
users = User.bulk_create([
    {"name": "Charlie", "age": 22},
    {"name": "Diana", "age": 28}
])
print(User.all())

db.close()


"""
# app.py
from models import User, Post
from orm_lite import db  # optional, for manual transaction control

# ---------- CREATE ----------
# Single insert
u1 = User(name="Alice", age=25)
u1.save()

# Bulk insert
users = User.bulk_create([
    {"name": "Bob", "age": 30},
    {"name": "Charlie", "age": 22}
])

# ---------- READ (QuerySet) ----------
# All users
all_users = User.all()
print("All users:", all_users)

# Filter with QuerySet
active_users = User.objects.filter(is_active=True).order_by("-age")
print("Active users (ordered):", active_users.all())

# Get single user by any field
alice = User.get(name="Alice")
print("Found:", alice)

# Filter exact
young = User.filter(age=22).all()
print("Age 22:", young)

# ---------- UPDATE ----------
# Update single instance
alice.age = 26
alice.save()

# Bulk update via QuerySet
User.objects.filter(is_active=False).update(is_active=True)

# ---------- DELETE ----------
# Delete single
bob = User.get(name="Bob")
if bob:
    bob.delete()

# Bulk delete (safe – requires filters)
User.objects.filter(age=22).delete()

# ---------- FOREIGN KEY ----------
# Create a post for Alice
post = Post(title="My First Post", content="Hello World", user_id=alice.id)
post.save()

# Get all posts by Alice
alice_posts = Post.objects.filter(user_id=alice.id).all()
print(f"Posts by {alice.name}:", alice_posts)

# ---------- TRANSACTION EXAMPLE ----------
with db.transaction():
    u_new = User(name="TransactionUser", age=99)
    u_new.save()
    # If any error occurs here, all changes roll back

# Close the connection when done (optional, usually auto-closed on exit)
db.close()
"""