import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

mydb = mysql.connector.connect(
    host= os.getenv("DB_HOST"),
    user= os.getenv("DB_USER"),
    password= os.getenv("DB_PASSWORD"),
    database= os.getenv("DB_DATABASE")
)
global_cursor = mydb.cursor()

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

@app.get('/', status_code=200)
def home():
    return {'message': 'API de projetos pessoais.'}

@app.get('/projects/{project_id}', status_code=200)
def get_one_project(project_id: int):
    try:
        query = "SELECT * FROM projects WHERE id = %s"
        global_cursor.execute(query, (project_id,))
        result = global_cursor.fetchone()
        if result:
            return result
        else:
            raise HTTPException(status_code=404, detail=f"Projeto com id {project_id} não encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/projects', status_code=200)
def get_projects():
    try:
        query = "SELECT * FROM projects"
        global_cursor.execute(query)
        result = global_cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/projects', status_code=201)
async def create_project(project: newProject):
    try:
        query = "INSERT INTO projects (img, title, descript, descript_ptbr, category, tecnologies, url, live_url, download, laptop_img, mobile_img) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (project.img, project.title, project.descript, project.descript_ptbr, project.category, project.tecnologies, project.url, project.live_url, project.download, project.laptop_img, project.mobile_img)
        global_cursor.execute(query, values)
        mydb.commit()
        project_id = global_cursor.lastrowid
        return {'message': 'Projeto criado com sucesso!', 'project_id': project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put('/projects/{project_id}', status_code=200)
def update_project(project: newProject, project_id: int):
        query = "UPDATE projects SET img = %s, title = %s, descript = %s, descript_ptbr = %s, category = %s, tecnologies = %s, url = %s, live_url = %s, download = %s, laptop_img = %s, mobile_img = %s WHERE id = %s"
        values = (
            project.img, project.title, project.descript, project.descript_ptbr, 
            project.category, project.tecnologies, project.url, project.live_url, 
            project.download, project.laptop_img, project.mobile_img, project_id
        )
        global_cursor.execute(query, values)
        mydb.commit()
        return {'message': 'Projeto atualizado com sucesso!'}

@app.delete('/projects/{project_id}', status_code=200)
def delete_project(project_id: int):
        query = 'DELETE FROM projects WHERE id = %s'
        values = (project_id,)
        global_cursor.execute(query, values)
        mydb.commit()
        return {'message': 'Projeto deletado com sucesso!'}

if __name__ == "__main__":
    uvicorn.run(app, port=7777)
