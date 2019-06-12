# Project: Item Catalog

This is the fourth project of the Udacity's Full Stack Web Developers Nanodegree.

The project consists in developing an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

This project uses a modified version of the [Full Stack Web Developer Nanodegree program virtual machine repository](https://github.com/udacity/fullstack-nanodegree-vm).


## Installation

To install this project you need to follow three major steps:

#### 1 - VirtualBox and Vagrant

First, you need to install and configure a VirtualBox and Vagrant, where the program will run. Follow the instructions [here](https://github.com/udacity/fullstack-nanodegree-vm#installation).

#### 2 - Repository

To install this project there are two ways:
- Download the repository ZIP file and unpack it.
- Or clone the repository

#### 3 - Client Secret

Create a file inside the folder /vagrant/catalog with the name cliente_secrets.json. Put the following content inside:

```sh
{"web":{"client_id":"PUT_HERE_THE_GOOGLE_CLIENT_ID","project_id":"PUT_HERE_THE_PROJECT_ID","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v2/certs","client_secret":"PUT_HERE_THE CLIENT_SECRET","redirect_uris":["http://localhost:8000"],"javascript_origins":["http://localhost:8000"]}}
```
Replace uppercase text with the correct information about the Google Developer Account.

#### 4 - Create Database

The last step is to create the database for the application. In order to do so, run the following commands in the terminal:

```sh
$ vagrant up
$ vagrant ssh
$ cd /vagrant/catalog
$ python models.py
```

## Requirements

This project was implemented with **Python 2.7.12**.

The Python Libraries used were:
- flask
- flask_sqlalchemy
- oauth2client
- random
- string
- json
- httplib2
- requests

All these Libraries were installed in the virtual machine, but in order to install in other environment, use the [requirements.txt](requirements.txt) file.


## Running the Item Catalog Web Server

To run the program, you only need to type the following command, inside the folder /vagrant/catalog on the vitual machine:
```sh
$ python application.py
```

## Item Catalog API

There are three API endpoints:

- Retrieve all categories and its items that were created in the catalog:

```sh
http://localhost:8000/catalog.json
```

- Retrieve a specific category with its items:

```sh
http://localhost:8000/catalog/<CATEGORY_NAME>/items/JSON
```

- Retrieve a specific item:

```sh
http://localhost:8000/catalog/<CATEGORY_NAME>/<ITEM_NAME>/JSON
```

## Code Quality

To ensure code quality, it was used the tools:
- Python: [pycodestyle](https://github.com/PyCQA/pycodestyle)

## How to Contribute

If you find any bug or have a suggestion for another resources, feel free to improve this project.

First, you have to fork this repository.

Next, clone this repository to your computer to make the changes.

Once you've pushed changes to your local repository, you can issue a pull request.

## License

The contents of this repository are covered under the [MIT License](LICENSE).
