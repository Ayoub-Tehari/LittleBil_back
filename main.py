from fastapi import FastAPI, HTTPException
import httpx, json


API_MAIL_USERNAME="techtest@gmail.com"
HIBOUTIK_API_KEY="2OZ58K8MYZV56SFA59NG2PQ2HYW4C6280IT"
API_BASE_URL="https://techtest.hiboutik.com/api"

CLIENTS_URL="/customers/search/"
SALES_ITEM_PER_PAGE=5
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/sales/")
async def get_sales_by_customer_id(customer_id: int, page:int):
    if customer_id is None and page is None:
        raise HTTPException(status_code=500, detail="Le numero de page et/ou id client sont requises")
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
            async with httpx.AsyncClient() as client:
                response = await client.get(URL_SALES_LINES, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))
                if response.status_code == 200:
                    res1 = response.json()
                    print(str(response.status_code) + " line number: " + str(line_id))
                    URL = API_BASE_URL + "/sales/" + str(res1[0].get("sale_id", None))
                    response = await client.get(URL, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))
                    if response.status_code == 200:
                        res2_customer_id = response.json()[0].get("customer_id", None)
                        if res2_customer_id is not None and res2_customer_id == customer_id:
                            count_result += 1
                            if count_result >= number_to_begin :
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
async def get_clients_by_name(name: str):
    URL=API_BASE_URL+CLIENTS_URL+"?last_name=" + name
    
    try:
        async with httpx.AsyncClient() as client:
            
            # Effectuer une requête POST à l'API externe avec les données JSON reçues
            response = await client.get(URL, auth=(API_MAIL_USERNAME, HIBOUTIK_API_KEY))

            # Vérifier si la requête a réussi (code 200)
            if response.status_code == 200:
                # Analyser la réponse JSON reçue
                result = response.json()
                return result
            else:
                # Si la requête n'a pas réussi, lever une exception HTTP
                raise HTTPException(status_code=response.status_code, detail="Échec de la soumission des données à l'API externe")

    except httpx.HTTPError as e:
        # En cas d'erreur de communication avec l'API externe, lever une exception HTTP
        raise HTTPException(status_code=500, detail="Erreur de communication avec l'API externe")
