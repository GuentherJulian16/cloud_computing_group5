# cloud_computing_group5

Cloud Computing project of Group 5 (Master AI SoSe 2021 Hochschule Fulda)
___

This project contains a simple database-driven chat application called "StudyChat" using Node.js and MySQL.

## AWS Deployment

The deployment folder contains scripts for deploying the application to AWS and stopping the application instances. The `start.py` script starts a database instance running a MySQL server and two webserver instances that deploy the front end of the web application.
The `add_new_webserver.py` script adds a new webserver instance.
The scripts retrieve the username and password for the database connection from the AWS Secret Manager. To do this, you must configure `database_user` and `database_password` in a secret named `CloudComputing/StudyChat`. If you do not want to use the AWS Secret Manager, simply set the corresponding variables to static strings.
The `stop.py` file stops all deployed and running instances for this application.

The application will be available on `https://your-public-ip:3000/`.

## Local testing
For a local deployment of the application, you need a running MySQL server to connect to and an installed Node.js version. Configure the connection to the database with the appropriate credentials in the `models/db.js` file. 
Create the database and tables by executing the following SQL commands:
```
create database db_cloudcomputing
create table users ( id INT AUTO_INCREMENT, username VARCHAR(150) NOT NULL, password VARCHAR(150) NOT NULL, PRIMARY KEY (id))
create table chats ( id INT AUTO_INCREMENT, name VARCHAR(255) NOT NULL, description VARCHAR(500) NOT NULL, creatorId INT NOT NULL, PRIMARY KEY (id))
create table messages ( id INT AUTO_INCREMENT, userId INT NOT NULL, chatId INT NOT NULL, message VARCHAR(1000) NOT NULL, time_created DATETIME NOT NULL, PRIMARY KEY (id))
```

Install the dependencies with `npm install` and launch the application with `node app.js`.