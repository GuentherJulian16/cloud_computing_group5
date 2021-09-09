# cloud_computing_group5

Cloud Computing project of Group 5 (Master AI SoSe 2021 Hochschule Fulda)
___

This project contains a simple database-driven chat application called "StudyChat" using Node.js and MySQL.

The deployment folder contains scripts for deploying the application to AWS and stopping the application instances. The `start.py` script starts a database instance running a MySQL server and two web server instances that deploy the front end of the web application.
The script retrieves the username and password for the database connection from the AWS Secret Manager. To do this, you must configure `database_user` and `database_password` in a secret named `CloudComputing/StudyChat`. If you do not want to use the AWS Secret Manager, simply set the corresponding variables to static strings.
