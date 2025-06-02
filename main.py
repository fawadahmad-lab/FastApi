from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
import json
from typing import Annotated, Literal,Optional
from pydantic import BaseModel, Field, computed_field

app = FastAPI()


# ------------------ Utility Functions ------------------
def load_data():
    with open('patient.json', 'r') as f:
        data = json.load(f)
    return data


def save_data(data):
    with open('patient.json', 'w') as f:
        json.dump(data, f, indent=4)


# ------------------ Pydantic Model ------------------
class Patient(BaseModel):
    id: Annotated[str, Field(..., description='ID of a patient', examples=['poo1'])]
    name: Annotated[str, Field(..., description='Name of the patient', examples=['Umer'])]
    city: Annotated[str, Field(..., description='City of a patient', examples=['Islamabad'])]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of a patient', examples=['24'])]
    gender: Annotated[Literal['Male', 'Female'], Field(..., description='Gender of a patient', examples=['Male'])]
    height: Annotated[float, Field(..., gt=0, description='Height of a patient in meters', examples=['1.75'])]
    weight: Annotated[float, Field(..., gt=0, description='Weight of a patient in kilograms', examples=['78'])]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "under weight"
        elif self.bmi < 25:
            return "normal"
        elif self.bmi < 30:
            return "overweight"
        else:
            return "obese"


# ------------------ Routes ------------------

@app.get("/")
def hello():
    return {'message': 'Hello from FastAPI'}


@app.get('/names')
def names():
    return {'name': 'Fawad'}


@app.get('/data')
def view():
    data = load_data()
    return data


@app.get('/patient/{patient_id}')
def patient(patient_id: str):
    data = load_data()
    if patient_id in data:
        # reconstruct into Patient model to compute BMI and verdict
        patient_obj = Patient(id=patient_id, **data[patient_id])
        return patient_obj.model_dump() | {"bmi": patient_obj.bmi, "verdict": patient_obj.verdict}
    raise HTTPException(status_code=404, detail="Patient not found")


@app.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description='Sort on the basis of weight, height, or bmi'),
    order: str = Query('asc', description='Sort order: asc or desc')
):
    valid_fields = ['weight', 'height', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'Invalid field. Choose from {valid_fields}')

    data = load_data()
    patient_objs = [Patient(id=pid, **details) for pid, details in data.items()]
    reverse = order == 'desc'

    sorted_objs = sorted(patient_objs, key=lambda p: getattr(p, sort_by), reverse=reverse)

    return [
        p.model_dump() | {"bmi": p.bmi, "verdict": p.verdict}
        for p in sorted_objs
    ]

@app.post("/create")
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient already exists')

    # Convert cm to meters if height > 3 (heuristic)
    if patient.height > 3:
        patient.height = round(patient.height / 100, 3)

    # Save only necessary fields
    data[patient.id] = patient.model_dump(exclude={"id"})

    save_data(data)
    return JSONResponse(status_code=202, content={'message': 'Patient created successfully'})




# ----------  Patient update Pydantic model ------------- #
class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default='None')]
    city: Annotated[Optional[str], Field(default='None')]
    age: Annotated[Optional[int], Field(default='None')]
    gender: Annotated[Optional[Literal['Male','Female']], Field(default='None')]
    height: Annotated[Optional[float], Field(default='None',gt=0)]
    weight: Annotated[Optional[float], Field(default='None',gt=0)]


@app.put('/edit/{patient_id}')
def update_patient(patient_id:str,patient_update:PatientUpdate):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail='patient id not found')
    existing_patient_info=data[patient_id]
    updated_patient_info=patient_update.model_dump(exclude_unset=True)
    for key,value in updated_patient_info.items():
        existing_patient_info[key]=value
    existing_patient_info['id']=patient_id
    patient_pydantic_object=Patient(**existing_patient_info)
    existing_patient_info=patient_pydantic_object.model_dump(exclude='id')
    data[patient_id]=existing_patient_info
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'patient updated'})


@app.delete('/delete/{patient_id}')
def delete_data(patient_id:str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=400,detail={'patient not found'})
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'patient deleted'})
