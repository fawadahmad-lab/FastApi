from fastapi import FastAPI , Path ,HTTPException , Query
import json
app=FastAPI()


def load_data():
    with open('patient.json','r') as f:
        data=json.load(f)
    return data

@app.get("/")
def hello():
    return {'message':'hello from fastapi'}


@app.get('/names')
def names():
    return {'name':'Fawad'}

@app.get('/data')
def view():
    data=load_data()
    return data

@app.get('/patient/{patient_id}')
def patient(patient_id:str):
    data=load_data()
    if patient_id in data:
        return data[patient_id]
    return {'error':'patient not found'}


@app.get('/sort')
def sort_patients(sort_by:str=Query(...,description='sort on the basis of Height , Weight , or BMI'), order: str=Query('asc',description='sort in asc or desc order')):
    valid_feilds=['weight','height','bmi']
    if sort_by not in valid_feilds:
        raise HTTPException(status_code=400,detail=f'invalid feild selected from {valid_feilds}')
    data=load_data()
    sorted_order=True if order =='desc' else False
    sorted_data=sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse=sorted_order)
    
    return sorted_data
