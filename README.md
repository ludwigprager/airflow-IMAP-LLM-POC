# git

# Prerequisites
- docker compose
- imap account. Preferably an unprotected account in your network because that's what I used. Using gmail and imap is another story. I managed to use it but it's not easy due to the new oauth2 requirements.
- A [runpod](https://runpod.io?ref=xf50meqh) endpoint. I used
    - worker configuration: 4090 / 24 GB GPU $0.00031/s, max workers: 3
    - Container image: runpod/worker-v1-vllm:v1.7.0stable-cuda12.1.0
    - Model: openchat/openchat-3.6-8b-20240522
Create an API-KEY and set it in the .env variable
If you want to do me a favour, use this [referral](https://runpod.io?ref=xf50meqh)


## Get the code

```
git clone https://github.com/ludwigprager/airflow-IMAP-LLM-POC.git
```

## Add Credentials (1)


```
cp .env-example .env
```
and edit the variables in `.env` according to the endpoints in runpod.

## Start Airflow
```
./start.sh
```
Open airflow at http://localhost:6789/ 
The default credentials are: account: `airflow`, password: `airflow`

## Add Credentials (2)
Create an 'airflow connection' to set the imap credentials.
In my case it is:
```
./airflow.sh  connections add --conn-type=imap --conn-host=imap.gx --conn-login=ludwig.prager@mydomain.de --conn-password=1234 --conn-port=143    --conn-extra='{"use_ssl": false}' imap_g1_lp
```
The connection-id `imap_g1_lp` is referenced somewhere in the DAG-code.
