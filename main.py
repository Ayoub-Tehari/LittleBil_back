from fastapi import FastAPI, HTTPException
import httpx, json
from fastapi.middleware.cors import CORSMiddleware
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

import motor.motor_asyncio
#import pymongo

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
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    await create_db()
    return {"message": "Hello World"}

async def fill_db(tab, url, client, collection) :
    for i in tab:
        URL_SALES_LINES = url + str(i)
        try:
            print(URL_SALES_LINES)
            response = await client.get(URL_SALES_LINES, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))
            if response.status_code == 200:
                res1 = response.json()
                #print(res1)
                if res1 :
                    await collection.insert_one(res1[0])
            else:
                print(response.status_code)
                i -= 1
                #break  # Exit the loop on failed request
        except httpx.HTTPError as e:
            print("Erreur de communication avec l'API externe")

async def create_db () :
    uri = "mongodb+srv://"+MONGO_DB_USERNAME+":"+MONGO_DB_PASSWORD+"@"+MONGO_DB_CLUSTER+"/?retryWrites=true&w=majority"
    # Create a new client and connect to the server
    client2 =  MongoClient(uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    try:
        #client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        
        db = client2['littleBil']

        costumers_collection = db['clients']
        sales_collection = db['ventes']
 
        with httpx.AsyncClient() as client:
            #await fill_db(range(1,12), API_BASE_URL + "/customer/", client, costumers_collection)
            sale_ids = [12,15,16,18,19,20]
            await fill_db(sale_ids, API_BASE_URL + "/sales/", client, sales_collection)
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
