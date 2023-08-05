
import httpx, json
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

from fastapi.responses import JSONResponse
from bson import json_util
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

API_MAIL_USERNAME="techtest@gmail.com"
HIBOUTIK_API_KEY="2OZ58K8MYZV56SFA59NG2PQ2HYW4C6280IT"
API_BASE_URL="https://techtest.hiboutik.com/api"
MONGO_DB_PASSWORD = "PTan5kyqG2Lj8ip3"
MONGO_DB_USERNAME = "ayoubtehari01"
MONGO_DB_CLUSTER = "cluster0.igtmo94.mongodb.net"
CLIENTS_URL="/customers/search/"
SALES_ITEM_PER_PAGE=5
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET","POST"],
    allow_headers=["*"],
)


# Secret key to sign the JWT token (Keep this secret and secure!)
SECRET_KEY = "your-secret-key"

# JWT token expiration time (e.g., 30 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Sample user data (Replace this with your user data)
USERS = {
    "testuser": {
        "username": "testuser",
        "password": "password123",
    }
}

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    password: str

# Function to create a JWT token
def create_jwt_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# Function to decode a JWT token
def decode_jwt_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Login endpoint to issue JWT token
@app.post("/login")
def login(user: User):
    if user.username in USERS and user.password == USERS[user.username]["password"]:
        token_data = {"sub": user.username}
        jwt_token = create_jwt_token(token_data)
        return {"access_token": jwt_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Protected endpoint example - requires authentication using JWT token
@app.get("/api/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    user = decode_jwt_token(token)
    return {"message": f"Hello, {user['sub']}"}

@app.get("/")
def root():
    return {"message": "Hello World"}

def fill_db(tab, url, collection) :
    with httpx.Client() as client:
        for i in tab:
            URL_SALES_LINES = url + str(i)
            try:
                print(URL_SALES_LINES)
                response = client.get(URL_SALES_LINES, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))
                if response.status_code == 200:
                    res1 = response.json()
                    #print(res1)
                    if res1 :
                        collection.insert_one(res1[0])
                else:
                    print(response.status_code)
                    i -= 1
                    #break  # Exit the loop on failed request
            except httpx.HTTPError as e:
                print("Erreur de communication avec l'API externe")
    
def mongodb_connect() :
    uri = "mongodb+srv://"+MONGO_DB_USERNAME+":"+MONGO_DB_PASSWORD+"@"+MONGO_DB_CLUSTER+"/?retryWrites=true&w=majority"
    # Create a new client and connect to the server
    client2 = MongoClient(uri, server_api=ServerApi('1'))
    return client2

def create_db () :
    client2 = mongodb_connect()
    try:
        # Ping to confirm a successful connection
        client2.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")

        db = client2['littleBil']

        costumers_collection = db['clients']
        sales_collection = db['ventes']

        fill_db(range(1,12), API_BASE_URL + "/customer/", costumers_collection)
        sale_ids = [12,15,16,18,19,20]
        fill_db(sale_ids, API_BASE_URL + "/sales/", sales_collection)
    except Exception as e:
        print(e)
    finally:
        client2.close()

@app.get("/sales/")
def get_sales_by_customer_id(customer_id: int, page:int):
    
    flag = 1
    line_id = 1
    final_result = []
    max_len = SALES_ITEM_PER_PAGE * page
    count_result = 0
    number_to_begin = max_len - SALES_ITEM_PER_PAGE
    if page < 1 :
        raise HTTPException(status_code=500, detail="Le numero de page doit etre positif")
    while flag:
        URL_SALES_LINES = API_BASE_URL + "/sale_line_item/" + str(line_id)
        try:
            with httpx.Client() as client:
                response = client.get(URL_SALES_LINES, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))
                if response.status_code == 200:
                    res1 = response.json()
                    print(str(response.status_code) + " line number: " + str(line_id))
                    URL = API_BASE_URL + "/sales/" + str(res1[0].get("sale_id", None))
                    response = client.get(URL, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))
                    if response.status_code == 200:
                        res2_customer_id = response.json()[0].get("customer_id", None)
                        if res2_customer_id is not None and res2_customer_id == customer_id:
                            count_result += 1
                            if count_result > number_to_begin :
                                final_result.append(response.json()[0])  # Append JSON content, not the response object
                            if (count_result ==max_len):
                                break

                    else:
                        break  # Exit the loop on failed request

                else:
                    break  # Exit the loop on failed request

        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail="Erreur de communication avec l'API externe")
        line_id += 1

    return final_result

@app.get("/clients/")
def get_clients_by_name(first_name: str="unknown",last_name: str="unknown",email: str="unknown"):
    if first_name =="unknown" and last_name =="unknown" and email =="unknown" :
        raise HTTPException(status_code=500, detail="le \"nom\" est necessaire")
    
    try:
        with httpx.Client() as client:
            result = []
            if last_name != "unknown" :
                URL=API_BASE_URL+CLIENTS_URL+"?last_name=" + last_name
                # Effectuer une requête POST à l'API externe avec les données JSON reçues
                response = client.get(URL, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))

                # Vérifier si la requête a réussi (code 200)
                if response.status_code == 200:
                    # Analyser la réponse JSON reçue
                    result = response.json()
                else:
                    # Si la requête n'a pas réussi, lever une exception HTTP
                    raise HTTPException(status_code=response.status_code, detail="Échec de la soumission des données à l'API externe")
            if first_name != "unknown" :
                URL=API_BASE_URL+CLIENTS_URL+"?first_name=" + first_name
                response = client.get(URL, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))

                # Vérifier si la requête a réussi (code 200)
                if response.status_code == 200:
                    # Analyser la réponse JSON reçue
                    tmp2=response.json()
                    for tmp in tmp2:
                        if tmp not in result:
                            result.append(tmp)
                else:
                    # Si la requête n'a pas réussi, lever une exception HTTP
                    raise HTTPException(status_code=response.status_code, detail="Échec de la soumission des données à l'API externe")
                
            if email != "unknown" :
                URL=API_BASE_URL+CLIENTS_URL+"?email=" + email
                response = client.get(URL, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))

                # Vérifier si la requête a réussi (code 200)
                if response.status_code == 200:
                    # Analyser la réponse JSON reçue
                    tmp2=response.json()
                    for tmp in tmp2:
                        if tmp not in result:
                            result.append(tmp)
                else:
                    # Si la requête n'a pas réussi, lever une exception HTTP
                    raise HTTPException(status_code=response.status_code, detail="Échec de la soumission des données à l'API externe")
                
            return result
            

    except httpx.HTTPError as e:
        # En cas d'erreur de communication avec l'API externe, lever une exception HTTP
        raise HTTPException(status_code=500, detail="Erreur de communication avec l'API externe")

@app.get("/clients_db/")
def get_clients_by_name_db (first_name: str="unknown",last_name: str="unknown",email: str="unknown"):
    if first_name =="unknown" and last_name =="unknown" and email =="unknown" :
        raise HTTPException(status_code=500, detail="le \"nom\" est necessaire")
    client2 = mongodb_connect()
    # Send a ping to confirm a successful connection
    try:
        #client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        
        db = client2['littleBil']

        costumers_collection = db['clients']
        results = costumers_collection.find({
            "$or": [
                {"email": email},
                {"last_name": last_name},
                {"first_name": first_name}
            ]
        })
        
        
        # Convert the MongoDB results to JSON
        sales_list = list(results)
        # Serialize the list using json_util
        json_string = json.dumps(sales_list, default=json_util.default, indent=4)

        client2.close()
        return JSONResponse(content=json_string, headers = {"X-Custom-Header": "Custom Value"}
    )
    except Exception as e:
        print(e)
        client2.close()
    
@app.get("/sales_db/")
def get_sales_by_customer_id_mongodb(customer_id: int):
  
    client2 = mongodb_connect()
    # Send a ping to confirm a successful connection
    try:
        #client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        
        db = client2['littleBil']

        sales_collection = db['ventes']
        results = sales_collection.find({
            "customer_id": customer_id
        })
        # Convert the MongoDB results to JSON
        sales_list = list(results)
        # Serialize the list using json_util
        json_string = json.dumps(sales_list, default=json_util.default, indent=4)

        client2.close()
        return JSONResponse(content=json_string, headers = {"X-Custom-Header": "Custom Value"}
    )
    except Exception as e:
        print(e)
        client2.close()
 
#create_db ()