# Pedotan-CC Repository (# Team C23-PS379)
Member of Cloud Computing for Bangkit Academy Capstone Team C23-PS379 
| Member | Student ID | University |
|:------:|:----------:|:----------:|
| Muhammad Dzaki Dwi Putranto | C017DSX0699 | Bandung Institute of Technology |
| Akmal Jauhar Sidqi | C017DSX0718 | Bandung Institute of Technology |

**

**This repository contains API and AI-Model for deployment**

**

## User authentication and user data
For the implementation of user authentication features, PEDOTAN make use of **firebase user authentication** feature. With this feature, user registration and authentication will be handled by **firebase**.

User can register an account using both email/password method and google provider method.

When user make a login, user will be given a **unique token** that will be used to accessing other API. Without this unique token, user may not get the API access for other features.

Data of PEDOTAN users will be saved on to firestore database. Here are the detail of the stored data on firestore database.
 
 - User Data
	 - Email
	 - Name
	 - Location
	 - NIK
	 - Phone Number
	 - Photo
 - Session Tokens
 - User's Farm Data
	 - ID
	 - User Email
	 - Commodity
	 - Area
	 - Location
	 - Status

## AI-Model
For the implemention of AI-Model in PEDOTAN, we have **3 AI-Model** that have been developed by our AI Team. For further details of the model, please check out our AI Team Repository.

Accessing the AI-Model from PEDOTAN apps will uses 2 APIs to **uploading image** and **sending data** required by the model. The APIs will preprocess the image and data to make sure the data that is used is suitable with the specification required by the AI-Model. 

After the prediction is made by the AI-Model, the data prediction will be used to update the user's farm data "status" according the result of the data prediction.

## Endpoints
Here are the endpoints used by PEDOTAN-APP

 - **'/auth/register'**
	User registration using email/password method (saving user data in firestore)
- **'/auth/google'**
	User registration using google provider (saving user data in firestore)
- **'/auth/login'**
	Creating a unique session token for user
- **'/auth/datauser'**
	- POST
		Sending a detailed user data on to firestore database
	- GET
		Retrieving user data from firestore database
- **'/auth/datakebun'**
	- POST
		Sending a user's farm data on to firestore database
	- GET
		Retrieving user's farm data from firestore database
- **'/auth/logout'**
	Deleting user's session token
- **'/ai/predictdisease'**
	Sending plant disease photo for AI prediction
- **'/ai/predictcrop'**
	Sending crop data for AI prediction

## Deployment
**PEDOTAN APIs are deployed on Google Cloud Platform Compute Engine.**
Here are the detailed specification of  the compute engine used for deployment.

| Item | Specification |
|:-----:|:------------:|
| Type | Instance |
| Zone | asia-southeast2-a |
| Machine type | e2-medium |
| CPU Platform | Intel Broadwell |
| Architecture | x86/64 |
| Boot Disk | debian-11-bullseye |
