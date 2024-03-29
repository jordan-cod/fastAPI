import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("JWT_SECRETKEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))

# Função para obter conexão com o banco de dados usando um context manager
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )

class newProject(BaseModel):
    img: str
    title: str
    descript: str
    descript_ptbr: str
    category: str
    tecnologies: str
    live_url: str
    url: str
    download: str
    laptop_img: str
    mobile_img: str

class Project(BaseModel):
    id: int
    img: str
    title: str
    descript: str
    descript_ptbr: str
    category: str
    tecnologies: str
    live_url: str
    url: str
    download: str
    laptop_img: str
    mobile_img: str

class User(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Função para obter usuário do banco de dados
def get_user(username: str, db: mysql.connector.connection.MySQLConnection):
    query = "SELECT * FROM users WHERE username = %s"
    cursor = db.cursor()
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    return user

# Função para criar token de acesso
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função para verificar token
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@app.post("/register", status_code=201)
def register_user(user: User):
    try:
        db = get_db_connection()
        existing_user = get_user(user.username, db)
        if existing_user:
            db.close()
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_password = pwd_context.hash(user.password)

        insert_query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        insert_values = (user.username, user.email, hashed_password)
        cursor = db.cursor()
        cursor.execute(insert_query, insert_values)
        db.commit()
        db.close()

        return {"message": "User registered successfully"}
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login", status_code=200)
def login_user(user: User):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (user.username,))
        db_user = cursor.fetchone()
        
        cursor.close()
        db.close()

        if db_user and verify_password(user.password, db_user[2]):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": db_user[1]}, expires_delta=access_token_expires)

            # Decodifica o token para obter a data de expiração
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            expiration_datetime = datetime.fromtimestamp(payload["exp"])

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expiration": expiration_datetime,
                "user": user.username
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/', status_code=200)
def home():
    return {'message': 'API de projetos pessoais.'}

@app.get('/', status_code=200)
def home():
    return {'message': 'API de projetos pessoais.'}

@app.get('/projects/{project_id}', response_model=Project, status_code=200)
def get_one_project(project_id: int):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = "SELECT * FROM projects WHERE id = %s"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()
        
        cursor.close()
        db.close()

        if result:
            project_obj = Project(
                id=result[0],
                img=str(result[1]),
                title=str(result[2]),
                descript=str(result[3]),
                descript_ptbr=str(result[4]),
                url=str(result[5]),
                download=str(result[6]),
                tecnologies=str(result[7]),
                live_url=str(result[8]),
                laptop_img=str(result[9]),
                mobile_img=str(result[10]),
                category=str(result[11])
            )
            return project_obj
        else:
            raise HTTPException(status_code=404, detail=f"Projeto com id {project_id} não encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/projects', status_code=200, response_model=list[Project])
def get_projects():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = "SELECT * FROM projects"
        cursor.execute(query)
        results = cursor.fetchall()

        projects_list = []
        for row in results:
            project_dict = {
                "id": row[0],
                "img": str(row[1]),
                "title": str(row[2]),
                "descript": str(row[3]),
                "descript_ptbr": str(row[4]),
                "url": str(row[5]),
                "download": str(row[6]),
                "tecnologies": str(row[7]),
                "live_url": str(row[8]),
                "mobile_img": str(row[9]),
                "laptop_img": str(row[10]),
                "category": str(row[11])
            }
            projects_list.append(project_dict)

        return projects_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.post('/projects', status_code=201)
async def create_project(project: newProject, dict = Depends(verify_token)):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = "INSERT INTO projects (img, title, descript, descript_ptbr, category, tecnologies, url, live_url, download, laptop_img, mobile_img) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (project.img, project.title, project.descript, project.descript_ptbr, project.category, project.tecnologies, project.url, project.live_url, project.download, project.laptop_img, project.mobile_img)
        cursor.execute(query, values)
        db.commit()
        project_id = cursor.lastrowid
        
        return {'message': 'Projeto criado com sucesso!', 'project_id': project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.put('/projects/{project_id}', status_code=200)
def update_project(project: newProject, project_id: int, dict = Depends(verify_token)):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = "UPDATE projects SET img = %s, title = %s, descript = %s, descript_ptbr = %s, category = %s, tecnologies = %s, url = %s, live_url = %s, download = %s, laptop_img = %s, mobile_img = %s WHERE id = %s"
        values = (
            project.img, project.title, project.descript, project.descript_ptbr, 
            project.category, project.tecnologies, project.url, project.live_url, 
            project.download, project.laptop_img, project.mobile_img, project_id
        )
        cursor.execute(query, values)
        db.commit()
        
        return {'message': 'Projeto atualizado com sucesso!'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.delete('/projects/{project_id}', status_code=200)
def delete_project(project_id: int, dict = Depends(verify_token)):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = 'DELETE FROM projects WHERE id = %s'
        values = (project_id,)
        cursor.execute(query, values)
        db.commit()
        
        return {'message': 'Projeto deletado com sucesso!'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, port=7777)
