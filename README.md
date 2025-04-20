![Logo](https://github.com/MohamedAhmed412000/NextGen-Bank/blob/main/NextGenLogo.jpg)


# NextGen Bank API

An example for simulating bank functionalities using DRF



## Project Architecture

![System Architecture](https://github.com/MohamedAhmed412000/NextGen-Bank/blob/main/System%20Architecture.png)


## Run Locally

1. Clone the project

```bash
  git clone https://github.com/MohamedAhmed412000/NextGen-Bank.git
```

2. Install dependencies and start all components

```bash
  docker compose -f local.yml up --build -d --remove-orphans
```

or if you have [makefile](https://opensource.com/article/18/8/what-how-makefile) installed just run

```bash
  make build
```


## Environment Variables

To run this project, you will need to add the following environment variables to your .env.local file in the .envs directory

| Key       | Type     | Description                        |
| :-------- | :------- | :--------------------------------- |
| `DEBUG`   | `boolean`| **Required**. Django debug flag    |
| `SITE_NAME` | `string` | **Required**. The site name      |
| `ADMIN_URL` | `string` | **Required**. Django admin panel URL path |
| `EMAIL_HOST` | `string` | **Required**. The SMTP server host |
| `EMAIL_PORT` | `number` | **Required**. The SMTP server port |
| `DEFAULT_FROM_EMAIL` | `string` | **Required**. The default sender email |
| `ADMIN_EMAIL` | `string` | **Required**. The admin sender email |
| `DOMAIN` | `string` | **Required**. The domain for the Django server |
| `POSTGRES_HOST` | `string` | **Required**. The postgres database host |
| `POSTGRES_PORT` | `number` | **Required**. The postgres database port |
| `POSTGRES_DB` | `string` | **Required**. The postgres database name |
| `POSTGRES_USER` | `string` | **Required**. The postgres database user |
| `POSTGRES_PASSWORD` | `string` | **Required**. The postgres database user password |
| `BANK_NAME` | `string` | **Required**. The bank name |
| `CELERY_FLOWER_USER` | `string` | **Required**. The celery flower portal default user |
| `CELERY_FLOWER_PASSWORD` | `string` | **Required**. The celery flower portal default password |
| `CELERY_BROKER_URL` | `string` | **Required**. The celery broker url |
| `CELERY_RESULT_BACKEND` | `string` | **Required**. The celery backend server |
| `CLOUDINARY_API_KEY` | `string` | **Required**. The cloudinary api-key |
| `CLOUDINARY_API_SECRET` | `string` | **Required**. The cloudinary api-secret |
| `CLOUDINARY_CLOUD_NAME` | `string` | **Required**. The cloudinary cloud name |
| `COOKIES_SECURE` | `boolean` | Optional. To make cookies passed in https connection only |
| `SIGNING_KEY` | `string` | **Required**. The key to sign jwt token included in the cookies |
| `BANK_CODE` | `number` | **Required**. The external bank code number |
| `BANK_BRANCH_CODE` | `number` | **Required**. The internal bank code number in the country |
| `CURRENCY_CODE_EGP` | `number` | **Required**. The egyptian pound currency code |
| `CURRENCY_CODE_SAR` | `number` | **Required**.The saudi riyal currency code |
| `CURRENCY_CODE_USD` | `number` | **Required**.The USA dollar currency code |
| `CURRENCY_CODE_EUR` | `number` | **Required**.The european euro currency code |
| `BANK_CARD_PREFIX` | `number` | **Required**. The country prefix for card numbering generation |
| `BANK_CARD_CODE` | `number` | **Required**. The bank prefix for card numbering generation |
| `CVV_SECRET_KEY` | `string` | **Required**. The key used to generate the last checksom digit in the card |
| `BANK_CODE` | `number` | **Required**. The internal bank code number in the country |
| `LARGE_TRANSACTION_THRESHOLD` | `number` | **Required**. The max amount to be transfered in one time window |
| `FREQUENT_TRANSACTION_THRESHOLD` | `number` | **Required**. The max number of transactions in one time window |
| `TIME_WINDOW_HOURS` | `number` | **Required**. The duration of one time window in hours |





## Access the swagger

#### Get swagger endpoint

```http
  GET /api/v1/schema/swagger-ui
```

#### Get redoc endpoint

```http
  GET /api/v1/schema/redoc
```



## Tech Stack

**Server:** Django, DRF, Celery, Docker, Nginx

