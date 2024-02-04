from fastapi import FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, select

app = FastAPI()

# Adjust the SQL Server connection URL based on your credentials and database information
DATABASE_URL = r"mssql+pyodbc://DESKTOP-G8JOIIS/master?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"

engine = create_engine(DATABASE_URL)
metadata = MetaData()


users = Table(
    "users",
    metadata,
    Column("user_id", Integer, primary_key=True, index=True),
    Column("user_name", String(length=255), unique=True, index=True),
    Column("user_email", String),
    Column("user_password", String),
    Column("user_location", String),
    Column("user_phone", String),
    Column("user_age", Integer),
)

# Create the table in the database
metadata.create_all(bind=engine)

# Pydantic model for user registration
class UserRegistration(BaseModel):
    user_name: str
    user_password: str
    user_email: EmailStr
    user_location: str
    user_phone: str
    user_age: int

# Pydantic model for user login
class UserLogin(BaseModel):
    user_name: str
    user_password: str

# Creating an instance of OAuth2PasswordBearer for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Function to register a user in the database
def register_user(user: UserRegistration):
    conn = engine.connect()
    conn.execute(users.insert().values(
        user_name=user.user_name,
        user_password=user.user_password,
        user_email=user.user_email,
        user_location=user.user_location,
        user_phone=user.user_phone,
        user_age=user.user_age,
    ))
    conn.commit()  # Add this line to commit the changes

# Function to verify user credentials in the database
def verify_user_credentials(user_name: str, user_password: str):
    conn = engine.connect()
    query = select(users.c.user_name, users.c.user_password).where(users.c.user_name == user_name)
    result = conn.execute(query).fetchone()

    if result and result[1] == user_password:
        return True
    return False

# Endpoint for user registration
@app.post("/register")
async def register(user: UserRegistration):
    if verify_user_credentials(user.user_name, user.user_password):
        raise HTTPException(status_code=400, detail="Username already registered")

    register_user(user)
    return {"message": "Registration successful"}

# Endpoint for user login
@app.post("/login")
async def login(user: UserLogin):
    user_name = user.user_name
    user_password = user.user_password

    if not verify_user_credentials(user_name, user_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"message": "Login successful"}
