from pydantic import BaseModel
class User(BaseModel):
    patient_name:str
    gender:str
    dob:str
    policy_number:str
    phone:str
    pan:str

user_db:User = User(
    patient_name='Akash Yadav',
    gender='M',
    dob='26-09-2002',
    policy_number='12hfds3ew3334',
    phone='9876543210',
    pan='BKJP2109H'
)

